# Backend — Preço Bão

API RESTful em FastAPI para coleta, enriquecimento e consulta de preços de medicamentos. O backend expõe catálogo, ofertas, histórico de preços, favoritos e autenticação JWT via `fastapi-users`, além de hospedar scrapers e rotinas de manutenção de imagens.

## Arquitetura

```text
backend/
├── app/
│   ├── api/routes/       # Endpoints FastAPI (catálogo, usuários, histórico)
│   ├── core/             # Configuração, banco de dados, auth JWT e utilitários
│   ├── models/           # Modelos SQLAlchemy (ORM)
│   ├── schemas/          # Schemas Pydantic (validação de entrada/saída)
│   ├── scrapers/         # Módulos de scraping por farmácia
│   ├── services/         # Regras de negócio, enriquecimento e imagens
│   ├── main.py           # Ponto de entrada da aplicação
│   └── __init__.py
├── migrations/           # Migrações Alembic
├── scripts/              # ETL CMED, manutenção de imagens e auditorias
├── tests/                # Testes unitários e de integração (pytest)
├── docker-compose.yml    # PostgreSQL, API, túnel Cloudflare e manutenção
├── alembic.ini           # Configuração do Alembic
├── pyproject.toml        # Dependências Poetry e configuração de ferramentas
└── .env.example          # Template de variáveis de ambiente
```

### Camadas

- **`api/routes/`**: controladores finos que recebem requisições HTTP, delegam aos serviços e retornam JSON. Rotas atuais: `catalogo`, `usuarios`, `historico`.
- **`core/`**: configurações globais. `auth.py` configura `fastapi-users` com backend JWT. `database.py` gerencia sessões SQLAlchemy. `utils.py` contém funções auxiliares. CORS é configurado em `main.py` lendo `BACKEND_CORS_ORIGINS` como lista JSON; o regex `https?://(localhost|127\.0\.0\.1)(:\d+)?` libera qualquer porta local para o Expo dev server.
- **`models/`**: tabelas PostgreSQL via SQLAlchemy. Entidades principais: `CatalogoBase`, `OfertaFarmacia`, `AnvisaMedicamento`, `HistoricoPreco`, `Usuario`, `Farmacia`. Favoritos usam tabelas associativas com chave primária composta (`usuario_medicamento_favorito`, `usuario_farmacia_favorita`).
- **`schemas/`**: validação Pydantic separada dos modelos ORM. Schemas de leitura e escrita podem divergir para filtrar campos sensíveis.
- **`scrapers/`**: módulos isolados por farmácia (`araujo.py`, `indiana.py`) com base comum em `base.py`. Usam `httpx` e `BeautifulSoup`. Layouts mudam frequentemente; cada scraper precisa de manutenção contínua.
- **`services/`**: orquestração de regras de negócio. `enriquecimento.py` cruza dados CMED com ofertas raspadas. `imagens.py` valida e associa URLs de imagens. `image_reference_portability.py` migra referências legadas. `preco_observacoes.py` normaliza observações de preço.

## Variáveis de ambiente

Copie `.env.example` para `.env` (ou use `make envs` na raiz):

| Variável | Descrição |
|---|---|
| `DATABASE_URL` | URL de conexão PostgreSQL para uso local (`127.0.0.1:4242`) |
| `DATABASE_URL_DOCKER` | URL de conexão para contêineres (`db:5432`) |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Credenciais do PostgreSQL |
| `JWT_SECRET` | Segredo aleatório longo para assinatura JWT. Trocar invalida tokens existentes |
| `BACKEND_CORS_ORIGINS` | Lista JSON de origens permitidas (ex: `["http://localhost:8081"]`) |
| `IMAGE_MONITOR_ENABLED` | Ativa monitoramento periódico de URLs de imagens |
| `IMAGE_RECOVERY_ENABLED` | Ativa recuperação automática de imagens quebradas |
| `IMAGE_MONITOR_BATCH_SIZE` | Quantidade de imagens verificadas por ciclo |
| `IMAGE_RECOVERY_BATCH_SIZE` | Quantidade de imagens recuperadas por ciclo |
| `IMAGE_MONITOR_RECHECK_HOURS` | Intervalo mínimo entre reverificações da mesma imagem |
| `IMAGE_MONITOR_CONCURRENCY` | Concorrência máxima nas verificações de imagem |
| `IMAGE_MONITOR_HOST_INTERVAL` | Delay entre requisições ao mesmo host (respeito a rate limits) |
| `IMAGE_MAINTENANCE_INTERVAL_SECONDS` | Intervalo entre ciclos do serviço de manutenção |

Senhas com caracteres especiais devem usar percent-encoding nos URLs de conexão.

## Comandos locais

```sh
cd backend
poetry install                              # Instala dependências
poetry run alembic upgrade head             # Aplica migrações
poetry run uvicorn app.main:app --reload    # Inicia API em modo desenvolvimento
poetry run python -m pytest -q              # Roda testes
poetry run ruff check app tests             # Verifica estilo de código
```

Na raiz do monorepo, os comandos equivalentes são `make setup-back`, `make migrate-back`, `make run-back`.

## Docker Compose

O `docker-compose.yml` define quatro serviços:

| Serviço | Descrição |
|---|---|
| `db` | PostgreSQL 15 Alpine. Porta `4242` (host) → `5432` (contêiner). Volume persistente `postgres_data`. Health check via `pg_isready`. |
| `api` | FastAPI na porta `8000`. Depende de `db` saudável. Usa `DATABASE_URL_DOCKER`. |
| `image-maintenance` | Ciclo contínuo de verificação e recuperação de imagens. Perfil `maintenance` (não inicia por padrão). |
| `tunnel` | Cloudflare Tunnel (`cloudflared`) expondo a API publicamente. Útil para acessar a API de dispositivos móveis fora da rede local sem configurar IP público ou DNS. |

### Execução

```sh
# Subir apenas banco e API
docker compose up -d db api

# Subir tudo incluindo manutenção de imagens
docker compose --profile maintenance up -d

# Derrubar e destruir volumes
docker compose down -v
```

A porta `4242` do PostgreSQL é exposta no host para permitir conexões diretas de clientes SQL externos (DBeaver, psql, etc.) durante o desenvolvimento.

## Pipeline ETL (CMED)

O catálogo base vem da planilha oficial da ANVISA/CMED. O pipeline tem duas etapas:

1. **Conversão** (`scripts/convert_cmed_xls_to_csv.py`): lê o XLSX (pulando 41 linhas de cabeçalho), limpa colunas vazias e exporta CSV UTF-8 com separador `;`.
2. **Ingestão** (`scripts/ingest_anvisa_cmed.py`): normaliza EANs (remove hifens, espaços, zeros à esquerda; aceita 13 ou 14 dígitos), faz upsert no modelo `AnvisaMedicamento` via SQLAlchemy.

Execute pela raiz:

```sh
make etl-run                                                    # Caminhos padrão
make etl-run CMED_XLSX=data/nova.xlsx CMED_CSV=data/cmed.csv   # Caminhos customizados
```

### Scripts adicionais

| Script | Função |
|---|---|
| `ingest_anvisa_oficial.py` | Ingestão alternativa com classificação oficial ANVISA |
| `manter_imagens_catalogo.py` | Verifica URLs de imagens e recupera candidatas pendentes (usado pelo serviço `image-maintenance`) |
| `processar_imagens.py` | Processamento em lote de imagens do catálogo |
| `capturar_frontend_imagens.py` | Captura imagens renderizadas no frontend para validação |
| `portar_referencias_imagens.py` | Migra referências de imagens entre formatos legados |
| `reclassificar_imagens_genericas.py` | Reclassifica imagens genéricas com base em metadados |
| `auditar_integridade_catalogo.py` | Verifica consistência entre catálogo, ofertas e imagens |
| `validar_imagens_catalogo.py` | Valida URLs de imagens ativas no catálogo |
| `verificar_cobertura_referencias_imagens.py` | Reporta cobertura de referências de imagens por produto |
| `testar_restauracao_referencias.py` | Testa restauração de referências de imagens a partir de backups |
| `validar_favoritos_imagem_browser.py` | Valida imagens de favoritos via navegador headless |
| `validar_fluxos_imagem_frontend.py` | Valida fluxos completos de exibição de imagens no frontend |

## Endpoints

Rotas montadas em `app/main.py`:

### Health check

| Método | Path | Descrição |
|---|---|---|
| GET | `/` | Retorna `{"Hello": "Aurora"}` |

### Catálogo (`/catalogo`)

| Método | Path | Descrição |
|---|---|---|
| GET | `/catalogo` | Lista paginada de medicamentos com busca e filtros |
| GET | `/catalogo/farmacias` | Lista todas as farmácias cadastradas |
| GET | `/catalogo/mais-baratos` | Medicamentos mais baratos (limite configurável) |
| GET | `/catalogo/filtros/opcoes` | Opções disponíveis para filtros dinâmicos |
| GET | `/catalogo/medicamentos/{id}` | Detalhes do medicamento com ofertas |
| GET | `/catalogo/medicamentos/{id}/imagem` | Redirecionamento para imagem do medicamento (oculto do schema) |

### Autenticação e Usuários

Autenticação gerenciada por `fastapi-users` (configurado em `app/core/auth.py`).

| Método | Path | Descrição |
|---|---|---|
| POST | `/auth/jwt/login` | Login com email e senha, retorna JWT |
| POST | `/auth/register` | Cadastro de nova conta |
| GET | `/users/me` | Perfil do usuário autenticado |
| PATCH | `/users/me` | Atualiza perfil do usuário autenticado |

### Favoritos

Favoritos são divididos em dois recursos independentes. Todos exigem JWT válido.

**Medicamentos:**

| Método | Path | Descrição |
|---|---|---|
| GET | `/users/me/favoritos/medicamentos` | Lista medicamentos favoritos |
| POST | `/users/me/favoritos/medicamentos/{id}` | Adiciona medicamento aos favoritos |
| DELETE | `/users/me/favoritos/medicamentos/{id}` | Remove medicamento dos favoritos |

**Farmácias:**

| Método | Path | Descrição |
|---|---|---|
| GET | `/users/me/favoritos/farmacias` | Lista farmácias favoritas |
| POST | `/users/me/favoritos/farmacias/{id}` | Adiciona farmácia aos favoritos |
| DELETE | `/users/me/favoritos/farmacias/{id}` | Remove farmácia dos favoritos |

### Histórico de Preços (`/api/v1/medicines`)

| Método | Path | Descrição |
|---|---|---|
| GET | `/api/v1/medicines/{id}/history` | Histórico de preços por medicamento. Parâmetros: `periodo` (`7d`, `30d`, `90d`, `6m`, `1y`, `all`), `farmacia_id` (opcional) |

Tokens JWT expiram em uma hora. Não há lista de revogação no servidor; logout remove o token apenas no cliente.

## Modelos de dados

| Modelo | Tabela | Descrição |
|---|---|---|
| `CatalogoBase` | `catalogo_base` | Catálogo unificado de medicamentos (SKU interno, EAN, nome, laboratório) |
| `AnvisaMedicamento` | `anvisa_medicamento` | Dados oficiais CMED/ANVISA |
| `OfertaFarmacia` | `oferta_farmacia` | Preços e disponibilidade raspados por farmácia |
| `HistoricoPreco` | `historico_preco` | Série temporal de preços por oferta |
| `Farmacia` | `farmacia` | Cadastro de farmácias alvo |
| `Usuario` | `usuario` | Contas de usuário com hash de senha |
| `usuario_medicamento_favorito` | `usuario_medicamento_favorito` | Associação muitos-para-muitos (usuário ↔ medicamento favorito) |
| `usuario_farmacia_favorita` | `usuario_farmacia_favorita` | Associação muitos-para-muitos (usuário ↔ farmácia favorita) |

## Testes

```sh
poetry run python -m pytest -q                                  # Todos os testes
poetry run python -m pytest tests/test_api_usuarios.py -v       # Arquivo específico
```

Suíte atual cobre: integridade do catálogo, filtros de classificação, sessões e favoritos, histórico de preços e imagens, manutenção de imagens, portabilidade de referências, validação de modelos, idempotência de scrapers sem EAN, e integração com banco de dados.

Testes usam mocks para evitar requisições reais a farmácias. Dados de teste são configurados em `tests/conftest.py`.

## Migrações

Gerenciadas pelo Alembic. Configuração em `alembic.ini` e `migrations/env.py`.

```sh
poetry run alembic upgrade head                         # Aplica todas as migrações pendentes
poetry run alembic revision --autogenerate -m "descricao"  # Cria nova migração a partir das mudanças nos modelos
poetry run alembic downgrade -1                         # Reverte última migração
poetry run alembic history                              # Lista todas as migrações existentes
```

Migrações existentes cobrem: tabelas iniciais, modelo ANVISA, separação catálogo/ofertas, categorias e enriquecimento, usuários e favoritos, referências de imagens, histórico com observações, SKU vs EAN, expansão de ingrediente ativo, e manutenção de imagens.

## Segurança

- `JWT_SECRET` deve ser gerado aleatoriamente e mantido estável entre reinícios.
- Nunca commite `.env`. Use `.env.example` como template.
- CORS permite localhost em qualquer porta via regex para compatibilidade com Expo dev server.
- Tokens JWT não são revogados no servidor; expiram naturalmente em uma hora.
- Senhas de banco com caracteres especiais exigem percent-encoding nos URLs.
- A autenticação usa `fastapi-users` com backend JWT. Configuração completa em `app/core/auth.py`.