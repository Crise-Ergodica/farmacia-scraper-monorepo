# Preço Bão — remoção Drogasil e prontidão de hospedagem

Data: 31/10/2026
Worktree: `C:\dev\farmacia-scraper-monorepo-ana`
Branch verificada: `ana`

Nenhum commit, branch, merge ou rebase foi criado. A outra worktree (`C:\dev\farmacia-scraper-monorepo`) não foi editada. Nenhum container foi iniciado/reiniciado, nenhum scraper foi executado, nenhum banco foi consultado ou modificado e nenhum serviço foi publicado.

## Parte A — descontinuação Drogasil

### Inventário e remoções

Os artefatos abaixo foram identificados como exclusivos do experimento antes da remoção. Os caminhos removidos foram:

- `backend/app/core/drogasil_settings.py`, `backend/app/scrapers/drogasil.py`, `backend/app/scrapers/drogasil_apify.py` e `backend/app/services/drogasil_import.py` — configuração, parser/coletor, adaptador Apify e importador.
- `backend/tests/test_drogasil_scraper.py`, `backend/tests/test_drogasil_import.py`, `backend/tests/test_drogasil_apify.py` e `backend/tests/fixtures/drogasil_real_product_sanitized.html` — testes e fixture exclusivos.
- `backend/scripts/capture_drogasil_hml_web.mjs`, `backend/scripts/homologar_drogasil_postgres.py`, `backend/Dockerfile.homologation`, `deploy/homologation/docker-compose.drogasil.yml` e a extensão `tools/drogasil-browser-capture/` — execução e captura de homologação.
- `backend/drogasil-validacao-01.json`, `backend/drogasil-validacao-02.json`, `backend/drogasil-validacao-04.json` e `backend/reports/drogasil-homologation-captures/` — dados/capturas sintéticas.
- Relatórios `backend/reports/drogasil-*.md` (incluindo diagnóstico HTTP 403, parser, importador, Apify, homologação PostgreSQL, fontes e políticas de localização) — removidos e substituídos por esta decisão resumida.
- Oito exports Expo temporários `.expo-drogasil-*` no frontend — artefatos gerados da homologação.

Não encontrei dependência adicionada exclusivamente para Drogasil que pudesse ser removida com segurança: `beautifulsoup4` e `curl-cffi` são usados por Araújo/Pacheco e em ferramentas compartilhadas; Playwright é usado por scripts de validação visual não relacionados. Não alterei `pyproject.toml`, lockfiles nem dependências frontend. Nenhum arquivo compartilhado de catálogo farmacológico ou dados de medicamentos foi excluído.

### Alterações compartilhadas

- Removi de `backend/app/api/routes/catalogo.py` a validade, variável `DROGASIL_OFFER_MAX_AGE_HOURS` e a exclusão/consulta especial pelo nome da farmácia. A listagem volta a usar a disponibilidade comum das ofertas.
- Removi as variáveis `DROGASIL_DEFAULT_*` e `DROGASIL_OFFER_MAX_AGE_HOURS` de `backend/.env.example`.
- Ajustei os testes de histórico e comparação para usar Indiana, Araújo e Pacheco; os testes de agrupamento por contexto continuam cobrindo comportamento genérico sem mock Drogasil.
- Mantive os campos opcionais de canal/localidade e chave de contexto como metadados genéricos de oferta/histórico. Eles não ativam coleta nem dependem de fornecedor.
- O Compose local deixa de iniciar Pacheco e atualização de ofertas por padrão: ambos estão no perfil explícito `scrapers`, sem reinício automático. Manutenção de imagens permanece no perfil `maintenance` e também não reinicia automaticamente. Isso altera apenas a configuração para próximas execuções; nenhum container atual foi alterado.

### Alembic e bancos

A revisão `c42a83d1710e` tem como pai `e4902ba81c6d`, é a única head e não possui migração filha. O relatório de homologação consultado antes de sua retirada registra aplicação e `alembic check` em um PostgreSQL 15 isolado. Não foi consultado o estado de nenhum outro banco nesta etapa; portanto a migração não foi removida nem reescrita, e nenhum downgrade foi executado.

A revisão cria colunas genéricas de contexto em ofertas/histórico e a tabela `identidades_catalogo_fonte`. Mantive o arquivo de migração e o modelo genérico `IdentidadeCatalogoFonte` no metadata para Alembic reconhecer esquemas que já receberam a revisão. Não há importador ativo que grave nessa tabela. A base isolada que contém registros sintéticos também não foi alterada ou apagada; registros de outros bancos, catálogos, ofertas e históricos foram preservados.

### Referências residuais e farmácias

A busca em código ativo, testes, scripts, configurações e deploy não encontrou `Drogasil`, `DROGASIL_*`, `APIFY_TOKEN`, `drogasil_apify` ou `drogasil_import`. Permanecem menções intencionais apenas na nota `docs/drogasil-discontinued.md` e em referências a este relatório. Os termos de contexto de venda restantes são genéricos e necessários para compatibilidade do histórico/migração.

Indiana, Araújo e Pacheco permanecem nos coletores existentes; os testes de backend incluem o teste Pacheco e a suíte passou após a remoção. Não foi executada coleta real.

## Parte B — hospedagem futura

Arquitetura preparada e independente do fornecedor:

```text
Web / Android → HTTPS → Caddy → Expo Web estático
                              └→ FastAPI → rede privada → PostgreSQL persistente
```

- `deploy/production/docker-compose.yml` contém somente `db`, `api`, `web` e `proxy`. O banco não publica porta; apenas Caddy publica 80/443. A rede da API é separada da Web, e Uvicorn aceita `X-Forwarded-*` somente do IP configurado de Caddy. A sub-rede/IP internos são configuráveis no arquivo de ambiente e precisam ser ajustados se houver conflito.
- `deploy/production/Caddyfile` tem hosts configuráveis, cabeçalhos de segurança, proxy reverso e HTTPS automático quando os domínios reais estiverem apontados e o servidor estiver acessível. Ainda não houve emissão ou teste de certificado real.
- `deploy/production/env.example` usa `example.invalid`, exige valores de domínio/API/CORS e segredos substituídos. O backend em produção valida origem HTTPS exata e segredo JWT forte. `.env.production` deve ficar fora do Git.
- `frontend/Dockerfile.web` cria export estático Expo Web; `frontend/nginx.production.conf` faz fallback de rotas do Expo Router e serve assets estáticos. O bundle Android exige API HTTPS para build standalone; nenhum domínio fictício foi inserido como configuração de produção.
- O PostgreSQL usa volume persistente e rede interna. O runbook `docs/preco-bao-deployment-guide.md` documenta configuração, migração manual, backup PostgreSQL e do arquivo JSON de imagens, restauração isolada, atualização, rollback, Android e checklist de publicação.
- O Compose de produção não inclui scraper, scheduler ou rotina de manutenção. Migrações só ocorrem com comando explícito, fora do `up` padrão.

Não escolhi fornecedor, comprei domínio, configurei DNS/firewall, abri portas, publiquei endpoints ou reutilizei dados atuais num servidor. O runbook sugere 2 vCPU, 8 GB RAM e 100 GB SSD apenas como estimativa inicial para orçamento, a validar por medição. Rate limiting/WAF, política final de logs/privacidade, armazenamento externo de backup, monitoramento operacional e teste de restauração integral continuam pendentes antes da publicação.

## Parte C — validações e status

| Área | Resultado observado | Classificação |
|---|---|---|
| Pytest backend | 85 testes passaram | Validado localmente; SQLite em memória/conftest, sem banco principal |
| Ruff | `ruff check app tests migrations scripts` passou | Validado localmente |
| Import FastAPI/modelos | 29 rotas e 9 tabelas registradas | Verificação local de import |
| Alembic | Uma head (`c42a83d1710e`); cadeia impressa sem erro | Verificado sem conexão; `alembic check` não executado nesta etapa |
| Jest | 17 suítes, 95 testes passaram | Validado localmente; avisos `act(...)` de conectividade, sem falhas |
| TypeScript / ESLint | `tsc --noEmit` e `npm run lint` passaram | Validado localmente |
| Expo Web / Android | Export de cada plataforma passou; Web contém `index.html` e export Android tem `metadata.json` | Build/export somente; não é teste funcional Android nem APK de produção |
| Docker Compose produção | `docker compose ... config --quiet` passou; serviços: db, api, web, proxy | Validação estática, nenhum container iniciado |
| Compose local | Serviços padrão: db e api; coletores/manutenção ficam fora dos perfis padrão | Verificado estaticamente |
| `git diff --check` | Passou, com avisos de conversão LF/CRLF do Git | Validado localmente |
| PostgreSQL de homologação persistente | Revisão aplicada em banco isolado em homologação anterior | Estado não consultado nem alterado nesta etapa |
| PostgreSQL principal | Nenhuma consulta, migração ou escrita feita | Preservado; estado não verificado agora |
| Navegador/Android físico | Não executado nesta remoção/preparação | Funcionalidade não homologada nesta etapa |
| Servidor/domínio/HTTPS público | Não existe configuração real aplicada | Pendente de escolha e publicação autorizada |

Os comandos de teste frontend resolveram dependências pelo `node_modules` já disponível em `C:\dev\farmacia-scraper-monorepo\frontend`; nenhum arquivo dessa outra worktree foi editado. Os exports foram gravados em diretórios temporários e removidos após a verificação.

## Arquivos alterados nesta etapa

- Alterados: `backend/app/api/routes/catalogo.py`, `backend/.env.example`, `backend/docker-compose.yml`, `backend/app/models/identidade_catalogo_fonte.py` (somente docstring de compatibilidade), `frontend/src/__tests__/history-series.test.ts`, `frontend/src/__tests__/medicine-detail.test.ts`, `deploy/production/docker-compose.yml`, `deploy/production/env.example`, `docs/preco-bao-production-readiness.md`.
- Adicionados: `docs/drogasil-discontinued.md`, `docs/preco-bao-deployment-guide.md` e este relatório.
- Removidos: arquivos e artefatos exclusivos listados na Parte A.
- Preservados: todas as demais alterações locais identificadas em `git status`, incluindo melhorias preexistentes de catálogo/imagens/histórico/favoritos, exports Android e relatórios visuais sem vínculo exclusivo comprovado com a integração.
