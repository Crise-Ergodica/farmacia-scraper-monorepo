# Preço Bão — APK Android standalone (25/10/2026)

## Resultado

Foi gerada e instalada no Xiaomi uma build interna com o bundle JavaScript incorporado. O APK abre sem Metro; para catálogo, autenticação, favoritos e histórico, continua dependendo da API FastAPI na mesma rede local.

- Branch: `ana` (sem commit).
- APK: `frontend/android/app/build/outputs/apk/standalone/app-standalone.apk`.
- Package: `com.dragoniana.precobao.standalone`.
- Versão: `1.0.0-internal`, versionCode `1`, minSdk `24`, targetSdk `36`.
- ABI compilada: `arm64-v8a` (compatível com o Xiaomi conectado).
- Tamanho: 40.818.937 bytes (aprox. 38,9 MiB).
- SHA-256: `9C535813D20FA37C62E5B371A360F463C0B2D65E0E561D90A5C4ADF7D1C5322A`.
- Assinatura verificada: APK Signature Scheme v2, chave Android Debug de teste; SHA-256 do certificado `fac61745dc0903786fb9ede62a962b399f7348f0bb6f899b8332667591033b9c`.

O bundle contém o endereço definido durante o build (`http://192.168.2.110:8000`) e os recursos locais. A URL é configuração pública do app, não contém credenciais. O APK não foi adicionado ao Git.

## Build e configuração

Foi usada a opção A: variante Gradle `standalone`, baseada no release, não depurável, com applicationId sufixado por `.standalone`, nome “Preço Bão (Teste)” e manifesto de HTTP claro restrito a essa variante interna. Isso preserva a instalação normal `com.dragoniana.precobao` e evita alterar as regras de rede das outras variantes.

O teste local exigiu apontar temporariamente `frontend/android/local.properties` para o SDK por uma unidade mapeada, pois o caminho do SDK sob `C:\Users\Usuário` é corrompido pelo clang/NDK durante o teste do linker. O caminho original escapado foi restaurado ao final; a unidade temporária foi desmontada. `local.properties` é ignorado pelo Git.

Para reconstruir em outra LAN, defina antes do Gradle:

```powershell
$env:EXPO_PUBLIC_API_URL = 'http://IP_PRIVADO_DO_SERVIDOR:8000'
$env:EXPO_PUBLIC_ALLOW_INSECURE_LAN_API = 'true'
$env:NODE_ENV = 'production'
cd frontend/android
.\gradlew.bat :app:assembleStandalone --no-daemon --max-workers=4 -PreactNativeArchitectures=arm64-v8a
```

O endereço precisa ser acessível pelo telefone e o FastAPI precisa permitir o tráfego LAN. Não use `localhost`, `127.0.0.1` nem `10.0.2.2` no telefone físico. Fora dessa rede, é necessário configurar um endpoint HTTPS estável e seguro e gerar uma nova build. A exceção HTTP existe somente para a variante de teste.

## Validações técnicas

| Verificação | Resultado |
|---|---|
| Jest completo | Passou: 16 suítes, 88 testes |
| TypeScript (`npx tsc --noEmit`) | Passou |
| ESLint (`npm run lint`) | Passou |
| `expo install --check` | Passou; dependências atualizadas |
| Expo Doctor | 19/20. Aviso conhecido: `app.json` contém propriedades nativas enquanto `android/ios` existem; EAS não sincronizaria esses campos. Não foi executado prebuild clean nem removidos diretórios nativos. |
| Export Web | Passou |
| Export Android | Passou; bundle Hermes de aproximadamente 5,9 MB |
| Gradle `assembleStandalone` | Passou após mapear o SDK para contornar o caminho acentuado |
| `apksigner verify` | Passou, assinatura v2 válida |
| `git diff --check` | Passou; Git emitiu somente avisos de conversão LF/CRLF |

## Instalação e teste no Xiaomi

O APK foi instalado como `com.dragoniana.precobao.standalone`, sem desinstalar, limpar dados ou substituir `com.dragoniana.precobao`. A instalação de desenvolvimento manteve os horários: primeira instalação `2026-10-24 18:59:32`, última atualização `2026-10-25 16:54:20`. A build standalone foi posteriormente atualizada com `adb install -r`, sem limpeza de dados.

No primeiro APK, desliguei o Metro da porta 8081 e removi o `adb reverse tcp:8081`. Forcei o encerramento apenas da variante standalone e a abri pelo launcher. A interface inicializou, entrou como convidado, carregou o catálogo real pela LAN, abriu detalhes e exibiu o painel de filtros. A captura mostrou 13.103 itens retornados pela API e o detalhe do Mounjaro. Isso comprova inicialização e navegação sem Metro; o backend e o PostgreSQL permaneceram ativos. Os workers de scraping não foram iniciados.

Capturas válidas desse teste:

- [Home e catálogo](visual/android-standalone-2026-10-25/after-guest.png)
- [Detalhe do medicamento](visual/android-standalone-2026-10-25/detail.png)
- [Painel de filtros](visual/android-standalone-2026-10-25/filters.png)
- [Erro de rede e ação “Tentar novamente”](visual/android-standalone-2026-10-25/airplane.png)
- [Catálogo após restaurar a conexão](visual/android-standalone-2026-10-25/retry.png)

Com modo avião ativo, a tela não mostrou medicamentos/preços como atuais, indicou que não conseguiu carregar e ofereceu “Tentar novamente”. Ao restaurar a rede e tocar nessa ação, o catálogo carregou novamente. Esse teste foi feito antes da última atualização da variante.

Na rodada seguinte, o estado de tela bloqueada do aparelho impediu novas capturas úteis após atualizar o APK. A instalação atualizada foi aceita e a Activity foi iniciada por ADB, mas as capturas ficaram pretas enquanto o aparelho estava bloqueado. Por isso, a atualização de retry descrita abaixo ainda precisa de uma confirmação visual após desbloquear o Xiaomi.

O aparelho estava com fonte/escala visual muito ampliada durante as capturas. As telas de Home, detalhe e filtros permaneceram navegáveis, mas a escala afeta a densidade e deve ser conferida com a configuração de acessibilidade que o usuário pretende usar.

## Tratamento de falha e recuperação

O teste sem rede revelou que, ao tentar novamente o catálogo, a consulta da lista de farmácias não era repetida. Em `frontend/src/app/(app)/home.tsx`, a busca de farmácias agora reinicia junto com o contador de retry, limpando o erro e voltando ao estado de carregamento. Jest, TypeScript e ESLint foram reexecutados depois dessa correção e passaram. A variante foi reconstruída e instalada por cima da instalação standalone.

A recuperação visual da lista de farmácias após essa última alteração não pôde ser confirmada por causa do bloqueio de tela mencionado acima. O endpoint `/catalogo/farmacias` respondeu no host quando consultado diretamente. Não foi criado catálogo offline nem alterado o tratamento de sessão.

## Cobertura funcional e pendências

| Fluxo | Situação |
|---|---|
| Inicialização sem Metro e reabertura após force-stop | Confirmado no Xiaomi antes da atualização pequena de retry |
| Home, catálogo, imagens e preços da API | Confirmado na LAN |
| Busca por texto | Campo visível; não foi feita uma consulta de busca nesta homologação |
| Abrir detalhe | Confirmado |
| Filtros | Painel abriu; não foram aplicados filtros de Indiana, Araújo ou Pacheco individualmente |
| Comparação, histórico e tooltip | Não homologados nesta rodada |
| Login, cadastro, favoritos e isolamento por conta | Pendentes; não havia credenciais de teste autorizadas |
| Tema escuro | Visível e confirmado; claro e sistema não foram percorridos |
| API indisponível e recuperação do catálogo | Confirmado antes da atualização pequena; mensagens de erro e botão vistos |
| Recuperação da lista de farmácias após a correção | Pendente de captura após desbloquear o Xiaomi |
| Memória | Aproximadamente 231.850 KiB PSS / 338.180 KiB RSS em uma leitura de `dumpsys meminfo` |
| Inicialização fria | 1.968 ms medidos por `am start -W` em uma abertura; não é amostra estatística |

O teste de desempenho é pontual, no Xiaomi e nesta build interna; não é comparável ao benchmark anterior de desenvolvimento. Não foi feita medição de p95, ANR ou uma série de aberturas. A autenticação e os dados de favoritos não foram alterados.

## Arquivos e estado Git

Na worktree `ana`, ficaram alterações em:

- `frontend/android/app/build.gradle` e novos recursos/manifesto da variante `standalone`;
- `frontend/src/services/apiConfig.ts`, `api.ts` e `src/__tests__/api-config.test.ts`;
- sessão, login e cadastro portados da worktree de desenvolvimento;
- `frontend/src/app/(app)/home.tsx` para sincronizar o retry das farmácias;
- este relatório e evidências em `frontend/reports/visual/android-standalone-2026-10-25/`.

A worktree original permaneceu em `refactor/preco-bao-integrado` com suas alterações locais preservadas. Nenhum commit, merge ou rebase foi feito. Docker continuou apenas com `farmacia_api` e `farmacia_postgres`; workers permaneceram parados.

Este APK é exclusivamente para testes internos. Usa chave debug e endereço IP local; não está pronto para Play Store nem para uso fora da LAN. Não houve publicação, configuração de assinatura definitiva nem validação iOS.
