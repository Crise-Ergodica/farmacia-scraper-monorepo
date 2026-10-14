# Auditoria das imagens do Preço Bão — 10/10/2026

## Cobertura

| Momento | Imagens verificadas | Cobertura do catálogo |
| --- | ---: | ---: |
| Início desta rodada | 2.724 de 4.109 | 66,3% |
| Após a auditoria completa | 3.414 de 4.109 | 83,1% |

O ganho líquido foi de **690 medicamentos** com imagem verificada. A primeira passada chegou a 3.471, mas uma revisão detectou arquivos genéricos com nomes codificados (`%20`) e corrigiu a contagem. No estado final, nenhuma das 3.414 URLs verificadas é rejeitada pelo validador local e nenhuma traz EAN divergente no nome do arquivo. São 2.501 imagens da Indiana e 913 da Araújo.

## Causas e correções

- Parte das listagens da Indiana fornecia caixas genéricas. A seleção VTEX agora exige correspondência com o item e seu EAN/SKU, e a auditoria tenta a API oficial pelo SKU e pelo EAN quando a varredura paginada não cobre o produto.
- Na Araújo, a miniatura da listagem às vezes era genérica, mas a página oficial tinha uma imagem própria. O lote consulta a página do produto e o `og:image`, confere SKU e EAN, valida o arquivo e persiste a URL correta. Para medicamentos com EAN, também pesquisa a fonte por EAN sem criar uma oferta comercial fictícia.
- Nomes como `CAIXA%20MEDICAMENTO...` passavam pela detecção de arquivos genéricos. Backend e frontend agora decodificam e normalizam o nome antes de aceitar a imagem.
- A API gera uma referência de imagem com versão baseada na URL. Isso evita que um redirecionamento antigo em cache continue exibindo uma imagem substituída. O componente visual tenta outras imagens válidas do mesmo medicamento após falha de carregamento.
- O botão **Buscar** foi removido do cabeçalho desktop. A busca principal da Home, a rota de resultados e a aba mobile continuam disponíveis.

O processamento foi retomável e executado sobre os **4.109** itens do catálogo local. A busca paginada pública da Indiana respondeu HTTP 400 ao chegar ao offset 2.550. A auditoria então usou as ofertas locais, a consulta oficial por SKU e EAN e as páginas da Araújo. Isso permite auditar os registros locais, mas impede declarar a varredura paginada da Indiana como completa.

As URLs recuperadas foram persistidas no PostgreSQL local e **não acompanham o commit Git**. Em outra instalação com o banco populado, executar no diretório `backend`:

```powershell
poetry run python -m scripts.processar_imagens
poetry run python -m scripts.processar_imagens --no-discovery --recheck-invalid
```

O primeiro comando processa o catálogo e salva o progresso em `.image_audit_state.json` (arquivo local ignorado pelo Git). O segundo revê imagens previamente verificadas que agora falham nas regras de identidade e URL.

## Exemplos investigados

| Medicamento | Resultado |
| --- | --- |
| Nimesulida Cimed, ID 9, EAN 7896523212685 | Imagem própria recuperada da Araújo e carregada no navegador. A Indiana entregava uma caixa genérica. |
| Dipirona EMS envelope com 10, ID 441, EAN 7896004703398 | Imagem de produto da Araújo verificada e carregada. |
| Dipirona EMS genérico com 10, ID 10, EAN 7896004769196 | Continua pendente: é outro EAN; a Indiana oferece caixa genérica e nenhuma foto exata foi confirmada. A imagem do ID 441 não foi atribuída a ele. |
| Drospirenona + Etinilestradiol EMS, ID 444 | Imagem recuperada da página Araújo de SKU ARJ11151 e carregada. Esse registro não possui EAN no catálogo, então a associação usa o SKU exato. |
| Rosuvastatina EMS, ID 12, EAN 7896004728858 | Imagem própria recuperada da Araújo e carregada. A Indiana oferecia uma caixa genérica. |

## Pendências identificadas

**695 itens** seguem com `imagem_status=pendente`:

- **262 com EAN**: nenhuma fotografia exata foi confirmada nas fontes consultadas. Isso inclui casos em que a única imagem disponível é genérica.
- **433 sem EAN**: a busca paginada da Indiana ficou incompleta e não existe identificação suficiente para associar com segurança uma imagem encontrada apenas por nome.

A lista individual e o motivo de cada item estão em [image-audit.json](image-audit.json). Nenhum medicamento ou oferta foi excluído; preços, histórico e classificação ANVISA não foram alterados pelo lote de imagens.

## Validação

- Backend: `pytest -q` — **24 passaram**; `ruff check app tests scripts` — **sem problemas**; `alembic heads` — **uma head**.
- Frontend: Jest — **31 passaram**; TypeScript — **sem erros**; ESLint — **sem problemas**.
- Exports Expo Web e Android — **concluídos**. São verificações de compilação, não testes funcionais nativos.
- `adb devices` não listou dispositivos; não houve validação funcional Android. Para validar manualmente, iniciar backend e Expo no IP acessível pelo emulador/dispositivo, abrir Home, busca, detalhe, login, favoritos e voltar ao app após reiniciar.
- No navegador, foram conferidos Home em 390, 768, 1440 e 1920 px, busca em 390 e 1440 px, detalhes dos exemplos e favoritos autenticados. As imagens relevantes tinham `naturalWidth > 0`; a largura do documento coincidiu com a viewport nas capturas verificadas.

Capturas: [Home 390](../../frontend/reports/visual/image-recovery-2026-10-10/final-home-390.png), [Home 768](../../frontend/reports/visual/image-recovery-2026-10-10/final-home-768.png), [Home 1440](../../frontend/reports/visual/image-recovery-2026-10-10/final-home-1440.png), [Home 1920](../../frontend/reports/visual/image-recovery-2026-10-10/final-home-1920.png), [Nimesulida 390](../../frontend/reports/visual/image-recovery-2026-10-10/final-detail-9-390.png), [Dipirona pendente 390](../../frontend/reports/visual/image-recovery-2026-10-10/final-detail-10-390.png), [Busca 390](../../frontend/reports/visual/image-recovery-2026-10-10/final-search-390.png), [Busca 1440](../../frontend/reports/visual/image-recovery-2026-10-10/final-search-1440.png), [Favoritos 390](../../frontend/reports/visual/image-recovery-2026-10-10/final-favorites-390.png). Para a comparação do cabeçalho, ver a captura [anterior 1920](../../frontend/reports/visual/image-recovery-2026-10-10/before-home-1920.png) e a captura final 1920.
