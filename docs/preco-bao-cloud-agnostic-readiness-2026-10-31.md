# Preço Bão — prontidão cloud-agnostic

Data: 2026-10-31
Worktree: `C:\dev\farmacia-scraper-monorepo-ana`
Branch: `ana`

## Resultado

O repositório recebeu uma configuração de implantação preparada para Docker Compose em Linux, com PostgreSQL privado, API FastAPI, export estático Expo servido por Nginx e Caddy como único serviço de entrada. Nenhum provedor, domínio, credencial de produção ou custo foi escolhido ou criado. Nenhum container, banco, scraper, scheduler ou migração foi iniciado.

Isto é preparação e validação local de código/configuração, não homologação de uma instalação em nuvem nem autorização para publicar em produção. O teste de restauração e o teste de tráfego entre serviços permanecem pendentes porque dependem de um PostgreSQL/volume descartável; iniciar o Docker poderia afetar serviços e volumes locais que não foram inspecionados.

## Alterações desta revisão

- Adicionado rate limiting configurável para login (10/minuto), cadastro (5/hora) e consultas do catálogo, detalhes e histórico (120/minuto). A resposta de limite é HTTP 429 com `Retry-After`; erros não incluem IP, token ou corpo nos logs. CORS também é aplicado nas respostas 429.
- A chave do cliente usa o endereço de conexão ASGI. O proxy encaminhado só é confiável quando o pedido chega do IP de Caddy configurado no Compose. O contador é local ao processo e o Compose executa uma instância da API; não escalar horizontalmente sem estado compartilhado ou limitação compartilhada no edge.
- A configuração de produção exige segredo JWT não demonstrativo e CORS com origem HTTPS exata, rejeita `DEBUG=true` e mantém documentação OpenAPI desligada. O Compose usa `APP_DEBUG` como variável de entrada para evitar colisão com uma variável comum `DEBUG` do host.
- O Compose de produção mantém o banco sem portas publicadas, API e banco em rede privada, Web isolada, proxy como único ponto de entrada e sem scraper, scheduler ou migração automática. A imagem Caddy foi fixada em `2.10-alpine`, versão compatível com a diretiva de limite de corpo de requisição usada na configuração.
- Adicionado `preflight.sh` para inspecionar a configuração renderizada e validar serviço, portas, redes, domínios, URL HTTPS, CORS e configuração de produção sem construir imagens nem iniciar serviço.
- Adicionados `backup.sh` e `verify-backup.sh` para backup cifrado com GPG do PostgreSQL e do registro JSON de imagens, checksums e validação do fingerprint configurado da chave pública. O operador precisa definir `BACKUP_GPG_RECIPIENT` e `BACKUP_GPG_FINGERPRINT` depois de verificar o fingerprint por canal independente.
- O runbook de implantação documenta backup, restore isolado, segredos, preflight, atualização e rollback. O backup e a restauração não foram executados nesta revisão.

O limite de corpo do Caddy usa a diretiva oficial `request_body` com `max_size 2MB`; consulte a [documentação do Caddy](https://caddyserver.com/docs/caddyfile/directives/request_body). A sintaxe foi revisada, mas não foi validada por um binário Caddy nesta máquina.

## Validações executadas

- Backend: `pytest tests -q` — **89 passaram**. A suíte usa banco de teste isolado; nenhum banco principal foi acessado nesta etapa.
- Ruff: `ruff check app tests migrations scripts` — **passou sem apontamentos**.
- Frontend: Jest — **17 suites e 95 testes passaram**. Permaneceram avisos React `act(...)` conhecidos no teste de conectividade, sem falhas.
- TypeScript: `npx tsc --noEmit` — **passou**.
- ESLint: `npm run lint` — **passou**.
- Expo Web: `expo export --platform web` — **passou** com `https://api.example.invalid`; saída temporária removida.
- Expo Android: `expo export --platform android` — **passou** com a mesma URL reservada; isso gera bundle JavaScript e **não** é build de APK nem validação funcional Android. Saída temporária removida.
- Produção Compose: `docker compose --env-file env.example -f docker-compose.yml config --quiet` — **passou** sem contatar o daemon.
- Shell: `bash -n preflight.sh backup.sh verify-backup.sh` — **passou**.
- Preflight: **passou** usando arquivo temporário com domínio, credenciais e dados sintéticos; não construiu imagens nem iniciou serviços. O arquivo temporário foi removido.
- `git diff --check` — passou; Git informou apenas conversões LF/CRLF em arquivos locais preexistentes. A branch e o status foram conferidos ao fim.

## Limitações e pendências para publicar

1. Escolher servidor/provedor, domínio sob controle, DNS, firewall, orçamento e responsáveis. Nenhum serviço externo foi criado.
2. Preencher `.env.production` com credenciais novas e executar o preflight antes do primeiro deploy. Os valores `.invalid` são apenas exemplos e não funcionam como API real.
3. Homologar o Caddy e o TLS com domínio real, verificar CORS e fazer testes de fluxos pelo proxy, health/readiness e falhas de conexão.
4. Executar backup cifrado em ambiente autorizado e testar a restauração em PostgreSQL isolado com volume e projeto Compose exclusivos. O script e o procedimento foram revisados estaticamente; não há evidência de recuperação funcional até esse teste.
5. Conferir Alembic no banco de staging; `alembic check` e migração ao banco não foram executados. Migrações continuam comandos operacionais explícitos.
6. Antes de produção, definir monitoramento, alertas, política de logs/privacidade, retenção e cópia externa de backups. O rate limiter local não protege globalmente múltiplas réplicas nem substitui controles de borda.
7. Fixar imagens de runtime por digest e executar análise de vulnerabilidades/atualizações. As imagens de aplicação ainda precisam de validação contra o ambiente e ciclo de manutenção escolhidos.
8. O export Android não testa instalação, teclado, rede ou fluxos em dispositivo. APK final requer URL HTTPS real e validação em aparelho.

## Git e segurança operacional

Branch observada: `ana`. Não houve checkout, branch nova, merge, rebase ou commit. O worktree original `C:\dev\farmacia-scraper-monorepo` não foi editado. Não houve acesso ao daemon Docker, ao PostgreSQL principal, a serviços externos ou a scrapers. Todas as credenciais usadas no preflight foram sintéticas; o arquivo temporário foi removido.

Este relatório não marca o sistema como pronto para produção. Ele registra uma base cloud-agnostic e as verificações locais possíveis sem iniciar serviços ou tocar em dados existentes.
