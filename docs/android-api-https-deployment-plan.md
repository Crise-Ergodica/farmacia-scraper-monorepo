# Preço Bão — plano para disponibilizar a API Android por HTTPS

**Status:** preparação apenas. Nenhum domínio foi registrado, serviço contratado, porta aberta ou endpoint publicado. Ainda não existe um endpoint HTTPS externo aprovado para o aplicativo.

## 1. Auditoria do estado atual

Na worktree `ana`, a rede local do computador apresenta `192.168.2.110`. No momento da auditoria, `farmacia_api` estava ativo e publicava `0.0.0.0:8000`; `farmacia_postgres` estava saudável e publicava `0.0.0.0:4242`. A consulta local a `/catalogo?limit=1&offset=0` retornou `total=13103`. Isso é um estado observado em 25/10/2026, não uma URL ou contagem estável para builds futuras. Os workers e `farmacia_tunnel` não estavam em execução.

O Compose de desenvolvimento publica também a porta do PostgreSQL no host para permitir conexões locais. Não encaminhar as portas 8000 ou 4242 no roteador nem abrir regras de entrada externas para essa configuração.

O serviço `tunnel` existente executa `cloudflared tunnel --url http://api:8000`. Esse comando cria um Quick Tunnel com URL temporária; ele não configura domínio próprio nem autenticação de aplicação. O serviço foi colocado no perfil Compose explícito `quick-tunnel` para não iniciar junto com o `docker compose up` comum. **Não ativar esse perfil para disponibilizar a API do produto.** Quick Tunnels e rotas públicas tornam o serviço acessível por uma URL pública; o próprio Cloudflare descreve o uso de uma rota de aplicação publicada para expor um hostname [na documentação de Cloudflare Tunnel](https://developers.cloudflare.com/tunnel/get-started/).

### Superfície da API identificada

- `POST /auth/register`, `POST /auth/jwt/login`, `GET/PATCH /users/me`.
- Catálogo e metadados: `GET /catalogo`, `/catalogo/farmacias`, `/catalogo/filtros/opcoes`, `/catalogo/mais-baratos`, `/catalogo/medicamentos/{id}`.
- Favoritos autenticados: `/users/me/favoritos/medicamentos`, `/users/me/favoritos/farmacias` (GET/POST/DELETE por recurso).
- Histórico: `GET /api/v1/medicines/{id}/history`.
- Imagens: URLs externas HTTPS das ofertas/registro; a rota legada `/catalogo/medicamentos/{id}/imagem` redireciona para uma URL de imagem.

FastAPI usa JWT assinado pelo `JWT_SECRET`, com validade configurada de uma hora. O backend inicia sem o segredo. O middleware CORS usa uma lista configurável e, na configuração atual, aceita também origens localhost/127.0.0.1 para desenvolvimento; CORS não autentica clientes Android e não substitui autorização.

Não foi localizada implementação de rate limiting na aplicação. O `GET /` responde uma mensagem de saudação; não há neste momento health check separado que valide dependências. O container do backend executa `uvicorn app.main:app --host 0.0.0.0 --port 8000`. O PostgreSQL não deve aceitar tráfego da Internet.

## 2. Arquitetura recomendada

```text
Aplicativo Android ── HTTPS :443 ──> DNS api.<domínio do proprietário>
                                        │
                                 Proxy TLS (Caddy)
                                        │ rede privada de containers
                                    FastAPI :8000
                                        │ rede privada
                                  PostgreSQL :5432
```

Para um serviço acessível fora de casa, a opção recomendada é hospedar proxy, API e banco numa VM/VPS com endereço estável ou utilizar uma plataforma com ingresso HTTPS estável e rede privada entre serviços. A escolha depende de orçamento, região, disponibilidade, backups e responsabilidade operacional; nenhum provedor foi escolhido ou contratado.

Caddy é uma opção simples para terminar TLS e manter certificados automaticamente. A emissão ACME pública normalmente exige DNS e que o servidor seja alcançável nas portas 80/443, conforme [o guia HTTPS do Caddy](https://caddyserver.com/docs/quick-starts/https) e [a documentação de HTTPS automático](https://caddyserver.com/docs/automatic-https). Se a infraestrutura não puder receber conexões nessas portas, avaliar ingresso HTTPS gerenciado por uma plataforma ou um túnel nomeado, autenticado e configurado com o domínio do proprietário. Isso ainda é publicação externa e requer autorização explícita.

Uma instalação doméstica com Caddy exigiria IP público estável ou DDNS e encaminhamento de 80/443 no roteador. CGNAT pode impedir conexões de entrada; não contornar essa limitação sem escolher uma alternativa autorizada. O endpoint doméstico também dependeria de energia, conexão e manutenção do computador. Não é recomendado como primeira produção.

## 3. Proteções antes de qualquer publicação

1. **Rede e containers:** somente o proxy publica 80/443. FastAPI fica em rede privada e sem porta do host na configuração de produção. PostgreSQL não tem `ports`; somente API e tarefas internas o alcançam. Usar um override de produção, mantendo a configuração local `8000`/`4242` para desenvolvimento.
2. **TLS:** certificado público válido, renovação monitorada, TLS moderno e redirecionamento HTTP→HTTPS no proxy. Nunca instalar certificados autoassinados no APK de distribuição nem desativar validação TLS.
3. **Proxy confiável:** a aplicação deve confiar em `X-Forwarded-*` apenas quando recebidos do proxy/rede conhecida. O FastAPI/Uvicorn documenta essa configuração com uma lista de IPs confiáveis [em HTTPS atrás de proxy](https://fastapi.tiangolo.com/deployment/https/). Não usar `--forwarded-allow-ips="*"` enquanto a porta da API puder ser alcançada diretamente.
4. **Autenticação:** manter JWT e autorização por usuário. Não colocar JWT, senha de banco, `JWT_SECRET`, token de Cloudflare ou segredo de serviço no app. Guardar segredos no gerenciador de segredos do host/CI; rotacionar `JWT_SECRET` exige considerar que sessões existentes deixarão de validar.
5. **Limites e abuso:** adicionar rate limiting no edge e/ou API para login, cadastro e endpoints caros; definir limite de corpo, concorrência e timeout. Retornar erros controlados. O limite precisa ser medido com tráfego real para não bloquear pesquisa legítima.
6. **CORS:** configurar somente as origens exatas da Web hospedada. Não usar `*` com credenciais. Manter a política de desenvolvimento separada. Clientes nativos não dependem de CORS.
7. **Documentação e saúde:** em produção, desabilitar `/docs`, `/redoc` e `/openapi.json` ou restringi-los; definir `/health/live` e `/health/ready` sem informação sensível, com readiness verificando a conexão do banco.
8. **Logs:** retenção e rotação, IDs de requisição e alertas; mascarar `Authorization`, senha, JWT, query de login e dados pessoais. Evitar armazenar corpos de requisição.
9. **Backups:** dumps criptografados, cópia fora do host, retenção definida e simulação periódica de restauração. Testar backup/restore antes de migrar; monitorar espaço e conexões do PostgreSQL.

## 4. Ambientes e builds Android

| Ambiente | URL/configuração | Variante e transporte |
|---|---|---|
| Web/Android desenvolvimento | Configurada localmente; Expo pode resolver host do Metro para o dispositivo | `debug`, apenas desenvolvimento |
| Standalone LAN | `EXPO_PUBLIC_API_URL=http://<IPv4-privado>:8000`, `EXPO_PUBLIC_ALLOW_INSECURE_LAN_API=true`, `-PstandaloneApiMode=lan` | Package `.standalone`, cleartext permitido só nessa variante deliberada |
| Standalone HTTPS interno | `EXPO_PUBLIC_API_URL=https://api.<domínio-real>`, sem flag HTTP | Package `.standalone`, cleartext desativado |
| Produção futura | Endpoint HTTPS aprovado; assinatura e identificador de produção próprios | Exige decisão de distribuição e chave privada fora do Git |

O Gradle agora valida a configuração standalone antes de empacotar: exige URL, rejeita loopback, credenciais, query e fragmento; o modo HTTPS exige `https`; o modo LAN exige IPv4 privado, HTTP e a flag explícita. O resolver JavaScript também rejeita URL com credenciais/query/fragmento e não aceita localhost/HTTP em build nativo sem configuração LAN. Não use `10.0.2.2` para um aparelho físico.

Build local LAN (PowerShell, depois de definir o IP real):

```powershell
$env:EXPO_PUBLIC_API_URL = 'http://192.168.x.y:8000'
$env:EXPO_PUBLIC_ALLOW_INSECURE_LAN_API = 'true'
$env:NODE_ENV = 'production'
cd frontend/android
.\gradlew.bat :app:assembleStandalone --no-daemon -PstandaloneApiMode=lan -PreactNativeArchitectures=arm64-v8a
```

Build local HTTPS:

```powershell
$env:EXPO_PUBLIC_API_URL = 'https://api.dominio-aprovado.example'
Remove-Item Env:EXPO_PUBLIC_ALLOW_INSECURE_LAN_API -ErrorAction SilentlyContinue
$env:NODE_ENV = 'production'
cd frontend/android
.\gradlew.bat :app:assembleStandalone --no-daemon -PstandaloneApiMode=https -PreactNativeArchitectures=arm64-v8a
```

Os endereços acima são exemplos de configuração. Não gravar IP de rede nem domínio fictício no código. `EXPO_PUBLIC_*` fica visível no bundle, portanto só deve conter URL pública da API e opções não secretas.

## 5. Sequência proposta de implantação (aguarda decisões/autorização)

1. Escolher provedor/host, região, domínio e custo mensal; confirmar responsabilidade por atualizações e plantão.
2. Criar ambiente de staging isolado, credenciais separadas e cópia de dados sanitizada/sintética. Não copiar produção sem plano de proteção.
3. Provisionar DNS e proxy HTTPS; permitir entrada somente em 80/443 onde necessário e tráfego interno mínimo. Não expor PostgreSQL.
4. Configurar segredos no host, `BACKEND_CORS_ORIGINS` exata, proxy trusted IP, limites, logs sanitizados, backup e monitoramento.
5. Testar TLS e cadeia do certificado; health checks, login/cadastro em conta descartável de staging, pesquisa, filtro, favorito, histórico, erros 401/429/5xx, timeouts e recuperação.
6. Compilar APK standalone HTTPS com `standaloneApiMode=https`; verificar bundle, certificado TLS, package/version e assinatura. Homologar em Wi-Fi externo e dados móveis autorizados.
7. Migrar somente após backup e validação; manter a API LAN anterior até confirmar staging/produção. Fazer rollout gradual.

### Rollback

Desabilitar o route/hostname público ou reverter o proxy para a revisão estável; não reverter schema sem confirmar compatibilidade. Manter snapshots e dumps testados. Para rollback de app, distribuir o APK anterior com versionCode compatível ou um build com API HTTPS anterior ainda ativo. Nunca fazer downgrade com `adb` que exija remoção de dados.

## 6. O que requer decisão e autorização

- Domínio/subdomínio de propriedade do usuário e acesso DNS.
- Provedor e orçamento de hospedagem, banco/armazenamento e backup.
- Publicar hostname e abrir firewall/portas (ou habilitar túnel nomeado).
- Origem Web oficial para CORS.
- Política de retenção de logs e backups e tratamento de dados de usuários.
- Chave de assinatura definitiva, package ID de produção e canal de distribuição.

Até essas decisões, o serviço permanece LAN. Não se deve testar acesso externo chamando uma URL inventada ou Quick Tunnel temporário. Esta etapa não alterou backend nem banco e não iniciou scrapers.
