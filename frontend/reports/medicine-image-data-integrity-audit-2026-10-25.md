# Preço Bão — auditoria de integridade das imagens e dados

Data da auditoria: 25/10/2026
Worktree/branch: `C:\dev\farmacia-scraper-monorepo-ana`, `ana`

## Escopo e segurança

Auditoria feita contra a API local na porta 8001, leitura do catálogo PostgreSQL já existente e leitura do registro externo `C:\dev\farmacia-scraper-monorepo\backend\data\image_references\references.json` (18.910 referências). O servidor de leitura usa o código desta worktree. Não foram iniciados scrapers/workers, feitas chamadas de coleta, alterados PostgreSQL/preços/históricos/usuários, nem editado o JSON externo. A outra worktree foi mantida sem alterações intencionais. As referências e imagens candidatas foram avaliadas por associação, regras do código e inspeção visual de uma amostra direcionada; não foi feito teste HTTP de cada URL do catálogo.

## Diagnóstico e cobertura

O problema central estava no caminho da API: `with_registry_images` convertia referências do JSON em URLs públicas sem filtrar arte genérica, EAN incompatível ou associação exata com oferta ativa. O frontend prioriza a primeira URL recebida, portanto uma imagem institucional colocada primeiro no JSON aparecia nos cards e detalhes como se fosse embalagem. O estado de rejeição do registro não era suficiente para impedir a entrega nesse caminho. A tela não criava a imagem; renderizava uma URL inadequada que a API havia autorizado.

Fluxo encontrado: página da farmácia → scraper/identificadores (EAN/SKU/URL e imagem) → registro JSON externo → `image_registry.resolve_catalog_images` → resposta FastAPI em `catalog_response.with_registry_images` → normalização/cache em `frontend/src/services/catalog.ts` e `useCatalogState` → `MedicineImage` → card, favorito e detalhe. O endpoint de redirecionamento `/catalogo/medicamentos/{id}/imagem` também foi alinhado à mesma política da resposta do catálogo.

| Medida da base lida | Resultado |
|---|---:|
| Medicamentos no catálogo | 13.103 |
| Com EAN | 12.589 |
| Sem EAN | 514 |
| Sem princípio ativo útil | 4.499 |
| Sem laboratório útil | 4.493 |
| Com `imagem_url` persistida | 4.109 |
| Persistidas com status `verificada` | 1.474 |
| Persistidas com status `pendente` | 2.635 |
| Sem status de imagem | 8.994 |
| Ofertas / ofertas disponíveis | 14.802 / 9.952 |
| Medicamentos com ofertas | 12.637 |
| Grupos com EAN duplicado | 0 |
| Grupos por nome normalizado que merecem revisão | 116 |

O status persistido `verificada` é uma declaração da base, não prova visual independente. A política nova também valida origem, identificadores e arte genérica. Uma simulação somente leitura da política identificou 4.629 referências elegíveis associadas a ofertas e 3.517 medicamentos com alguma imagem segura; 1.197 registros com imagem persistida passaram as verificações adicionais. Esses números são análise de elegibilidade, não contagem de URLs testadas por HTTP nem atualização da base. Os 116 grupos por nome não foram classificados como duplicatas confirmadas.

No JSON: 18.910 registros ligados a 13.102 IDs de catálogo. A análise encontrou 750 URLs cujo caminho contém EAN diferente do cadastro, e nenhuma divergência entre o campo EAN do registro JSON e o EAN de seu cadastro associado. Esse achado não confirma que todas as URLs com EAN igual sejam fotos corretas: foram encontradas imagens promocionais e genéricas com EAN/SKU corretos. A classificação atual pelo código identifica 12.932 registros como genéricos, institucionais, promocionais ou placeholder; é uma contagem de bloqueios da política baseada em URLs/fontes/nomes de arquivos e imagens conhecidas, não uma taxa de falha HTTP nem uma inspeção manual de todos os arquivos.

## Casos examinados

### Glyxambi

| ID | EAN cadastrado | Apresentação/cadastro | SKU e candidata observados | Resultado |
|---:|---|---|---|---|
| 2 | `7896026307925` | Glyxambi 25 mg + 5 mg, 30 comprimidos; princípio ativo pendente e laboratório não informado | Indiana `IND122816`; a URL oficial do produto termina em `/glyxambi-25mg-5mg-30-comprimidos/p`. Imagem `https://farmaciaindiana.vteximg.com.br/arquivos/ids/306093/7896026306751.jpg?...` | EAN no nome da imagem é `7896026306751`, divergente do produto. A imagem baixada era a ilustração Indiana “Produto sem foto por determinação da ANVISA”, não uma embalagem. Agora bloqueada; API entrega zero URL de imagem e o app mostra placeholder. |
| 3103 | `7896026306751` | Glyxambi 25 mg + 5 mg, 30 comprimidos; princípio ativo e Boehringer informados | Araújo `ARJ7290`; página `/glyxambi-25mg--5mg-com-30-comprimidos/7290.html`; candidata `https://i3-imagens-prd.araujo.com.br/webp/7290/128666_7896026306751_1.webp?...` | O EAN/SKU/caminho correspondem ao cadastro, mas o ativo da referência Araújo está na lista de arte genérica visualmente confirmada. Bloqueada. Não transferida ao ID 2. |

Os dois registros têm EANs distintos apesar de nome/apresentação muito semelhantes. A diferença pode ser divergência cadastral ou variante/identificador histórico; sem fonte oficial suficiente não os unifiquei nem alterei EAN, princípio ativo ou laboratório. O campo incompleto do ID 2 vem do próprio PostgreSQL/API (`Não informado (Pendente)` e `Não informado`), não de perda no cache. O cache agora evita que resposta parcial apague valor útil já conhecido; não consegue completar um cadastro que já chega vazio.

### Infralax

| ID | EAN | Apresentação/cadastro | Candidatas | Resultado |
|---:|---|---|---|---|
| 619 | `7896004705682` | Infralax, 30 comprimidos; ativo e EMS informados | Indiana `IND20385`, produto `/infralax-300-30-125-50mg-30-comprimidos/p`, imagem `.../MEDICAMENTOS CAIXA AZUL - OTC.jpg`; Araújo `ARJ76969`, EAN no nome `132205_7896004705682_1.webp`; Pacheco `PCH157716`, produto `/infralax-50mg-ems-30-comprimidos/p`, arte `de-referencia-tarja-vermelha-em-comprimido-pacheco.jpg` | A imagem Indiana foi inspecionada e é arte genérica OTC. A Pacheco é um molde vermelho/branco da farmácia com indicação de imagem ilustrativa. As duas são bloqueadas. A candidata Araújo é EAN/SKU vinculada e não consta entre os ativos genéricos conhecidos; ainda não foi inspecionada/validada visualmente nesta auditoria, por isso a página não a trata como confirmada sem a associação de oferta ativa. |
| 1209 | `7896004727158` | Infralax, 15 comprimidos | Indiana `IND20386` usa o mesmo arquivo OTC genérico; Pacheco `PCH341142` usa o molde vermelho/branco; Araújo SKU `ARJ71565`, `128866_7896004727158_1.webp` | Candidatas Indiana/Pacheco bloqueadas; imagem de Araújo exige validação da oferta/apresentação. Nenhuma imagem foi movida entre 15 e 30 comprimidos. |

### Mounjaro

IDs confirmados na API: 1 (5 mg, EAN `7896382709135`), 3 (2,5 mg, `7896382709111`), 43 (10 mg, `7896382709173`), 413 (7,5 mg, `7896382709159`), 778 (12,5 mg, `7896382709197`) e 136 (15 mg, `7896382709210`). Todos retornam tirzepatida e Eli Lilly no cadastro. As seis URLs Indiana usam `MEDICAMENTOS-CAIXA-AZUL---OTC.jpg.jpg`; são ilustrações genéricas e foram bloqueadas. As candidatas Araújo (`239898_7896382709135_1.webp`, `239899_7896382709111_1.webp`, `239360_7896382709173_1.webp`, `239363_7896382709159_1.webp`, `239367_7896382709197_1.webp`, `239366_7896382709210_1.webp`) e Pacheco (`887455-2.jpg`, `887528-DPA.png`, `888060-2.jpg`, `887951-2.jpg`, `888079-2.jpg`, `888087-2.jpg`) foram baixadas e examinadas. São composições promocionais/combinadas de concentrações e preços, não uma foto isolada e inequívoca da embalagem da apresentação selecionada. Foram bloqueadas mesmo quando EAN/SKU correspondiam. Não usei a imagem de uma concentração como substituta de outra.

## Correções de código

- `backend/app/services/imagens.py`: reconhece marcadores e arquivos genéricos de Indiana/Pacheco e os ativos promocionais revisados; inclui `is_generic_image_url` limitado a fontes conhecidas para não classificar arbitrariamente imagens de qualquer domínio.
- `backend/app/services/image_registry.py`: exige associação com oferta ativa por ID/farmácia/SKU quando disponível; se não houver oferta associada, exige EAN igual. Rejeita arte genérica e EAN divergente no registro e no caminho da imagem.
- `backend/app/services/catalog_response.py`: só antepõe imagem persistida quando status, origem, correspondência e EAN passam; limpa imagem direta das ofertas para não abrir um caminho paralelo não validado.
- `backend/app/api/routes/catalogo.py`: redirecionamento de imagem usa o mesmo resolvedor.
- `frontend/src/services/catalog.ts` e `frontend/src/hooks/useCatalogState.ts`: merge de resposta parcial mantém EAN, princípio ativo, laboratório, ofertas, categorias e imagens conhecidos quando a chave foi omitida, mas atualiza valores explicitamente retornados.
- `frontend/src/theme.ts`: placeholder no tema escuro usa superfície escura neutra, em vez do retângulo quase branco observado na primeira inspeção.
- Testes de API/registro e cache foram ajustados/adicionados. Nenhuma imagem candidata foi promovida ou escrita no JSON/DB.

## Validação funcional e visual

API 8001 consultada para IDs 2, 3103, 619, 1209, 1, 3, 43, 413, 778 e 136: retornou identidade, ofertas e preços sem imagem candidata para os casos suspeitos; detalhes incompletos de Glyxambi ID 2 permanecem explícitos. Na web, foram abertos Home, busca, detalhe, histórico, favoritos, login e cadastro. Foram capturados os tamanhos 360, 390, 768, 1440 e 1920 px, em tema claro e escuro (Home em desktop e telas selecionadas em mobile). `document.documentElement.scrollWidth` foi igual à largura de viewport em todas as capturas verificadas. A pasta de evidências é [`medicine-image-audit-2026-10-25`](medicine-image-audit-2026-10-25/).

| Antes | Depois |
|---|---|
| [Detalhe Glyxambi na homologação Android anterior](visual/android-standalone-2026-10-25/final-f049-detail.png): arte Indiana genérica aparece como imagem do produto. | [Detalhe Glyxambi Web, claro](medicine-image-audit-2026-10-25/390-glyxambi-detail.png) e [escuro](medicine-image-audit-2026-10-25/390-glyxambi-detail-dark-final.png): placeholder sem embalagem, identidade/preço preservados; ativo/laboratório continuam corretamente marcados como ausentes. |
| [Home anterior Android](visual/android-standalone-2026-10-25/final-f049-home.png) continha resultados que exibiam arte suspeita. | [Home mobile 360 px](medicine-image-audit-2026-10-25/360-home-light.png), [desktop 1440 px](medicine-image-audit-2026-10-25/1440-home-light.png) e [desktop escuro](medicine-image-audit-2026-10-25/1440-home-dark-final.png) mostram placeholder neutro; [captura Xiaomi após atualizar](medicine-image-audit-2026-10-25/xiaomi-home-after-update.png) comprova abertura da versão nova, mas documenta bloqueio de conexão LAN. |

Android: `assembleStandalone` concluiu com sucesso depois de mapear temporariamente o SDK para `Q:`; o `local.properties` original foi restaurado e a unidade desmontada. APK `1.0.0-internal`, SHA-256 `BBD1C45140AEF65459317224BF3F993432ACC935A5686A2C3A92613898D29C7F`, assinatura APK v2 válida. Instalado com `adb install -r` no Xiaomi `23021RAAEG` sem limpar dados; abriu sem Metro e entrou na Home como convidado. A captura [`xiaomi-home-after-update.png`](medicine-image-audit-2026-10-25/xiaomi-home-after-update.png) registra a falha de conexão da API: `toybox nc` no aparelho expirou ao conectar a `192.168.2.110:8001`, embora o serviço responda localmente. O Windows recusou criar a regra temporária de firewall (erro de acesso negado), portanto catálogo e imagens não carregaram no aparelho. Não considero esse estado validação funcional dos dados/imagens no Xiaomi.

## Testes

- Backend: `pytest tests -q` — 78 passaram.
- Ruff: `ruff check app tests` — sem apontamentos.
- Frontend: Jest — 90 testes em 16 suítes passaram; `npx tsc --noEmit` e `npm run lint` passaram após o ajuste de tema.
- Expo export `--platform all` — Web, Android Hermes e iOS concluídos em diretório temporário, sem sobrescrever `frontend/dist` e `dist-android` existentes. Metro descartou cache serializado inválido, refez o crawl e concluiu a exportação.
- APK/Gradle: `:app:assembleStandalone` passou para arm64-v8a; assinatura v2 verificada; `adb install -r` retornou `Success`.
- `git diff --check` — passou; Git avisou apenas sobre conversão LF/CRLF em arquivos já modificados.

## Limitações e integridade

Nem todas as URLs foram submetidas a requisição HTTP nem todos os pixels dos 18.910 registros foram inspecionados. EAN/SKU iguais são evidência de identidade, mas não atestam sozinhos que a foto representa a embalagem. O JSON e PostgreSQL continuam inalterados; dados farmacológicos ausentes dependem de fonte oficial e revisão cadastral. A navegação/app nativo abriu no aparelho, mas validação conectada do catálogo fica pendente até liberar o acesso LAN à porta 8001. Nenhum scraper foi iniciado. Nenhum commit, merge, rebase ou branch nova foi criado.
