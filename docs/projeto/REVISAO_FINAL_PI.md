# Revisão do Projeto Integrador — Preço Bão

Estado: **Aguardando resposta**. Revisão iniciada em 03/11/2026 (America/Sao_Paulo).
Esta matriz é um registro de trabalho; não integra o documento acadêmico. Nenhum item é aprovado apenas pela compilação. A revisão não altera a aplicação.

**Versão vigente:** 47 páginas físicas, após integração das Práticas 1 e 2. Consulte a última seção, “Retomada — integração das Práticas 1 e 2”, para os estados e localizações atuais, com a correção de escopo registrada ao final. O usuário confirmou que não houve Práticas 3, 4 e 5: o escopo vigente do oitavo período contém somente as Práticas 1 e 2. Os resultados de 39 páginas abaixo são históricos.

## Fontes e decisões

- Solicitação integral anexada pelo usuário: fonte das exigências da professora aqui transcritas; enunciados e respostas das Práticas 1 e 2 recebidos posteriormente; demais originais pendentes. Correções técnicas não constituem novas exigências acadêmicas.
- Checkout inicialmente limpo (`git status --short`); nenhum AGENTS.md localizado no repositório nem nos diretórios ancestrais consultados.
- `docs/ANALISE_E_PROMPT_REVISAO_LATEX_PI.md`: ausente, inclusive na busca de arquivos ignorados. Diagnóstico anterior não revalidável sem o arquivo.
- Fontes locais lidas: `main.tex`, os três capítulos, ambos os estilos, `references.bib`, quatro diagramas PDF e o protótipo PNG; README da raiz, modelos/schemas, rotas, autenticação, scrapers, serviços, migrações, testes, frontend e infraestrutura. Nenhum dado de usuário real ou segredo deve ser incluído na documentação.
- Manual Unileste **2023**, organizado por Jacqueline Dias Cabral, 119 páginas numeradas, PDF com 120 páginas físicas: https://www.unileste.catolica.edu.br/portal/wp-content/uploads/2024/02/UNILESTE_-_MANUAL_DE_NORMALIZACAO_PARA_TRABALHOS_ACADEMICOS-1.pdf. Consultados identificação, §§3.1–3.14 e regras de apresentação. A data 2024 no URL não é a edição. Aplicabilidade ao PI depende de confirmação das orientações originais.
- Manual Unileste **2020**, organizado por Jacqueline Dias Cabral e Ilma Maria da Silva: https://unileste.catolica.edu.br/portal/wp-content/uploads/2020/08/manual-de-normalizacao-para-trabalhos-academicos-v2.pdf. Consultado para identificação; versão anterior, não adotada como substituta da de 2023.
- ABNT NBR **14724:2024**, 4ª edição, 16/12/2024: texto consultado em https://www.ccs.ufpb.br/coordfarm/wp-content/uploads/sites/21/sites/454/2026/03/ABNT_NBR_14724_2024-1.pdf, especialmente §§4–5. A cópia consultada não identifica errata de 2025. A validação deve considerar a versão corrigida aplicável.
- ABNT NBR **6028:2021**: consultada por meio do informativo GNT/Unesp, julho/2021, pp. 4 e 6: https://www.foa.unesp.br/Home/instituicao/biblioteca108/informativo-gnt---nbr-6028-2021_final.pdf. Não se alega consulta integral à norma.
- NBR **10520:2023**, **6023:2025**, **6024:2012** e **6027:2012**: identificadas como pertinentes; catálogo institucional da Ufes https://biblioteca.ufes.br/normalizacao e referências do manual. Textos integrais dessas edições ainda não consultados; não aprovadas por inferência a partir de abntex2.
- Conflito: manual 2023 §§3.7–3.8, pp. 19–21, indica palavras-chave “separadas por ponto”; informativo NBR 6028:2021, p. 6, indica ponto e vírgula. **Decisão expressa do usuário nesta conversa: adotar ponto e vírgula conforme NBR 6028:2021**, aplicada ao resumo e abstract.
- O manual indica Arial ou Times New Roman (§2) e sugere esses tipos (§4.1); o template usa Latin Modern. Não substituir silenciosamente por fonte apenas semelhante nem afirmar conformidade institucional completa. Decisão sobre a aplicação do manual ao PI permanece pendente.
- Datas de junho/2026: sequência registrada é 03, 08, 12, 16, 13, 14, 17. As linhas não estão em ordem temporal; 13 e 14 antecedem 16. Isso não prova erro nas datas. Preservar integralmente e solicitar esclarecimento sobre o registro de falhas de 14/06 frente à execução de interface de 16/06.

## Matriz inicial de dependências (antes das correções)

As localizações abaixo são dos fontes. Páginas do PDF só serão aprovadas após compilação e inspeção da versão correspondente.

| Exigência | Evidência/fonte | Localização no LaTeX | Situação | Ação | Dependência | Critério de aceite |
|---|---|---|---|---|---|---|
| Capa e identificação completa | `main.tex`; nomes da solicitação | capa/folha de rosto; quadro de equipe | aguardando informação | Preservar as três grafias existentes | Confirmar integrantes, nomes, título, instituição, natureza, local e ano | Identificação confirmada e legível no PDF |
| Introdução e conclusão | implementação e artefatos locais | capítulos 01 e 03 | parcial | Desenvolver textos sem inventar metodologia histórica | Revalidar após entregas acadêmicas | Texto e sumário coerentes, sem capítulo vazio |
| Minimundo | texto anterior; rotas/frontend | capítulo 02, Minimundo | parcial | Distinguir objetivo de implementação; retirar garantias absolutas | PDF da versão consolidada | Domínio preservado e limitações explícitas |
| RF01–RF08 | código; requisitos preservados | capítulo 02, Requisitos | parcial | Manter IDs e metas; explicitar estado e evidência | Validação funcional com evidência própria | Nenhuma meta apagada ou confundida com resultado |
| RNF01–RNF11 | Compose, Makefile, configs, rotas | capítulo 02, Requisitos | parcial | Qualificar p95, retenção, HTTPS, privacidade e CI/CD | Medições e ambiente de produção/proteções de branch | Nenhum controle declarado efetivo sem prova |
| Casos de uso | PDFs anteriores inspecionados; rotas | `fig:diagrama_casos_de_uso` | parcial | Corrigir autenticação como precondição; separar atores externos da automação interna | Inspeção final e referência UML | RF cobertos, fronteira e relações corretas |
| Classes de scraping | `scrapers/base.py`, `araujo.py`, `pacheco.py`, `indiana.py` | `fig:diagrama_scraping` | parcial | BasePharmacyScraper; Indiana funcional; fontes editáveis | Inspeção da figura | Não inventar subclasses |
| Schemas | `schemas/usuario.py`, catálogo, ofertas, histórico | `fig:diagrama_schemas` | parcial | UsuarioRead/Create/Update e heranças reais | Inspeção da figura | Não mostrar UsuarioOut/UsuarioBase inexistentes |
| Classes ORM | `models/*.py`, biblioteca herdada instalada | `fig:diagrama_orm` | parcial | Incluir Usuario e as duas associações; corrigir atributos herdados | Inspeção da figura | Classes e relações coerentes com modelo |
| DER e dicionário | ORM PostgreSQL e migrações até e4902ba81c6d | seção de banco a consolidar | parcial | Representar as oito tabelas; colunas, PK/FK, nulabilidade, tipos e restrições; registrar divergências | Verificação de cobertura e PDF | Cada entidade do DER localiza sua descrição; não alegar esquema do banco vivo |
| Interfaces | `prototipo-telas.png`, frontend | `fig:prototipo_telas` | parcial | Corrigir ordem real das cinco telas; identificar protótipo e limites | Origem/autoria/ferramenta não comprovadas; inspeção | Rótulos legíveis e jornadas rastreáveis |
| Entregas anteriores, inclusive 6º | Não encontrados enunciados nem atribuições acadêmicas | Não incorporadas | aguardando informação | Incorporar originais e referenciar artefatos existentes | Relação por período e entregas originais | Toda entrega obrigatória comprovada no PDF |
| Diários de bordo | Não encontrados | Não incorporados | aguardando informação | Incorporar registros autênticos | Diários originais | Datas, participantes e conteúdo sem inferência de Git |
| Configuração e Manutenção de Software — 8º | Apenas título e práticas 1–5 na solicitação | Capítulo ainda não criado | aguardando informação | Criar capítulo com conteúdo comprovado e uma seção por prática | Enunciados, entregas 1–5 e confirmação de outras práticas | Não aceitar capítulo vazio ou reprodução de enunciados |
| Plano de testes | CT01–CT14 existentes; testes no repositório | capítulo 02, Plano de Testes | parcial | RF02/CT13, CT14 p95, rastreabilidade e qualificação de planejamento | Execuções históricas, se houver | Preservar Pendente sem inventar resultados |
| Cronograma e atribuições | Quadros existentes no LaTeX | `qua:equipe_responsabilidades`, `qua:cronograma_testes` | aguardando informação | Manter datas e nomes; deixar explícito caráter planejado | Confirmar cronograma e responsabilidades históricas | Não converter planejamento em realização |
| Bibliografia | Cinco entradas anteriores não citadas; menções Booch/Larman sem entradas | `references.bib`; modelagem | parcial | Confirmar obras antes de acrescentar; centralizar pós-textuais | Edição efetivamente usada pela equipe quando não verificável | Toda citação tem entrada conferida, sem referência inventada |
| ABNT e orientação institucional | Fontes/versionamento acima | documento inteiro | aguardando informação | Resolver conflitos e aplicar apenas critérios sustentados | Orientações originais e versões integrais indispensáveis | Revalidação global, inclusive listas, sumário e paginação |
| Compilação e inspeção de todas as páginas | Sem runtime TeX inicialmente | PDF a gerar | parcial | Tectonic local e alternativa de bundle; examinar log e renderizar | Resolver runtime/bundle | Build limpo, referências estáveis e todas as páginas verificadas |
| Diff e preservação do usuário | Checkout inicialmente limpo | repositório | parcial | Limitar alterações à documentação/diagramas | Revisão final | Aplicação sem alterações; fontes editáveis preservadas |

## Pendências encaminhadas

Pedido único de materiais enviado na conversa: identificação, manual/orientações originais, quadro/enunciados e entregas das práticas, entregas por período, diários e diagnóstico ausente. A ausência de resposta não confirma nenhum dado.

Não criar seções vazias para as atividades ausentes; não substituir atividades acadêmicas por manutenção técnica encontrada no código. A demanda permanece aberta, com escopo integral.

## Verificação técnica em andamento

- `latex-doctor`: `missing`; não há Tectonic, TeX Live, latexmk, pdflatex ou BibTeX no ambiente inicial.
- Tectonic oficial 0.17.0 obtido em diretório temporário local, sem alterar a aplicação ou o sistema.
- Primeira compilação do original falhou antes de processar LaTeX: indisponibilidade do bundle `https://relay.fullyjustified.net/default_bundle_v33.tar.index.gz`. Nenhum PDF completo gerado nessa tentativa. Em investigação.
- Os quatro PDFs originais dos diagramas foram renderizados e inspecionados, além do PNG do protótipo. Evidenciadas classes e atributos desatualizados, autenticação modelada indevidamente como include e descrição das telas em ordem incompatível com a imagem.

## Resultado da rodada técnica (03/11/2026)

**Permanece Aguardando resposta.** O PDF é uma versão parcial para revisão; não é a entrega acadêmica completa. As pendências acadêmicas não foram substituídas por atividades técnicas nem retiradas do escopo.

### Fontes bibliográficas conferidas

- Booch, Rumbaugh e Jacobson: *The Unified Modeling Language User Guide*, 2. ed., Addison-Wesley, 2005, ISBN 9780321267979. Dados editoriais: https://www.informit.com/store/unified-modeling-language-user-guide-9780321267979; local confirmado no catálogo https://search.worldcat.org/title/799556306. Foi identificada explicitamente a edição em inglês; não se inventou uma ficha para a tradução brasileira.
- Larman: *Utilizando UML e padrões: uma introdução à análise e ao projeto orientados a objetos e ao desenvolvimento iterativo*, 3. ed., Bookman, 2007, ISBN 9788560031528. Editora: https://loja.grupoa.com.br/utilizando-uml-e-padroes-3ed-ebook-p988162; edição/local: https://search.worldcat.org/title/817066961.
- As cinco entradas bibliográficas anteriores foram preservadas nos fontes; não foram acrescentadas artificialmente ao PDF com `nocite`. As duas citações utilizadas possuem correspondentes na bibliografia. Essa conferência de metadados não alega leitura integral dos livros.

### Compilação e verificações

- Comando reproduzível: `TECTONIC_BIN=tmp/latex-runtime/tectonic TECTONIC_BUNDLE=https://data1b.fullyjustified.net/tlextras-2022.0r0.tar python3 docs/projeto/scripts/compilar.py` (da raiz).
- O script usa uma cópia temporária limpa. Tectonic 0.17.0 executou LaTeX, BibTeX 0.99d e passagens de estabilização. Os capítulos passaram de `include` a `input`, mantendo labels e quebras de capítulo, para evitar tentativas indevidas de BibTeX nos auxiliares individuais. Pós-textuais e bibliografia estão exclusivamente no arquivo principal.
- A indisponibilidade inicial do relay foi contornada pelo endereço direto do bundle. PDFs vetoriais foram gerados em versão 1.5 compatível, removendo os avisos de inclusão de versão mais recente. Foi removida também a duplicação de âncora da capa.
- Resultado: **39 páginas físicas**, A4, PDF 1.5. Capa não contada; introdução na página impressa 8, física 9; referências na página impressa 38, física 39.
- Log final: sem erros LaTeX/BibTeX, citações ou remissões indefinidas, caracteres ausentes, overfull ou necessidade de nova passagem. Resta `Underfull hbox (badness 1817)` na impressão da folha de rosto (`main.tex`, chamada de `imprimirfolhaderosto`), cujo parágrafo de natureza tem coluna estreita. A página física 2 foi inspecionada: texto integral, sem corte ou colisão. O aviso não foi ocultado.
- Todas as páginas foram renderizadas com Poppler a 1500 pixels no lado maior. Foram inspecionadas composição, limites, paginação, tabelas, fontes, diagramas e recortes. Na última iteração, as páginas renderizadas foram comparadas por SHA-256 com a rodada anterior: as 15 páginas alteradas foram reinspecionadas; as outras 24 são pixel a pixel idênticas às já inspecionadas. Não há página vazia no PDF vigente.
- Conferidos sumário (incluindo continuação) e listas contra títulos/legendas e páginas impressas. Foram preservados todos os labels anteriores, sem duplicação e sem remissão sem destino. Os quadros multipágina repetem número/cabeçalho e indicam continuação; a fonte fecha o quadro.
- Conferência estrutural: RF01–RF08, RNF01–RNF11, CT01–CT14 e as sete datas de junho de 2026 foram preservados. Todos os CT continuam pendentes, explicitamente no texto comum aos quadros; as prioridades permanecem nas respectivas legendas.
- `git diff --check` passou. Nenhum arquivo versionado da aplicação foi alterado. O checkout inicial era limpo; fontes e figuras foram alterados apenas em `docs/projeto/`, além dos artefatos de saída em `output/pdf/`.
- Verificação por execução da aplicação não foi realizada nesta rodada e não foi atribuída ao histórico da equipe. A conferência de código é estática; o gerador de dicionário importa somente metadados.

### Localização e aceite por exigência na versão parcial

Páginas abaixo são **impressas**, salvo quando explicitamente físicas. O fato de localizar um artefato não aprova automaticamente seu conteúdo acadêmico ou a ABNT global.

| Exigência | Fonte/evidência aplicada | Seção/página vigente | Verificação e situação na rodada |
|---|---|---|---|
| Capa e identificação | Dados existentes preservados | físicas 1–2; equipe impressa 34 | Três nomes legíveis, um por linha na capa/folha. **Integrantes, grafias e título confirmados pelo usuário na retomada**; permanecem pendentes a orientação institucional e os demais dados factuais não confirmados. |
| Resumo e abstract | Consolidação técnica e decisão do usuário | físicas 3–4 | Mesmos objetivos, procedimento documental e limitações; palavras-chave com ponto e vírgula. **Parcial**: revalidar após conteúdo acadêmico pendente. |
| Introdução e conclusão | Artefatos e implementação | cap. 1, p. 8; cap. 3, p. 37 | Textos ativos, sem capítulo vazio de metodologia e sem resultados fictícios. **Parcial** até integração das entregas acadêmicas. |
| Minimundo | Texto anterior + rotas e serviços | §2.1, p. 9 | Preservado domínio, estoque estimado e distinção de geolocalização prevista. **Atendido na conferência técnica**; aceite acadêmico global pendente. |
| RF01–RF08 | Requisitos anteriores + código | §2.2, p. 9–12; Quadro 1, p. 10 | IDs e metas mantidos; estado de implementação distinguido em §2.2.1. **Atendido na conferência documental**, sem alegar validação funcional. |
| RNF01–RNF11 | Configurações, serviços, rotas | Quadros 2–4, p. 10–11; §2.2.1, p. 11–12 | Retenção, p95, TLS, privacidade, CI/CD qualificados. `.editorconfig` existe vazio. **Atendido na conferência documental**, controles/metas sem prova continuam não validados. |
| Casos de uso | RF + rotas + projeto previsto | §2.3.1, p. 13–14; Figura 1, p. 13 | UC01–UC07 cobrem RF, atores externos e fronteira; favoritos exigem sessão como precondição; histórico público; extend de distância previsto. Diagrama final vetorial com posições explícitas em fonte Python/Pycairo. **Atendido tecnicamente**; sem afirmar execução. |
| Classes de coleta | Scrapers | §2.3.2.1, p. 14–15; Figura 2, p. 15 | BasePharmacyScraper, Araujo/Pacheco e módulo funcional Indiana conferidos; fontes editáveis preservados. **Atendido tecnicamente**. |
| Schemas | Pydantic/FastAPI Users | §2.3.2.2, p. 15; Figura 3, p. 16 | UsuarioRead/Create/Update e famílias de catálogo, ofertas e histórico em painéis legíveis. **Atendido tecnicamente**. |
| Classes ORM | Modelos e metadados da biblioteca herdada | §2.3.2.3, p. 15–16; Figura 4, p. 17 | Oito tabelas, incluindo associações e campos herdados, sem Favorito fictício. **Atendido tecnicamente**. |
| Projeto de banco | ORM; migrações até e4902ba81c6d | §2.4, p. 17–23; DER p. 18 | DER horizontal legível; cardinalidades e opcionalidade; cruzamento Anvisa sem FK. Divergências de padrão SQL/Python e índice composto registradas. **Atendido para a versão ORM documentada**, sem atestar banco vivo. |
| Dicionário | Geração de Base.metadata, dialeto PostgreSQL | §2.4.2, p. 19–23; Quadros 5–12 | Oito tabelas e 80 colunas, tipos/nulos, PK/FK, unicidade, padrões e ON DELETE das associações; remissões entre DER e cada descrição. **Atendido tecnicamente**. |
| Interfaces | PNG preservado e metadado Figma; código frontend | §2.5, p. 24–28; Figuras 6–9, p. 24–27 | Cinco telas identificadas como protótipo; recortes sem cortes de rótulos; diferenças com implementação e acessibilidade não comprovada explicitadas. **Parcial**: autoria/projeto editável e validação de jornadas não comprovadas. |
| Entregas por período, inclusive 6º | Sem originais disponíveis | Não incorporadas | **Aguardando informação**. Não atribuir artefatos atuais a períodos por inferência. |
| Diários de bordo | Sem originais disponíveis | Não incorporados | **Aguardando informação**. Não inventar presença, reuniões ou participação por histórico Git. |
| Capítulo Configuração e Manutenção de Software | Título e práticas 1–5 apenas na solicitação | Não criado | **Aguardando informação**: enunciados, entregas e confirmação de outras práticas. Capítulo vazio ou títulos de práticas não cumpririam a entrega. Escopo obrigatório preservado. |
| Plano de testes | CT existentes, sem prova histórica | §2.6, p. 28–36; Quadros 13–22 | CT13/RF02 na p. 33; CT14/p95 ≤500 ms na p. 33. Rastreabilidade na p. 32; recuperação de senha ainda sem caso específico e RNF sem procedimentos detalhados são lacunas explícitas. **Parcial**, sem execução atribuída. |
| Equipe e cronograma | Quadros históricos do plano | §2.6.7–2.6.8, p. 34–35 | Nomes, atribuições planejadas e sete datas mantidos; sequência de junho explicada sem mudar datas. **Aguardando informação** sobre confirmação e eventuais registros históricos. |
| Citações e referências | Editora e catálogos acima | Citações p. 12; referências p. 38 | Duas referências impressas e verificadas; bibliografia centralizada e sem indefinições. **Atendido tecnicamente**; conferência integral da edição normativa pertinente ainda pendente. |
| Apresentação e ABNT | Fontes/versões registradas no início | Documento inteiro | Inspeção de 39 páginas realizada. **Aguardando informação** sobre modelo/orientações aplicáveis; integral das normas pertinentes e tipografia institucional ainda não aprovadas. Compilação não comprova conformidade. |
| PDF e fontes | Build limpo + inspeção + diff | caminhos abaixo | **Atendido tecnicamente nesta versão parcial**; conteúdo acadêmico obrigatório ausente impede “Concluído”. |

### Caminhos e próxima retomada

- PDF: `output/pdf/preco-bao-revisao-parcial.pdf`.
- Principal: `docs/projeto/main.tex`; capítulos em `docs/projeto/capitulos/`.
- Evidência de compilação: `output/pdf/preco-bao-compilacao.txt`, `output/pdf/preco-bao.log` e `output/pdf/preco-bao.blg`.
- Fontes editáveis: `docs/projeto/figures/fontes/`; geradores e compilação em `docs/projeto/scripts/`.
- Matriz: este arquivo. Diagnóstico solicitado continua ausente.

Ao receber os materiais: confirmar orientação institucional e dados factuais; incorporar entregas/diários e práticas no capítulo específico; revisar resumo/introdução/conclusão; resolver lacunas acadêmicas/normativas; recompilar e reinspecionar todo o documento cuja paginação será afetada. O aceite final não foi concedido nesta rodada.

## Retomada — confirmação de integrantes e título

O usuário confirmou expressamente os integrantes Kayke Wellington Ribeiro Santos, Ana Clara de Souza e Aurora Drumond Costa Magalhães, além do título “Especificação e Projeto de Software: Plataforma Preço Bão”, com quebra de linha após os dois-pontos. A ordem já utilizada na capa foi preservada, pois a mensagem não solicitou reordenação de autoria.

O título existente em `main.tex` já corresponde ao informado e foi mantido. O nome de Kayke foi completado na capa/folha de rosto, na relação de integrantes, no quadro de equipe e nas duas atribuições do cronograma. As responsabilidades continuam descritas como planejamento, sem nova atribuição de execução. A confirmação resolve a dependência de nomes, composição da equipe e título; não confirma automaticamente instituição, natureza, local, ano ou regras de apresentação.

Permanecem pendentes os enunciados e entregas das práticas do 8º período, a relação de entregas anteriores (inclusive 6º), os diários originais, o diagnóstico ausente e as orientações institucionais/normativas aplicáveis. O estado geral permanece **Aguardando resposta**.

Verificação da retomada: compilação limpa concluída com bibliografia e referências estabilizadas; 39 páginas físicas preservadas. As páginas físicas 1, 2, 29, 35 e 36 foram renderizadas e reinspecionadas: nomes completos legíveis, sem cortes ou transbordamento. As outras 34 páginas são pixel a pixel idênticas à versão previamente inspecionada. As remissões e a paginação não mudaram. Log sem novos avisos, erros, caracteres ausentes ou referências indefinidas; permanece somente o underfull da folha de rosto já examinado. `git diff --check` passou. O manifesto de validação foi atualizado para o novo SHA-256 do PDF.

## Retomada — integração das Práticas 1 e 2

### Fontes recebidas e decisão de escopo

Recebidos em 03/11/2026 os arquivos `Atividade_Prática_01_Preenchida_Preço_Bão (1).docx` e `DOC-20260819-WA0006 (1).pdf`, no diretório Downloads do usuário. Cópias byte a byte preservadas em `fontes-academicas/pratica-01-preenchida.docx` e `fontes-academicas/pratica-02-preenchida.pdf`; nomes originais, tamanho e SHA-256 em `fontes-academicas/PROVENIENCIA.json`.

O Word foi extraído e renderizado com o runtime de documentos e LibreOffice empacotado: quatro páginas, última em paisagem. O PDF tem oito páginas em paisagem; todas foram extraídas e renderizadas. Todos os originais foram visualmente consultados. Os campos de data estão em branco: o nome `DOC-20260819` não fundamenta uma data de atividade. Os cabeçalhos identificam a disciplina Configuração e Manutenção de Software, o oitavo período e a professora Maíza Cristina de Souza Dias. Não se alteraram os demais dados institucionais do trabalho a partir das alternativas do formulário.

A Etapa 4 da Prática 2 pede análise por componente do grupo, mas o produto preenchido contém apenas M-01 sem autoria individual. Consultado o usuário, a decisão foi **“Use o plano coletivo”**. A seção 3.2.4 usa esse plano coletivo, sem fabricar análises individuais, atribuir papéis a pessoas ou declarar autorização da professora. Essa decisão expressa resolve a dependência específica de formato/autoria dessa etapa.

O conteúdo instrucional dos documentos é tratado como enunciado acadêmico. A revisão não executa manutenção na aplicação, não publica no AVA e não presume apresentação em aula a partir de solicitações dos roteiros. Os produtos efetivamente recebidos são respostas e planos; não há relatórios de execução ou métricas que autorizem converter propostas em resultados.

O artigo indicado na Prática 1 foi conferido na página original da DevMedia: https://www.devmedia.com.br/alternativas-para-reducao-de-problemas-na-manutencao-de-software-artigo-revista-engenharia-de-software-magazine-34/20113. Título confirmado; assinatura disponível “Mateus”, ano 2011; revista *Engenharia de Software Magazine*, número 34. Não se inventou sobrenome, paginação ou data completa. A síntese distingue a documentação interna ainda problemática no estudo das alternativas propostas para o PI. As ISO/IEC 12207 e 14764 e IEEE 1219 são mencionadas como referências dos roteiros/artigo, sem edição ou consulta integral inferidas.

### Alterações e evidência por atividade

O capítulo 3 foi inserido antes da conclusão por `input`, com numeração automática. A conclusão passou a capítulo 4. Resumo, abstract, introdução e conclusão foram ajustados ao conteúdo documental recebido. Não foram criadas seções vazias para as Práticas 3–5.

| Exigência / produto | Fonte e localização no original | Localização vigente no PDF (páginas impressas) | Situação | Ação aplicada | Dependência remanescente | Critério conferido |
|---|---|---|---|---|---|---|
| Prática 1 — solicitação e respostas | Word preenchido, itens 1–5 e 5.1 | §3.1, p. 37–40 | Atendido como produto documental; execução não comprovada | Síntese da leitura, componentes, desafios, riscos, alternativas e prioridades | Provas de apresentação/AVA/aplicação, se exigidas para aceite da atividade | Enunciado, produto e limites explicitados; não apenas reprodução do roteiro |
| Prática 1 — estimativas e itens | Word, item 4(b) e quadro 5.1 | Quadros 23–24, p. 39–40 | Atendido documentalmente | Preservados quatro itens e sete estimativas, sem datas ou custos monetários inventados | Sem medição realizada fornecida | Prazos e gravidade compatíveis com a ficha; continuação do Quadro 24 identificada |
| Prática 2 — levantamento/classificação | PDF, p. físicas 2–4, etapas 1–2 | §3.2.2, p. 41; Quadro 25 | Atendido documentalmente | Mantidos M-01–M-04, solicitantes por papel, impacto, tipo, justificativa e risco | Evidência de incidentes/execução não recebida | Classificação fiel sem transformar hipótese em causa reproduzida |
| Prática 2 — backlog | PDF, p. físicas 4–5, etapa 3 | §3.2.3, p. 42; Quadro 26 | Atendido documentalmente | Ordem M-01, M-04, M-02, M-03, prioridades e sprints preservadas | Nenhuma para transcrição do backlog | Distinção entre prioridade do backlog e criticidade de M-04 na reflexão |
| Prática 2 — plano de ação coletivo | PDF, p. físicas 5–7, etapa 4; decisão do usuário | §3.2.4, p. 42–43 | Atendido no formato coletivo decidido pelo usuário | Problema, causa provável, impacto, componentes, solução, estratégia, testes, recursos e estimativa | Execução e resultados não recebidos | Sem autoria individual inferida; causa provável e prazo de 1–2 dias qualificados |
| Prática 2 — sprints e equipes | PDF, p. físicas 7–8, etapa 5 | §3.2.5, p. 43–44; Quadro 27, p. 44 | Atendido como planejamento | Duas semanas/sprints planejadas, itens e papéis preservados | Sem datas e resultados de sprints | Não mapear equipes A/B/C aos três integrantes sem fonte |
| Prática 2 — reflexão | PDF, p. física 8, etapa 6 | §3.2.6, p. 44 | Atendido documentalmente | Criticidade, evolução, indicadores e gestão Scrum consolidados | Métricas medidas não fornecidas | Indicadores e cerimônias descritos como propostos |
| Escopo das práticas do oitavo período | Correção expressa do usuário: não houve atividades 3, 4 e 5 | Cap. 3, §§3.1–3.2 | Escopo confirmado: somente Práticas 1 e 2 | Retirada a cobrança de atividades inexistentes | Nenhuma relativa às Práticas 3–5 ou à confirmação de adicionais | Práticas efetivamente solicitadas incorporadas, sem criar entregas fictícias |

A ficha da Prática 2 menciona Cloudflare permanente; a Prática 1 propõe substituir túnel temporário. Sem datas e evidência de implantação correspondente, não se inventou sequência temporal nem se passou a declarar publicação permanente. M-03 continua como proposta histórica de histórico visual e alertas, embora o código atual já contenha parte de histórico. Os testes de M-01 são relacionados aos requisitos/casos gerais, deixando explícito que ciclos de remoção e nova autenticação acrescentam cenários. Nenhum CT foi marcado executado.

### Revalidação global da versão vigente

| Exigência | Fonte / localização atual | Verificação e estado |
|---|---|---|
| Capa, folha e equipe | Confirmação dos três nomes e título; físicas 1–2, §2.6.7 p. 34 | Legíveis e uniformes. Demais dados institucionais mantidos; confirmação ainda pendente. |
| Resumo e abstract | Físicas 3–4 | Conteúdo equivalente, incluindo manutenção como planejamento; palavras-chave mantidas com ponto e vírgula por decisão do usuário. |
| Introdução e conclusão | Cap. 1 p. 8; cap. 4 p. 45 | Coerentes com práticas integradas e limitações; capítulo novo citado e numerado automaticamente. |
| Minimundo, RF e RNF | §2.1–2.2.1 p. 9–12; Quadros 1–4 | Preservados RF01–RF08, RNF01–RNF11 e distinção de metas/implementação/validação. Aceite técnico mantido, sem prova funcional acrescentada. |
| Casos de uso e classes | §2.3 p. 12–17; Figuras 1–4 | Mesmas figuras vetoriais e fontes editáveis; legibilidade e remissões verificadas na nova renderização. |
| Banco, DER e dicionário | §2.4 p. 17–23; Figura 5 p. 18; Quadros 5–12 | Oito tabelas/80 colunas mantidas, fontes ORM/migrações e divergências explícitas. Sem consulta ao banco vivo. |
| Interfaces | §2.5 p. 24–28; Figuras 6–9 | Protótipo e ampliações preservados e inspecionados. Autoria/editável/validação permanecem sem comprovação. |
| Plano de testes | §2.6 p. 28–36; Quadros 13–22 | CT01–CT14 e sete datas de junho mantidos. Todos pendentes; CT13/RF02 e CT14/p95 de 500 ms preservados; sem execução atribuída. |
| Entregas anteriores, inclusive sexto período | Sem registros originais | Aguardando informação; nenhuma atribuição por inferência de código ou Git. |
| Diários de bordo | Sem registros originais | Aguardando informação; nenhuma presença, reunião ou autoria inventada. |
| Oitavo período | Cap. 3 p. 37–44, Quadros 23–27 | Práticas 1 e 2 integradas com produtos concretos e procedência. O usuário confirmou que não houve Práticas 3, 4 e 5; retirada essa pendência. |
| Referências | P. 46 | Cinco entradas impressas: duas fichas sem data/autoria inventadas, artigo e duas obras já conferidas. Citações distinguem os títulos das fichas; sem chave interna, remissão ou citação indefinida. Textos integrais normativos pertinentes continuam pendentes. |
| Listas, sumário e numeração | Físicas 5–8 | Nove figuras e 27 quadros; capítulo 3, seções e conclusão 4 localizados contra legendas, títulos e páginas impressas. Sem transbordamentos. |
| Apresentação e ABNT | Fontes e decisões normativas acima | Verificação visual local realizada; aceite global ainda depende de orientação/modelo institucional e fontes normativas integrais pertinentes, inclusive regra tipográfica e forma de representar documento sem data verificável. Não se estimou ano para as fichas. |
| Diagnóstico inicial | `docs/ANALISE_E_PROMPT_REVISAO_LATEX_PI.md` ausente | Aguardando arquivo para revalidar achados específicos. |
| Preservação e escopo | Diff e arquivos originais com SHA-256 | Alterações versionadas limitadas a `docs/projeto/`, saídas em `output/pdf/`; aplicação sem alterações. |

Compilação limpa pelo script documentado, com Tectonic 0.17.0, BibTeX e passagens de estabilização. Resultado: **47 páginas físicas**, última impressa **46**; introdução na impressa 8, capítulo de manutenção na 37, conclusão na 45 e referências na 46. PDF SHA-256: `6792e44477bd038693cd3ee76246289974a14972ffa06c849ffaa8166679b346`.

Todas as 47 páginas foram renderizadas a 1500 pixels no lado maior e inspecionadas. Após correções de citação e caractere ordinal, as físicas 3, 9, 38, 39, 41 e 47 foram renderizadas e reinspecionadas; as outras 41 são pixel a pixel idênticas às já inspecionadas nesta rodada. Não há páginas vazias, cortes, colisões ou quadros partidos sem identificação. Quadro 24 repete cabeçalho e número na continuação. As páginas de fontes originais também foram inspecionadas; seus problemas de cabeçalho não foram reproduzidos.

Log final sem erros LaTeX/BibTeX, overfull, caracteres ausentes, duplicação de labels/âncoras ou citações/remissões indefinidas. Permanece somente o underfull de badness 1817 da folha de rosto, já inspecionado e sem perda de texto. Conferidas 57 labels e 30 remissões distintas nos fontes; todos os destinos existentes. `git diff --check` passou. O manifesto `output/pdf/VALIDACAO_PI.json` foi atualizado.

**Estado geral: Aguardando resposta.** A integração das duas fichas foi realizada; a demanda completa continua aberta. Permanecem pendentes entregas anteriores/diários, diagnóstico e orientação institucional/fontes normativas indispensáveis. A cobrança das Práticas 3–5 e de confirmação de adicionais foi retirada após a correção expressa do usuário.

## Correção de escopo — somente Práticas 1 e 2

O usuário esclareceu: “Não tiveram atividades 3, 4 e 5.” A menção anterior veio do texto inicial anexado, que incluía “novo capítulo do 8º período com atividades práticas 1 a 5 e outras que tenham sido solicitadas”. Essa formulação inicial foi superada pela confirmação do usuário; não é evidência de enunciados ou entregas adicionais. As referências a 1–5 nas seções históricas acima registram a origem da dependência anterior, sem manter sua exigibilidade.

O escopo vigente do capítulo contém somente as Práticas 1 e 2, já incorporadas. Foram corrigidos a matriz atual e o manifesto de validação para retirar a pendência de Práticas 3–5 e a solicitação de confirmação de adicionais. Não havia títulos ou conteúdo dessas práticas no LaTeX; portanto, os fontes acadêmicos e o PDF de 47 páginas permanecem inalterados. SHA-256 do PDF conferido contra o manifesto, sem necessidade de recompilação por esta correção exclusivamente no registro de trabalho. As demais pendências da demanda original permanecem independentes desta decisão.
