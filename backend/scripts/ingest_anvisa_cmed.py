import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy.dialects.postgresql import insert

# Configura o path do projeto para permitir importar os módulos app
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal  # noqa: E402
from app.models.anvisa import AnvisaMedicamento  # noqa: E402


def normalize_ean(ean_str: str):
    """
    Normaliza a string EAN:
    - Separa por vírgulas se houver múltiplos EANs.
    - Remove hifens, espaços.
    - Remove zeros à esquerda.
    - Filtra EANs que têm 13 ou 14 dígitos (após a limpeza).
    Retorna uma lista de strings EAN válidas.
    """
    if pd.isna(ean_str) or not isinstance(ean_str, str):
        return []

    eans_brutos = ean_str.split(",")
    eans_validos = []

    for ean in eans_brutos:
        # Limpeza
        ean_limpo = ean.strip().replace("-", "").replace(" ", "")

        # Remove zeros à esquerda (as vezes a Anvisa manda coisas como 00007891234567)
        # ean_limpo = ean_limpo.lstrip('0')

        # Se após a limpeza o tamanho for 13 ou 14, e for numérico, aceitamos
        if ean_limpo.isdigit() and len(ean_limpo) in (13, 14):
            eans_validos.append(ean_limpo)

    return eans_validos


def run_etl(csv_filepath: str, batch_size: int = 10000):
    if not os.path.exists(csv_filepath):
        print(f"Erro: Arquivo CSV {csv_filepath} não encontrado.")
        sys.exit(1)

    print(f"Lendo o CSV {csv_filepath}...")

    try:
        # Lê colunas como strings para preservar a precisão dos identificadores.
        df = pd.read_csv(
            csv_filepath, sep=";", encoding="utf-8", dtype=str, keep_default_na=False
        )
    except Exception as e:
        print(f"Falha ao ler o CSV: {e}")
        sys.exit(1)

    # Fazemos correspondência parcial porque os cabeçalhos variam entre arquivos.
    # "EAN 1", "SUBSTÂNCIA", "LABORATÓRIO", "TARJA"
    col_map = {}
    for col in df.columns:
        col_upper = col.upper()
        if "EAN 1" in col_upper or "EAN" in col_upper and "ean_col" not in col_map:
            col_map["ean_col"] = col
        elif "SUBSTÂNCIA" in col_upper or "PRINCIPIO ATIVO" in col_upper:
            col_map["substancia_col"] = col
        elif "LABORATÓRIO" in col_upper:
            col_map["lab_col"] = col
        elif "TARJA" in col_upper:
            col_map["tarja_col"] = col

    if len(col_map) < 4:
        print(
            "Aviso: Não encontrou as colunas esperadas. Usando fallback. "
            f"Colunas disponíveis: {df.columns.tolist()}"
        )
        # Tenta pegar as que achar.
        ean_col = col_map.get("ean_col", "EAN 1")
        substancia_col = col_map.get("substancia_col", "SUBSTÂNCIA")
        lab_col = col_map.get("lab_col", "LABORATÓRIO")
        tarja_col = col_map.get("tarja_col", "TARJA")
    else:
        ean_col = col_map["ean_col"]
        substancia_col = col_map["substancia_col"]
        lab_col = col_map["lab_col"]
        tarja_col = col_map["tarja_col"]

    print("Iniciando transformação...")

    medicamentos_a_inserir = {}

    for index, row in df.iterrows():
        eans_str = row.get(ean_col, "")
        substancia = row.get(substancia_col, "Não informado").strip()
        laboratorio = row.get(lab_col, "Não informado").strip()
        tarja_bruta = row.get(tarja_col, "Sem Tarja").strip()
        tarja = tarja_bruta.replace("(*)", "").strip()

        eans_validos = normalize_ean(eans_str)

        for ean in eans_validos:
            # Mantém uma entrada por EAN quando houver duplicatas no arquivo.
            # Para evitar estourar memória com DB queries
            if ean not in medicamentos_a_inserir:
                medicamentos_a_inserir[ean] = {
                    "ean": ean,
                    "principio_ativo": substancia,
                    "laboratorio": laboratorio,
                    "tarja": tarja,
                }

    lista_inserir = list(medicamentos_a_inserir.values())
    total_registros = len(lista_inserir)
    print(f"Total de EANs válidos e únicos para inserir: {total_registros}")

    if total_registros == 0:
        print("Nenhum registro para inserir. Saindo.")
        return

    print("Iniciando carga no banco de dados...")

    with SessionLocal() as db:
        for i in range(0, total_registros, batch_size):
            lote = lista_inserir[i : i + batch_size]

            stmt = insert(AnvisaMedicamento).values(lote)
            # On conflict do nothing
            stmt = stmt.on_conflict_do_nothing(index_elements=["ean"])

            db.execute(stmt)
            db.commit()

            print(
                f"Inseridos {min(i + batch_size, total_registros)} / {total_registros}"
            )

    print("Carga finalizada com sucesso.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python ingest_anvisa_cmed.py <caminho_para_csv_cmed>")
        sys.exit(1)

    csv_file = sys.argv[1]
    run_etl(csv_file)
