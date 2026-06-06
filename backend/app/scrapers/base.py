import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from pydantic import ValidationError
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionLocal
from app.models.catalogo import CatalogoBase
from app.models.oferta_farmacia import OfertaFarmacia
from app.models.historico import HistoricoPreco
from app.models.farmacia import Farmacia
from app.schemas.oferta import ProdutoExtraidoSchema
from app.services.enriquecimento import ServicoEnriquecimentoFarmacologico
from app.core.utils import validar_ean13

class BasePharmacyScraper(ABC):
    def __init__(
        self,
        farmacia_cnpj: str,
        farmacia_razao_social: str,
        farmacia_nome_fantasia: str,
        farmacia_endereco: str,
        num_workers: int = 3,
        batch_size: int = 50
    ):
        self.fila = asyncio.Queue()
        self.num_workers = num_workers
        self.batch_size = batch_size
        self.farmacia_cnpj = farmacia_cnpj
        self.farmacia_razao_social = farmacia_razao_social
        self.farmacia_nome_fantasia = farmacia_nome_fantasia
        self.farmacia_endereco = farmacia_endereco

    @abstractmethod
    async def extrair_catalogo(self) -> None:
        """
        Método obrigatório que as classes filhas devem implementar.
        Deve extrair os dados e usar `await self.fila.put(produto_dict)`.
        """
        pass

    async def _worker(self):
        batch = []
        while True:
            produto_dict = await self.fila.get()

            try:
                # Usado para sinalizar fim da extração
                if produto_dict is None:
                    # Salva o restante antes de finalizar o worker
                    if batch:
                        await asyncio.to_thread(self._processar_e_salvar_lote, batch)
                    break

                try:
                    # 1. Validação Pydantic
                    prod_validado = ProdutoExtraidoSchema.model_validate(produto_dict)
                except ValidationError as e:
                    print(f"[AVISO] Ignorando produto inválido: {e}")
                    continue

                # Validação de EAN - limpa EAN se for inválido
                ean_valido = prod_validado.ean if prod_validado.ean and validar_ean13(prod_validado.ean) else None
                # Se mudamos a validação de ean, mas é immutable no Schema de saida, passamos como copia
                # Contudo podemos usar ele validado para as proximas etapas
                prod_validado.ean = ean_valido

                # Prepara dicionário consolidado para o banco (enriquecido será preenchido em lote)
                item_enriquecido = {
                    "validado": prod_validado,
                    "enriquecido": None
                }

                batch.append(item_enriquecido)

                if len(batch) >= self.batch_size:
                    # Salva em lote usando uma thread separada para não bloquear o loop de eventos
                    await asyncio.to_thread(self._processar_e_salvar_lote, batch.copy())
                    batch.clear()

            except Exception as e:
                print(f"[ERRO WORKER] Falha no processamento: {e}")
            finally:
                self.fila.task_done()

    def _processar_e_salvar_lote(self, batch: List[Dict[str, Any]]) -> None:
        """
        Realiza o Bulk Lookup de enriquecimento e persiste o lote no banco de dados.
        Roda dentro de uma thread separada via asyncio.to_thread.
        """
        if not batch:
            return

        db = SessionLocal()
        try:
            # 1. Enriquecimento em lote (Bulk Lookup)
            batch = ServicoEnriquecimentoFarmacologico.enriquecer_lote(db, batch)

            # 1. Garante que a farmácia existe
            farmacia = db.query(Farmacia).filter(Farmacia.cnpj == self.farmacia_cnpj).first()
            if not farmacia:
                farmacia = Farmacia(
                    cnpj=self.farmacia_cnpj,
                    razao_social=self.farmacia_razao_social,
                    nome_fantasia=self.farmacia_nome_fantasia,
                    endereco_completo=self.farmacia_endereco
                )
                db.add(farmacia)
                db.commit()
                db.refresh(farmacia)

            # Desduplicação do CatalogoBase no lote atual
            catalogo_values_dict = {}
            for item in batch:
                prod: ProdutoExtraidoSchema = item["validado"]
                enriquecido: dict = item["enriquecido"]

                # Chave de desduplicação pode ser o ean ou, se não existir, o name_search.
                # EAN é prioritario e é a chave unica indexada pelo ON CONFLICT.
                # Produtos sem EAN (nulos) não causam conflito ON CONFLICT do EAN no postgres,
                # Mas vamos inseri-los normalmente (desduplicados pelo nome se sem ean, para simplificar).

                chave_dedup = prod.ean if prod.ean else prod.name_search

                catalogo_values_dict[chave_dedup] = {
                    "codigo_barras": prod.ean,
                    "name_search": prod.name_search,
                    "principio_ativo": enriquecido['principio_ativo'],
                    "laboratorio": enriquecido['laboratorio'],
                    "exige_receita": enriquecido['exige_receita'],
                    "categorias": enriquecido['categorias']
                }

            catalogo_values = list(catalogo_values_dict.values())

            if catalogo_values:
                # Upsert CatalogoBase
                stmt = insert(CatalogoBase).values(catalogo_values)
                # O conflito pode ser no codigo_barras
                stmt = stmt.on_conflict_do_update(
                    index_elements=['codigo_barras'],
                    set_={
                        "name_search": stmt.excluded.name_search,
                        "principio_ativo": stmt.excluded.principio_ativo,
                        "laboratorio": stmt.excluded.laboratorio,
                        "exige_receita": stmt.excluded.exige_receita,
                        "categorias": stmt.excluded.categorias
                    },
                    where=(CatalogoBase.codigo_barras.is_not(None))
                )

                db.execute(stmt)
                db.commit()

            # Recupera IDs
            eans_no_lote = [item["validado"].ean for item in batch if item["validado"].ean]
            nomes_no_lote_sem_ean = [item["validado"].name_search for item in batch if not item["validado"].ean]

            mapa_catalogo = {}
            if eans_no_lote:
                catalogos_com_ean = db.query(CatalogoBase).filter(CatalogoBase.codigo_barras.in_(eans_no_lote)).all()
                for c in catalogos_com_ean:
                    mapa_catalogo[c.codigo_barras] = c.id

            if nomes_no_lote_sem_ean:
                catalogos_sem_ean = db.query(CatalogoBase).filter(
                    CatalogoBase.codigo_barras.is_(None),
                    CatalogoBase.name_search.in_(nomes_no_lote_sem_ean)
                ).all()
                for c in catalogos_sem_ean:
                    mapa_catalogo[c.name_search] = c.id


            # Prepare to query existing OfertaFarmacia to check for price changes
            urls_no_lote = [item["validado"].link for item in batch]
            precos_existentes = {}
            if urls_no_lote:
                ofertas_existentes = db.query(OfertaFarmacia).filter(OfertaFarmacia.url_origem.in_(urls_no_lote)).all()
                for oferta in ofertas_existentes:
                    precos_existentes[oferta.url_origem] = oferta.preco

            # Desduplicação da OfertaFarmacia no lote atual
            oferta_dicts_map = {}
            for item in batch:
                prod: ProdutoExtraidoSchema = item["validado"]
                catalogo_id = None
                if prod.ean and prod.ean in mapa_catalogo:
                    catalogo_id = mapa_catalogo[prod.ean]
                elif not prod.ean and prod.name_search in mapa_catalogo:
                    catalogo_id = mapa_catalogo[prod.name_search]

                if catalogo_id:
                    # Chave de desduplicação pela URL origem que é a unique key
                    oferta_dicts_map[prod.link] = {
                        "sku_interno": prod.sku_interno,
                        "preco": prod.preco,
                        "quantidade_estoque": 1,
                        "disponivel": True,
                        "url_origem": prod.link,
                        "imagem_url": prod.imagem_url,
                        "farmacia_id": farmacia.id,
                        "catalogo_id": catalogo_id
                    }

            oferta_dicts = list(oferta_dicts_map.values())

            historico_dicts = []
            for url, oferta_data in oferta_dicts_map.items():
                preco_novo = oferta_data["preco"]
                preco_antigo = precos_existentes.get(url)

                # If it's a new offer or the price has changed, add to history
                if preco_antigo is None or preco_novo != preco_antigo:
                    historico_dicts.append({
                        "medicamento_id": oferta_data["catalogo_id"],
                        "farmacia_id": oferta_data["farmacia_id"],
                        "preco": preco_novo
                    })

            if oferta_dicts:
                # Upsert OfertaFarmacia
                stmt_oferta = insert(OfertaFarmacia).values(oferta_dicts)
                stmt_oferta = stmt_oferta.on_conflict_do_update(
                    index_elements=['url_origem'],
                    set_={
                        "preco": stmt_oferta.excluded.preco,
                        "imagem_url": stmt_oferta.excluded.imagem_url
                    }
                )
                db.execute(stmt_oferta)

            if historico_dicts:
                stmt_historico = insert(HistoricoPreco).values(historico_dicts)
                db.execute(stmt_historico)

            db.commit()

        except SQLAlchemyError as e:
            db.rollback()
            print(f"[ERRO DB] Falha na persistência em lote: {e}")
        finally:
            db.close()

    async def executar_com_backoff(self, funcao, *args, max_retries=5, initial_delay=2.0, **kwargs):
        """
        Implementa a estratégia genérica de Exponential Backoff para lidar com Rate Limits.
        """
        retries = 0
        delay = initial_delay

        while retries <= max_retries:
            try:
                # Executa a função assíncrona
                response = await funcao(*args, **kwargs)

                # Avalia o status no objeto de resposta se existir
                status = getattr(response, "status_code", 200)
                if status == 429 or status >= 500:
                    retries += 1
                    if retries > max_retries:
                        print(f"Max retries excedido para o status HTTP {status}.")
                        return response
                    print(f"Rate limit / Server Error ({status}). Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue

                return response

            except Exception as e:
                # Avalia atributos encadeados de exceção (para libraries como httpx)
                status_obj = getattr(e, "response", None)
                if status_obj is not None:
                    status_code = getattr(status_obj, "status_code", 0)
                    if status_code == 429 or status_code >= 500:
                        retries += 1
                        if retries > max_retries:
                            print(f"Max retries excedido para a falha HTTP {status_code}.")
                            raise e
                        print(f"Rate limit / Server Error ({status_code}). Retrying in {delay}s...")
                        await asyncio.sleep(delay)
                        delay *= 2
                        continue

                # Outras falhas de conexão/timeout
                retries += 1
                if retries > max_retries:
                    print(f"Max retries excedido para erro de rede: {e}")
                    raise e
                print(f"Network/Library error ({e}). Retrying in {delay}s...")
                await asyncio.sleep(delay)
                delay *= 2

    async def run(self):
        """
        Ponto de entrada principal do scraper.
        Inicia os workers consumidores e aguarda a extração.
        """
        # Inicia os workers
        workers = [asyncio.create_task(self._worker()) for _ in range(self.num_workers)]

        try:
            # Roda a extração
            await self.extrair_catalogo()
        finally:
            # Envia sinal de término para os workers (None)
            for _ in range(self.num_workers):
                await self.fila.put(None)

            # Aguarda o processamento de tudo que está na fila
            await self.fila.join()

            # Aguarda as tasks finalizarem
            await asyncio.gather(*workers)
