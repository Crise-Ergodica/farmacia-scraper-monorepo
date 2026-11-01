# Preço Bão — guia de implantação futura

Este runbook prepara uma implantação Linux com Docker Compose, mas não publica o sistema. Ainda faltam provedor, servidor, domínio próprio, DNS, segredos de produção e decisão de migração dos dados. Os exemplos `*.example.invalid` são reservados e não devem ser usados para subir os serviços.

## Arquitetura preparada

```text
Web / Android ── HTTPS ── Caddy ──┬── Expo Web estático
                                  └── FastAPI ── rede privada ── PostgreSQL
```

O Compose de `deploy/production` inclui apenas PostgreSQL, API, Web e Caddy. O PostgreSQL não publica porta no host. Caddy é o único serviço com portas 80/443. API e Web ficam em redes separadas com o proxy; o FastAPI confia somente no IP configurado para Caddy na rede `api_edge`. Nenhum scraper, scheduler ou migração automática é iniciado no `up` padrão.

O exemplo de capacidade para orçamento é 2 vCPU, 8 GB RAM e 100 GB SSD, apenas estimativa inicial a validar com medição real. Linux x86_64 mantido pelo provedor, Docker Engine e Docker Compose v2 são necessários. Se a sub-rede `172.28.240.0/24` conflitar com VPN, rede local do host ou outra rede Docker, altere em conjunto `API_PROXY_SUBNET` e `API_PROXY_IP` no `.env.production` e mantenha o IP confiável coincidente.

### Protecao de endpoints

A API aplica janelas fixas por IP obtido de request.client; em producao, Uvicorn so aceita os cabecalhos encaminhados pelo IP de proxy configurado. Os limites iniciais sao login 10/min, cadastro 5/h e consultas de catalogo, detalhes e historico 120/min. Sao configuraveis pelo ambiente. O excesso retorna HTTP 429 com Retry-After; o log registra apenas a politica, sem IP, token ou corpo.

O contador e limitado em memoria para o unico processo API deste Compose. Nao escale horizontalmente ate trocar o contador por estado compartilhado ou rate limiting no edge com estado compartilhado. Reiniciar a instancia zera as janelas. O rate limit nao substitui WAF/edge protection contra ataques distribuidos; configure essa protecao antes de expor o servico. Nao ha endpoint de recuperacao de senha.

## Configurar sem iniciar serviços

1. Escolha e configure um servidor e um domínio sob seu controle. Crie DNS para `APP_DOMAIN` e `API_DOMAIN` apontando para o servidor. O Caddy precisa receber conexões públicas nas portas 80 e 443 para emitir/renovar certificados ACME; não abra essas portas antes da decisão de publicar.
2. Copie `deploy/production/env.example` para `.env.production`, fora do Git. Troque todo placeholder: `APP_DOMAIN`, `API_DOMAIN`, `EXPO_PUBLIC_API_URL`, `BACKEND_CORS_ORIGINS`, usuário/senha PostgreSQL e `JWT_SECRET`. A senha de banco deve ser URL-safe para corresponder ao `DATABASE_URL`; se usar outros caracteres, codifique-os na URL. Gere o JWT com `python -c "import secrets; print(secrets.token_urlsafe(48))"` e não reutilize o segredo local.
3. Configure `BACKEND_CORS_ORIGINS` somente com a origem HTTPS exata do Web. Android nativo não usa CORS. A URL `EXPO_PUBLIC_API_URL` é pública e entra no bundle; nunca inclua credenciais nela.
4. Valide a configuração sem iniciar containers:

   ```sh
   cd deploy/production
   docker compose --env-file .env.production config --quiet
   ```

   Revise a configuracao sem expor valores secretos. Execute `bash ./preflight.sh` nessa pasta para validar servicos, portas, redes, dominios, CORS e segredos; o script nao constroi imagens nem inicia servicos. Somente o proxy pode publicar 80/443.

## Migração e inicialização controlada

Antes de usar dados reais, determine o banco destino e confirme titularidade, versão Alembic, permissões e compatibilidade. Não reutilize volumes locais por engano. Use primeiro staging isolado e dados sintéticos.

1. Faça e confira o backup conforme a seção abaixo.
2. Suba somente o banco no ambiente aprovado: `docker compose --env-file .env.production up -d db`; aguarde `healthy`.
3. Registre a revisão existente em destino e revise as migrações pendentes. Aplique migrações somente por comando operacional explícito, após o backup:

   ```sh
   docker compose --env-file .env.production run --rm --no-deps api alembic current
   docker compose --env-file .env.production run --rm --no-deps api alembic upgrade head
   ```

   Não use `alembic stamp` para contornar divergência. Para `c42a83d1710e`, preserve o histórico e não execute downgrade sem plano de dados aprovado.
4. Inicie API, Web e proxy somente após a migração aprovada: `docker compose --env-file .env.production up -d api web proxy`. Isso publica o proxy e exige DNS/domínio real corretamente configurados.
5. Confirme `https://API_DOMAIN/health/live`, `/health/ready`, o frontend, cadastro/login, pesquisa, filtros, detalhes, favoritos e histórico. Teste os erros esperados e confira logs sem expor tokens ou dados pessoais.

## Backup e restauracao

O backup cobre PostgreSQL e o registro JSON de referencias de imagem, criptografados com GnuPG para uma chave publica do operador. Nao guarda senhas ou chaves privadas no repositorio. Instale GnuPG, importe a chave publica do responsavel e confira sua impressao digital por canal independente antes do primeiro backup.

Defina `PRECO_BAO_ENV_FILE`, `BACKUP_DIR`, `BACKUP_GPG_RECIPIENT` (email ou key ID) e `BACKUP_GPG_FINGERPRINT` (fingerprint completo conferido por outro canal):

    bash ./backup.sh
    bash ./verify-backup.sh "$BACKUP_DIR/preco-bao-AAAAMMDDTHHMMSSZ"

O backup cria diretorio privado com timestamp, revisao Git, arquivos cifrados e checksums. O comando nao inicia containers; falha se db/api nao estiverem ja disponiveis. A verificacao valida checksum, o formato custom do pg_dump e o JSON depois de descriptografar em memoria. Retencao e copia externa criptografada devem ser definidas pelo operador; o script nao apaga backups antigos.

A restauracao funcional nao foi homologada nesta etapa porque isso exigiria um PostgreSQL e volume descartaveis; nao e seguro iniciar o Docker sem confirmar o estado dos containers existentes. Quando houver homologacao autorizada, use projeto/rede/volume e credenciais exclusivos, crie banco vazio preco-bao-restore-test, descriptografe o dump e execute pg_restore sem --clean. Confira usuarios e favoritos sinteticos, catalogo, ofertas, historico, integridade das relacoes e referencias JSON. Nunca restaure sobre o banco principal. Repita restore em instancia isolada e registre os totais antes de marcar o backup como recuperavel.

## Web e Android

O `frontend/Dockerfile.web` cria o export estático Expo e o Nginx faz fallback de rotas para `index.html`, além de cache longo para assets com hash e revalidação do HTML. O build exige `EXPO_PUBLIC_API_URL` HTTPS. A API do Android é incorporada no APK durante o build: aguarde o domínio real e o certificado HTTPS válidos, depois configure `EXPO_PUBLIC_API_URL=https://<API_DOMAIN>` e `-PstandaloneApiMode=https`. Não produza APK final com domínio `.invalid`, localhost ou HTTP de LAN. Distribuir o app exige assinatura e decisão de canal próprias.

## Atualização e rollback

Use tags imutáveis de imagem/revisões identificadas; valide Compose antes de baixar e iniciar. Faça backup, atualize primeiro staging, aplique migrações compatíveis de forma explícita, faça rollout da aplicação e verifique readiness. Em falha, volte a imagem anterior sem reverter automaticamente o schema. Restaure dados somente em procedimento aprovado, depois de confirmar o destino e a data do backup. Mantenha o Caddy com os volumes `caddy_data` e `caddy_config` para preservar certificados.

## Coletores e serviços de manutenção

O Compose de produção não contém Indiana, Araújo, Pacheco, manutenção de imagens ou scheduler. A configuração local mantém essas operações fora do perfil padrão; serviços Pacheco e atualização de ofertas não reiniciam automaticamente. Não habilite perfil de scraper durante deploy, reinício do host ou inicialização do banco. Coletas futuras exigem comando operacional e autorização separados.

## Checklist antes de publicar

- [ ] Provedor, região, orçamento, responsável operacional e domínio aprovados.
- [ ] DNS e firewall revisados; somente o proxy recebe tráfego externo.
- [ ] `.env.production` criado com segredos únicos fora do Git; CORS contém somente a origem Web aprovada.
- [ ] Redes sem conflito, PostgreSQL sem porta publicada, volumes persistentes e disco monitorado.
- [ ] Backup externo criptografado e teste de restauração isolada concluído.
- [ ] Revisões Alembic conferidas e migração aprovada em staging.
- [ ] Rate limit por instancia verificado; estado compartilhado ou edge limit aprovado antes de escalar; WAF, alertas, logs e privacidade revisados.
- [ ] DNS real, HTTPS válido, health checks, cadastro/login, busca, favoritos, perfil e histórico verificados.
- [ ] Scrapers permanecem desligados e ausentes do deploy padrão.
- [ ] APK HTTPS compilado com a API real e homologado em dispositivo fora da LAN.
- [ ] Plano de rollback de aplicação e recuperação de dados revisado.
