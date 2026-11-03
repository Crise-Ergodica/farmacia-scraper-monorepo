# Documentação LaTeX do Preço Bão

O estado de aceite, as fontes e as dependências acadêmicas estão em
[REVISAO_FINAL_PI.md](REVISAO_FINAL_PI.md). O PDF parcial não representa aprovação
integral das entregas ou certificação ABNT.

## Compilar

Na raiz do repositório, com Tectonic ou TeX Live/latexmk no PATH:

```bash
python3 docs/projeto/scripts/compilar.py
```

O script compila uma cópia limpa e preserva bibliografia, passagens de
estabilização, PDF e log em `output/pdf/`. Não altera a aplicação nem usa banco.
Para indicar um Tectonic fora do PATH e um bundle alternativo:

```bash
TECTONIC_BIN=/caminho/tectonic \
TECTONIC_BUNDLE=https://data1b.fullyjustified.net/tlextras-2022.0r0.tar \
python3 docs/projeto/scripts/compilar.py
```

A rodada de revisão usou Tectonic 0.17.0, bundle `tlextras-2022.0r0`, classe
abntex2 1.9.7 e BibTeX 0.99d. O runtime obtido temporariamente não integra a
entrega. Disponibilidade do bundle remoto não é garantida.

## Fontes e diagramas

`main.tex` reúne os includes e centraliza pós-textuais e bibliografia.
`capitulos/02-dicionario.tex` é gerado a partir do ORM. A numeração dos capítulos
é automática; nenhum número literal X deve ser acrescentado.

Os diagramas incorporados são PDFs vetoriais compatíveis com PDF 1.5. Suas fontes editáveis estão em
`figures/fontes/*.dot` e `figures/fontes/diagrama-caso-de-uso.py`; o retrato estruturado do ORM está em
`figures/fontes/esquema-orm.json`. A visão de schemas e a visão ORM têm painéis
para manter a legibilidade; os arquivos `diagrama-schemas` e `diagrama-orm`
conservam também uma visão agregada. O DER omite atributos não-chave no desenho,
mas remete às oito descrições e às 80 colunas do dicionário.

Com as dependências do backend instaladas e Graphviz, Ghostscript e Pycairo (no Python 3 do sistema):

```bash
PYTHONPATH=backend backend/.venv/bin/python docs/projeto/scripts/gerar_artefatos.py
```

O gerador importa somente os modelos, sem carregar `.env`, consultar banco,
executar migrações ou coletar dados externos. Antes de regenerar, confira qual
versão do código o documento deverá representar. Os modelos atuais não provam
o esquema aplicado a um banco vivo.

O protótipo PNG original é preservado. As ampliações usam recortes LaTeX da
mesma imagem. Os metadados indicam Figma; não foi encontrado o projeto editável.
Não são capturas da aplicação atual.

## Atividades acadêmicas

`capitulos/configuracao-manutencao.tex` incorpora as Práticas 1 e 2 do 8º
período como análises e propostas documentadas. Os originais fornecidos estão
em `fontes-academicas/`, com manifesto de procedência e SHA-256. A etapa 4 da
Prática 2 usa o plano coletivo por decisão expressa do usuário. As atividades
ainda ausentes e os limites de evidência estão na matriz de revisão.
