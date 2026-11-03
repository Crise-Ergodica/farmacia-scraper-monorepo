# Preco Bao — prontidao para hospedagem e dominio

Revisao: 2026-10-31. Este documento prepara uma futura implantacao; nao cria recursos externos, nao migra dados e nao inicia servicos.

## Resumo

A arquitetura está preparada para Linux com Docker Compose, sem fornecedor escolhido. Publicação futura depende de domínio próprio, DNS, segredos, backups externos e validação em staging. O dimensionamento de 2 vCPU, 8 GB RAM e 100 GB SSD é uma estimativa inicial a confirmar com medições. Consulte preco-bao-deployment-guide.md para o runbook.

## Arquitetura preparada

```text
Browser ── HTTPS app.<dominio> ── Caddy ── Nginx/Expo Web (estatico)
                         │
Android ─ HTTPS api.<dominio> ── Caddy ── FastAPI ── rede privada ── PostgreSQL
                                                        └── volume JSON de referencias de imagem
```

Arquivos de exemplo adicionados, sem dominio real, credenciais ou dados:

- `deploy/production/docker-compose.yml`: API, PostgreSQL sem `ports` publicados, web estatico e proxy Caddy. Scrapers e workers nao estao incluidos. Apenas o proxy tem portas publicadas.
- `deploy/production/Caddyfile`: dois hosts, TLS automatico via ACME quando os DNS reais apontarem ao servidor e as portas estiverem acessiveis.
- `deploy/production/env.example`: valores reservados em `.invalid`; copiar para `.env.production` apenas ao preparar staging real, substituir todos os placeholders e proteger o arquivo.
- `frontend/Dockerfile.web` e `frontend/nginx.production.conf`: export web Expo no build, exige `EXPO_PUBLIC_API_URL` HTTPS e serve a pasta estatica `dist`.

O Compose local continua sendo somente para desenvolvimento e publica API e PostgreSQL no host. Nesta revisão, Pacheco e atualização de ofertas ficam no perfil explícito scrapers, e manutenção de imagens no perfil maintenance; esses serviços não fazem parte do up padrão e usam restart no. O Compose de produção não inclui scrapers, manutenção ou migração automática.

### Producao no backend

`APP_ENV=production` agora exige `BACKEND_CORS_ORIGINS` como lista de origens HTTPS exatas, rejeita `*`/origens HTTP, desativa regex de localhost e remove `/docs`, `/redoc` e `/openapi.json`. Tambem exige `JWT_SECRET` unico com no minimo 32 caracteres e rejeita placeholders comuns. JWT e autorizacao por usuario permanecem ativos.

Foram adicionados /health/live e /health/ready. O Compose de producao usa readiness no healthcheck da API e limita X-Forwarded ao IP configurado do Caddy numa rede isolada. Login, cadastro, catalogo, detalhes e historico recebem rate limit por IP com resposta 429 e Retry-After; os limites sao configuraveis. O contador e process-local e o Compose tem uma instancia API: nao escalar horizontalmente sem store de estado compartilhada ou limitacao compartilhada no edge. Configurar WAF/edge contra abuso distribuido antes da publicacao. CORS nao substitui autenticacao.

### Dominio, DNS e HTTPS

1. Registrar/usar somente dominio sob controle do proprietario. Os exemplos `app.example.invalid` e `api.example.invalid` sao placeholders, nao enderecos publicaveis.
2. Configurar registros A e, se houver IPv6 funcional no host, AAAA para app/API. Confirmar que o firewall do servidor/host aceita entrada 80 e 443 antes de iniciar Caddy. Com hostnames reais, DNS apontado e portas abertas, [Caddy provisiona/renova TLS e redireciona HTTP para HTTPS](https://caddyserver.com/docs/automatic-https); os dados persistentes do Caddy devem ser preservados.
3. Caddy solicita e renova certificados TLS automaticamente. Persistir `caddy_data` e `caddy_config`; nao copiar certificados para Git.
4. Configurar `BACKEND_CORS_ORIGINS` para exatamente `https://app.<dominio-real>`. O Android consome HTTPS diretamente e nao usa CORS.
5. Compilar um APK standalone com `EXPO_PUBLIC_API_URL=https://api.<dominio-real>` e `-PstandaloneApiMode=https`. A URL e publica no bundle; nao colocar segredos nela. Validar certificado e API real antes de distribuir.

## Dimensionamento inicial (estimativa)

A configuracao deve poder ser executada em Linux com Docker Compose, sem depender de um fornecedor. Como ponto de partida para cotacao e teste, considerar uma VM com 2 vCPU, 8 GB RAM e SSD de 100 GB; isso e uma estimativa de planejamento, nao uma medicao de consumo nem garantia de capacidade. Medir memoria da API/PostgreSQL, tamanho e crescimento do banco, armazenamento de imagens/backups, conexoes e latencia antes de escolher o host. Um PostgreSQL gerenciado tambem e possivel se oferecer rede privada, backup restauravel e conexao TLS; nenhum fornecedor foi escolhido.

## Dados, persistencia e backups

- PostgreSQL: volume Docker `postgres_data`; em VPS, criptografia de disco/host e backup externo continuam necessarios. Nao compartilhar a porta 5432 nem publicar o servico. Nao copiar dados atuais para terceiro sem aprovacao.
- Referencias de imagem: volume separado `image_references`, contendo `references.json`; o JSON nao e um volume do Postgres. Migrar o arquivo atual apenas com copia controlada, checksum, backup e verificacao de permissao.
- Checkpoints: o exemplo nao inicia collectors; se forem autorizados no futuro, criar volumes persistentes distintos para `pacheco` e `offer_refresh`, mais lock/checkpoint, sem incluir workers no perfil default.
- Backup minimo: `pg_dump -Fc` criptografado para destino fora do VPS, copia/checksum do registro JSON e documentacao da versao da imagem/config. Definir retencao, RPO/RTO e alertas. Snapshot de VPS nao substitui backup logico do banco.
- Restauracao: restaurar em instancia isolada; verificar usuarios, favoritos, catalogo, ofertas, historico e referencias JSON antes de aceitar uma mudanca. Nao praticar restore sobre producao.
- Migracoes: Alembic. Fazer dump testado, revisar `alembic upgrade head` e executar explicitamente antes de subir a versao nova; nao ligar migracao destrutiva a entrypoint.
- Segredos: manter `.env.production` fora do Git, usar segredo aleatorio, restringir permissao; `.dockerignore` exclui `.env*` dos contextos backend e web, e remove do build backend os diretorios `data/` e `reports/` (volume de referencias deve ser migrado separadamente). `DATABASE_URL` requer senha URL-encoded e deve corresponder ao `POSTGRES_PASSWORD`. Rotacionar `JWT_SECRET` invalida tokens emitidos anteriormente.

## Deploy e rollback

O exemplo nao foi iniciado. Quando dominio/servidor forem aprovados, a sequencia e:

1. Criar staging sem dados pessoais/operacionais; provisionar DNS e firewall no plano aprovado.
2. Preparar `.env.production`, gerar `JWT_SECRET` forte, senha PostgreSQL e URL codificada; validar CORS e URL HTTPS do frontend.
3. Fazer backup e registrar checksums de configuracao e volumes; migrar dados apenas com autorizacao explicita.
4. Validar a configuracao sem subir servicos: `docker compose --env-file .env.production -f docker-compose.yml config`.
5. Subir somente `db`, aguardar `healthy`, rodar `docker compose --env-file .env.production -f docker-compose.yml run --rm --no-deps api alembic upgrade head` e, apos a migracao aprovada, iniciar `api`, `web` e `proxy`. Nao usar `up` global antes desse passo, pois a aplicacao de migracoes e manual.
6. Testar health/readiness, TLS, CORS, cadastro/login, busca, filtros, ofertas, favoritos, historico, paginacao, erros 401/5xx/timeouts, backup e restore isolado.
7. Build standalone Android apontando para a API HTTPS real; conferir URL no bundle e testar com Wi-Fi e rede movel fora da LAN.
8. Registrar metricas/alertas e procedimento de plantao. Workers continuam fora do Compose publico ate autorizacao e homologacao proprias.

Rollback: retirar DNS/rota publica ou reverter proxy para imagem/tag conhecida; manter API anterior ativa durante a transicao. Restaurar backup apenas em procedimento aprovado e validado, nunca sobrescrever o banco com dump sem conferir data e destino. Distribuir APK anterior somente com API HTTPS compativel ainda ativa. Rollback de schema requer migration reversa revisada ou restauracao controlada.

## Validacoes desta etapa

- Backend: pytest tests -q passou, 85 testes; Ruff em app, tests, migrations e scripts passou.
- Import da aplicação/modelos passou; foram registradas 29 rotas e 9 tabelas.
- Alembic: grafo válido com uma única head, c42a83d1710e. alembic check não foi executado por exigir conexão ao banco.
- Frontend: Jest passou (17 suites, 95 testes), TypeScript e ESLint passaram. Jest mostrou avisos conhecidos de act no teste de conectividade, sem falhas.
- Expo: exports Web e Android passaram com URL HTTPS reservada .invalid; isso não equivale a APK nem homologação Android funcional.
- Docker Compose: configuração estática de produção passou; serviços padrão locais foram db e api. Nenhum container foi iniciado.
- git diff --check passou; Git apenas avisou sobre conversão LF/CRLF em arquivos locais.
- Nenhum deploy, migração de banco ou coleta foi executado.

## Pendencias antes de publicacao

- Provedor, regiao, dominio real, titularidade de DNS, orcamento, backup externo e responsabilidade operacional.
- Tamanho atual do Postgres e volume JSON, teste de carga/conexoes, armazenamento e banda.
- Rate limiting/WAF e estrategia de monitoramento/alerta testados.
- Política de retencao e privacidade para dados de conta, logs e backups.
- Teste de backup/restore integral e plano de rotacao de segredos.
- Confirmar `nginx`, `caddy`, `node`, `postgres` e imagens Python por versao/digest antes de deploy e manter rotina de atualizacao.
- Dominios HTTPS reais para build final Android e CORS.

O projeto esta preparado com templates e checks de producao, nao publicado e ainda nao pronto para liberar em producao sem concluir os itens acima.
