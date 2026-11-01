# Preço Bão — conectividade Android ↔ FastAPI na LAN

Data: 25/10/2026 · Worktree `C:\dev\farmacia-scraper-monorepo-ana` · Branch `ana`

## Diagnóstico

| Item | Evidência |
|---|---|
| Host/API | Docker `farmacia_api`, imagem `backend-api`, processo `uvicorn app.main:app --host 0.0.0.0 --port 8000`; PID local do proxy Docker 8372. |
| Postgres | Container `farmacia_postgres`, `pg_isready` confirmou conexão; health `healthy`; API usa host `db`, base `farmacia_db`. |
| Porta publicada | Docker publica `0.0.0.0:8000` e `:::8000`; `restart=always`. Não há listener na porta 8001. |
| IP do PC | `192.168.2.110/24`, adaptador ativo Ethernet 5 (Realtek), gateway `192.168.2.1`, perfil Windows `Private`. O endereço tem origem DHCP. |
| Xiaomi | ADB `7e2009a6`, modelo `23021RAAEG`, Android 15/API 35; interface Wi-Fi `192.168.2.109/24`, mesma sub-rede do computador. |
| URL no APK anterior | A última build foi produzida com `EXPO_PUBLIC_API_URL=http://192.168.2.110:8001`. O bundle Android tinha essa URL. |

### Causa confirmada

O APK anterior apontava para a porta 8001, mas não existia processo/listener nessa porta. O serviço efetivamente publicado pelo Docker é 8000. Do computador, `127.0.0.1:8000` e `192.168.2.110:8000` responderam; no Xiaomi, `toybox nc` conectou a `192.168.2.110:8000` e expirou em `:8001`. Assim, o timeout anterior era causado pela porta incorreta no bundle. O teste TCP do próprio Xiaomi na 8000 também mostra que o aparelho alcança a LAN e que a porta não está bloqueada para esse cliente; não foi necessária nova regra de firewall.

Testes HTTP feitos do PC, todos `200`:

| URL | Tempo observado | Dados |
|---|---:|---|
| `http://127.0.0.1:8000/openapi.json` | 341 ms | OpenAPI respondeu. |
| `http://127.0.0.1:8000/catalogo?limit=1&offset=0` | 268 ms | 1 item retornado, total 13.103. |
| `http://127.0.0.1:8000/catalogo/farmacias` | 36 ms | 3 farmácias. |
| `http://192.168.2.110:8000/openapi.json` | 49 ms | OpenAPI respondeu pelo IP LAN. |
| `http://192.168.2.110:8000/catalogo?limit=1&offset=0` | 49 ms | 1 item retornado, total 13.103. |
| `http://192.168.2.110:8000/catalogo/farmacias` | 25 ms | Araújo, Indiana e Pacheco. |

Porta 8001 recusou conexão local e não tinha listener. No Xiaomi, TCP 8000 retornou sucesso; TCP 8001 terminou em timeout.

## Correção e configuração

Não alterei backend, contratos, PostgreSQL, preços, imagens, rede ou firewall. A porta 8000 já estava publicada corretamente no container; alterar o Compose não corrigiria a URL já incorporada ao APK. A configuração do app não tem IP fixo no código: a variante standalone lê `EXPO_PUBLIC_API_URL` no momento do bundle e o Gradle valida modo LAN, endereço IPv4 privado, HTTP explícito e a variável de permissão LAN.

Build feita com:

```powershell
$env:EXPO_PUBLIC_API_URL = 'http://192.168.2.110:8000'
$env:EXPO_PUBLIC_ALLOW_INSECURE_LAN_API = 'true'
$env:NODE_ENV = 'production'
cd frontend/android
.\gradlew.bat :app:assembleStandalone --no-daemon --max-workers=4 -PreactNativeArchitectures=arm64-v8a -PstandaloneApiMode=lan
```

O bundle da build contém `http://192.168.2.110:8000` e não contém `192.168.2.110:8001`. A assinatura APK v2 é válida. Para contornar o bug de linker do NDK com o caminho acentuado `C:\Users\Usuário`, o SDK foi mapeado temporariamente para `Q:`; o `local.properties` original foi restaurado e a unidade removida após a build.

Para iniciar os containers existentes sem executar schedulers/workers ou depender da interpolação de `.env` do Compose nesta worktree:

```powershell
docker start farmacia_postgres
# aguarde: docker inspect --format '{{.State.Health.Status}}' farmacia_postgres
docker start farmacia_api
```

Os containers têm política `restart=always`; depois que o Docker Desktop estiver ativo, eles reiniciam com as portas configuradas. Não reiniciei os serviços compartilhados durante a auditoria. `docker compose -f backend/docker-compose.yml ps` nesta worktree não consegue interpolar a configuração porque não há `backend/.env`; não expus nem copiei segredos de outra worktree. Os containers existentes continuam ativos e servindo a API.

Não foi criada regra de firewall nem desligado o Firewall do Windows. A tentativa anterior de regra temporária para 8001 havia sido recusada por permissão. O teste atual na porta 8000 passou do Xiaomi, portanto não há evidência que justifique pedir uma nova regra.

## Persistência de endereço após reinício

O PC recebe `192.168.2.110` por DHCP. `DESKTOP-BAIMUCL` e `DESKTOP-BAIMUCL.local` não resolveram no Xiaomi, então não há hostname LAN validado para usar no APK. A conexão agora pode funcionar com o IP atual e o Docker tem reinício configurado, mas não posso garantir que o IP sobreviva a expiração/troca de lease do roteador. Para estabilidade permanente após reboot do roteador ou mudança de lease é necessária uma reserva DHCP no roteador para o MAC do adaptador (`D8-43-AE-6E-83-07`) ou um nome DNS local resolvível pelo Xiaomi. Não alterei essas configurações administrativas. Se o IP mudar, confirme o novo IPv4 e gere nova build com `EXPO_PUBLIC_API_URL` atualizado.

## APK e homologacao no Xiaomi

- APK: `frontend/android/app/build/outputs/apk/standalone/app-standalone.apk`.
- Package: `com.dragoniana.precobao.standalone`; versao `1.0.0-internal`, versionCode 1, ABI arm64-v8a.
- SHA-256: `D4316BADB60C16AF7D4CB578106D740EE4EBB1E1D80545C13AF65CD01023AC39`.
- Build standalone Gradle concluido; assinatura v2 verificada. O bundle contem `http://192.168.2.110:8000` e nao contem a porta 8001.
- A primeira tentativa de `adb install -r` foi cancelada no aparelho. Apos o usuario desbloquear e confirmar, a instalacao de atualizacao terminou com `Success`; os dados do app nao foram apagados.
- O app instalado foi aberto diretamente pelo Android, sem Metro. A Home carregou 13.103 medicamentos, as tres farmacias e imagens de produtos.
- Busca por "paracetamol" retornou 140 medicamentos. Selecionar Pacheco aplicou `farmacia_id=4` e exibiu 84 resultados.
- Detalhes do Torsilax (medicamento ID 34) carregaram duas ofertas, Indiana e Pacheco. A tela de historico exibiu o menor preco e os precos das duas farmacias.
- Logs do FastAPI confirmam chamadas do app via Docker (`172.18.0.1`) para `/catalogo`, `/catalogo/farmacias`, busca com `termo_busca=paracetamol`, filtro `farmacia_id=4`, `/catalogo/medicamentos/34` e `/api/v1/medicines/34/history?periodo=all`; todas responderam `200 OK`.
- O Wi-Fi do telefone foi temporariamente desativado e restaurado em seguida. Durante essa janela o app mostrou conteudo previamente carregado; nao foi possivel confirmar uma mensagem de falha nem exercitar com sucesso o botao de retry. Nao houve escrita ou perda de dados. A reconexao Wi-Fi e o catalogo voltaram a funcionar.
- A retomada sem Metro esta verificada pelo lancamento standalone apos force-stop. Login, cadastro, favoritos autenticados e alteracao de perfil nao foram exercitados nesta homologacao.

Capturas e hierarquias Android desta execucao estao em [`medicine-image-audit-2026-10-25`](medicine-image-audit-2026-10-25/): `xiaomi-home-api-8000.png`, `xiaomi-catalog-api-8000.png`, `xiaomi-search-paracetamol.png`, `xiaomi-filter-pacheco.png`, `xiaomi-filter-panel.png`, `xiaomi-detail-api-8000.png`, `xiaomi-detail-bottom-api-8000.png`, `xiaomi-history-api-8000.png`, `xiaomi-offline-state.png` e `xiaomi-offline-retry.png`.

## Testes automatizados e exports

- Jest: 17 suítes, 92 testes passaram. Foram adicionados dois testes de retry do Home (timeout do catálogo e erro da lista de farmácias). O renderer React Native emite avisos de ambiente `act` na nova integração; sem falhas de teste.
- TypeScript: `npx tsc --noEmit` passou.
- ESLint: `npm run lint` passou sem avisos após substituir os imports dinâmicos do teste por `jest.requireActual`.
- `npx expo install --check`: dependências atualizadas.
- Expo Doctor: 19/20. Único aviso existente: propriedades nativas em `app.json` coexistem com diretórios nativos em projeto não-CNG; não é causa do timeout.
- Expo export `--platform all`: Web, Android Hermes e iOS concluídos em diretório temporário.
- Gradle `assembleStandalone`: passou; APK v2 válida, package conferido, URL LAN 8000 presente no bundle e 8001 ausente.
- Backend não teve alterações nesta etapa; `pytest` 78 passou e Ruff sem apontamentos foram executados novamente.
- `git diff --check`: concluído sem erros; apenas avisos Git de conversão LF/CRLF em arquivos que já estavam modificados.

## Evidencias e pendencias

A causa original foi corrigida no APK desta worktree ao apontar para o servico ja disponivel em `192.168.2.110:8000`. O teste real no Xiaomi comprovou catalogo, farmacias, busca, filtro por farmacia, detalhe e historico com HTTP 200 no backend. A versao antiga no Xiaomi havia apontado para 8001, sem servico escutando nessa porta.

Permanecem pendentes os fluxos autenticados (login/cadastro/favoritos/perfil) e a validacao visual de uma falha de rede com acao de retry. A interrupcao temporaria de Wi-Fi deixou o conteudo anterior visivel e nao produziu uma mensagem de falha observavel; por isso o retry nao esta marcado como validado. A estabilidade do IP apos expiracao/troca de lease DHCP requer uma reserva no roteador ou DNS local administravel; nao alterei configuracoes de rede.

Nenhum worker foi iniciado, nenhum container compartilhado foi reiniciado, nenhuma regra de firewall foi criada, nenhum dado foi apagado e nenhuma alteracao foi feita na outra worktree. Sem commit.
