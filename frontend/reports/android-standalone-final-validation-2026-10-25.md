# Preço Bão — homologação Android standalone e preparação HTTPS

Data: 25/10/2026. Worktree `C:\dev\farmacia-scraper-monorepo-ana`, branch `ana`.

## APK instalado e identificado

- Arquivo: `android/app/build/outputs/apk/standalone/app-standalone.apk`.
- Package: `com.dragoniana.precobao.standalone` — `1.0.0-internal`, versionCode 1, minSdk 24, targetSdk 36, ABI arm64-v8a.
- SHA-256: `F0497FDC3216BBD3173772C9276CD44935629814CCD48529BF3B062B65323E94`.
- Instalado no Xiaomi por `adb install -r` (retorno `Success`), sem desinstalar nem limpar dados. A assinatura APK v2 foi verificada.
- URL embutida: `http://192.168.2.110:8000`, configuração explícita da variante LAN. O host e o Xiaomi estavam na mesma rede; o endpoint respondeu HTTP 200.
- Metro desligado: porta 8081 sem listener e `adb reverse` sem encaminhamento. O bundle Hermes está dentro do APK. O app foi aberto após force-stop e funcionou sem Metro; FastAPI continuou disponível.
- O APK anterior, documentado em `android-standalone-build-2026-10-25.md`, é evidência histórica e não foi usado para atribuir os resultados desta rodada.

## Testes reais no Xiaomi

O aparelho foi confirmado desbloqueado e com o app em primeiro plano. Resolução reportada: 1080×2400. O sistema do aparelho usa fonte ampliada e teclado personalizado; as capturas mostram essa configuração de acessibilidade, que altera a escala visual em relação a uma configuração padrão.

| Fluxo | Resultado desta build |
|---|---|
| Inicialização standalone | Aprovada: abriu após encerramento forçado, sem Metro. |
| Home e catálogo | Aprovados: catálogo carregou 13.103 medicamentos; busca e rolagem funcionaram. |
| Busca | Aprovada: Paracetamol retornou 140 resultados; Glyxambi, 10; Infralax, 2. |
| Farmácias | Aprovadas: Todas, Araújo, Indiana e Pacheco responderam e alteraram resultados. Para Glyxambi, Araújo mostrou 1 resultado, Indiana 2 e Pacheco 2. |
| Categoria e painel de filtros | Painel abriu, mostrou filtro ativo e categorias Genérico/Similar. Os botões Limpar/Aplicar ficaram acessíveis após rolagem, acima da navegação inferior. Seleção de laboratório não foi concluída nesta rodada. |
| Detalhes e comparação | Detalhe abriu a partir do resultado, preço e comparação de ofertas foram exibidos. Um registro de Glyxambi 25 mg apresentou princípio ativo e laboratório como “Não informado”; a imagem também era embalagem genérica. |
| Histórico e gráfico | Aprovados visualmente: períodos 7 dias a 1 ano/Tudo, farmácias, série e tooltip por toque foram exibidos. Histórico consultado era do Glyxambi 10 mg. Araújo não era uma série disponível nesse medicamento. |
| Temas | Claro e escuro foram selecionados; Sistema foi restaurado. Persistência após fechar e reabrir não foi medida. |
| Favoritos e perfil | Em modo convidado, a tela de favoritos mostrou a exigência de login e o perfil mostrou estado de convidado. Não houve escrita de favoritos/perfil. |
| Login/cadastro e teclado | Formulários foram abertos sem submissão. O teclado abriu no campo de email e a ação Entrar continuou visível. Cadastro completo coube na tela sem teclado. Cadastro real não foi enviado. |
| Erro e retry de rede | Com Wi-Fi e dados móveis desligados e app iniciado a frio, Home mostrou erro do catálogo e erro de farmácias, sem mostrar preços como atuais. Ao restabelecer a rede e acionar retry, catálogo e farmácias carregaram novamente. |

### Correção descoberta durante a homologação

O teste offline mostrou que o erro isolado de farmácias não oferecia retry próprio. Foi acrescentada a ação **Tentar novamente** junto à mensagem de farmácias; ela incrementa o mesmo contador de recarga que refaz catálogo e farmácias. Jest, TypeScript e ESLint passaram após a alteração. O APK foi reconstruído, reinstalado e o estado de falha/reconexão foi observado nessa versão. Capturas: `visual/android-standalone-2026-10-25/final-retry-offline.png` e `final-pharmacy-retry.png`.

### Divergência de imagens observada

Na tela de detalhe de um registro de Glyxambi 25 mg foi exibida uma embalagem genérica da Indiana (“produto sem foto”), junto a campos de princípio ativo e laboratório como “Não informado”. O catálogo também mostrou essa imagem genérica em resultados de Infralax e Mounjaro. Um card de Glyxambi/Pacheco mostrou imagem específica da oferta. Isso evidencia registros com metadados incompletos e divergência entre imagem associada ao medicamento e imagem da oferta; nenhuma imagem, oferta ou dado do catálogo foi alterado nesta homologação. As capturas `final-f049-detail.png`, `f049-search-infralax.png` e `final-reconnect-home.png` registram ocorrências. Requer auditoria de associação de imagens e dos campos do catálogo antes de considerar esses itens visualmente homologados.

## Capturas desta build

As evidências seguintes foram capturadas após instalar o APK com o hash acima, em `visual/android-standalone-2026-10-25/`: `final-f049-home.png`, `final-f049-search.png`, `f049-paracetamol.png`, `f049-glyxambi-all.png`, `f049-infralax-all.png`, `f049-filter-araujo.png`, `f049-filter-indiana.png`, `f049-filter-pacheco.png`, `final-f049-detail.png`, `final-f049-detail-lower.png`, `final-f049-history.png`, `final-f049-history-chart.png`, `final-f049-history-tooltip.png`, `f049-history-filters.png`, `f049-history-7d.png`, `f049-theme-light.png`, `f049-theme-dark.png`, `f049-theme-system.png`, `final-favorites-guest.png`, `final-profile-guest.png`, `final-login-screen.png`, `final-signup-visual.png`, `final-retry-offline.png` e `final-pharmacy-retry.png`. Capturas anteriores à reinstalação foram mantidas como arquivos de trabalho, mas não são usadas como prova do hash F049.

## Itens pendentes ou limitados

- Login autenticado, persistência de sessão, edição de perfil e adicionar/remover favoritos: pendentes; não há credenciais de teste autorizadas. Nenhuma conta foi criada nem dados de usuário foram enviados.
- Seleção efetiva de laboratório: pendente. Retry de farmácias em erro isolado foi adicionado, mas nesta reprodução a indisponibilidade afetou catálogo e farmácias ao mesmo tempo.
- Persistência do tema após reinício e medições de startup/cache frio/cache quente: não medidas.
- Regressão visual Web em 390/768/1440/1920 px e ambos os temas: export Web foi gerado, mas não houve inspeção em navegador nessas dimensões. Export não é evidência visual.
- Testes em outra rede, dados móveis e acesso externo HTTPS: pendentes porque ainda não existe endpoint HTTPS implantado/autorizado. A API continua LAN.
- Registro/quantidade atual do catálogo veio da API e coincidiu com o frontend: 13.103 durante o teste; não é contagem permanente.

## Validações automatizadas

| Verificação após a última alteração de Home | Resultado |
|---|---|
| Jest | Passou: 16 suítes, 89 testes. |
| TypeScript (`npx tsc --noEmit`) | Passou. |
| ESLint (`npm run lint`) | Passou. |
| `expo install --check` | Passou. |
| Expo Doctor | 19/20; único aviso sobre configuração nativa em `app.json` e diretórios `android/ios` num projeto não-CNG. |
| Expo export Web | Passou (`dist`). |
| Expo export Android | Passou (`dist-android`, bundle Hermes). |
| Gradle `assembleStandalone` | Passou para arm64-v8a, perfil LAN. |
| APK Signature v2 | Verificada no APK standalone. |
| Guarda Gradle de URL/cleartext | HTTPS e LAN privado aceitos; loopback e HTTPS privado rejeitados nas verificações documentadas. |
| Ruff/backend | Não executado nesta rodada; backend não foi alterado. |
| `git diff --check` | Passou antes da última alteração; rodar novamente na revisão final. |

## Segurança e infraestrutura HTTPS

Foi preparado o plano `../../docs/android-api-https-deployment-plan.md`. O Gradle agora valida URL e modo antes de construir; somente a variante LAN permite HTTP e tráfego cleartext. O perfil de Quick Tunnel do Compose passou a exigir ativação explícita. Nenhum túnel foi iniciado, porta externa aberta, domínio registrado ou serviço contratado. FastAPI e PostgreSQL ficaram locais; nenhum dado de banco, preço ou histórico foi alterado.

## Git e worktrees

Branch permanece `ana`; não houve commit, merge, rebase ou branch nova. A worktree `C:\dev\farmacia-scraper-monorepo` não foi modificada por esta rodada. Alterações locais e arquivos não rastreados foram preservados.
