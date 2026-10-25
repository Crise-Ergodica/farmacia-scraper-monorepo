# Relatório — desempenho, teclado Android e navegação mobile

**Data:** 24/10/2026  
**Branch:** `refactor/preco-bao-integrado`  
**Dispositivo:** Xiaomi 23021RAAEG, Android 15, 1080×2400, densidade configurada 461 dpi, escala de fonte 1.0  
**API local:** `192.168.2.110:8000`

As alterações locais e os dados existentes foram preservados: não houve `adb uninstall`, `pm clear`, alteração no backend ou no banco, criação de conta de teste nem commit. Antes da reinstalação, a interface autenticada e a lista vazia de Favoritos foram observadas; nenhum favorito foi alterado. O APK foi atualizado por `adb install -r`, com `firstInstallTime` inalterado, mas depois da reinicialização o aplicativo apresentou Login. Portanto, a restauração da sessão não ficou confirmada e não afirmo que a sessão autenticada tenha sido preservada. Não havia credenciais disponíveis para entrar novamente sem interferir na conta.

## Desempenho dos detalhes

### Investigação

A medição no Xiaomi separou o toque, a navegação, a montagem, a consulta, a apresentação do cache e a imagem. Na primeira abertura observada do medicamento da Home:

| Etapa | Tempo desde o toque |
| --- | ---: |
| Evento de toque | 0 ms |
| Início da navegação | 7 ms |
| Montagem do detalhe | 402 ms |
| Conteúdo disponível do cache | 420 ms |
| Início da atualização pela API | 408 ms |
| Resposta da API | 524 ms |
| Imagem carregada | 638 ms |
| Conteúdo utilizável | 654 ms |
| Conteúdo pronto | 661 ms |

Na reabertura do mesmo medicamento, o cache permitiu apresentar os dados em 226 ms; a atualização da API respondeu em 361 ms e a imagem terminou em 464 ms. Foram duas aberturas observadas, amostra insuficiente para p50/p95 ou para afirmar uma distribuição de desempenho.

Antes da correção, as capturas de referência mostravam a tela de carregamento aos 500 ms e o detalhe preenchido por volta de 1500 ms. Depois, a captura aos 500 ms já mostrava o detalhe com conteúdo e imagem. Esses intervalos das capturas são aproximados; os marcos do log `[medicine-open]` são a medição instrumentada.

A demora não era explicada apenas pela API: o início da navegação ocorreu em 7 ms, mas a montagem veio 395 ms depois; a API levou aproximadamente 116 ms entre início e resposta, e a imagem carregou após o conteúdo inicial. Isso aponta a montagem/execução do cliente como parte relevante do tempo percebido. O cache disponível na Home antecipou a informação; não foi feita uma comparação controlada entre processo frio e processo de produção. O aparelho executou o cliente de desenvolvimento conectado ao Metro.

### Correções

- A tela de detalhe agora inicializa com os dados do medicamento já mantidos no cache por ID e atualiza as ofertas pela API em segundo plano. Os preços novos da API continuam sendo consultados.
- A tela apresenta um estado inicial estruturado quando ainda não há cache e identifica quando precisa exibir dados anteriores após falha de atualização.
- O cache permanece limitado a 180 medicamentos. A leitura de item por ID é estável e não publica uma atualização de estado global a cada gravação do cache.
- Requisições simultâneas para o mesmo ID são compartilhadas, inclusive quando uma chamada pede atualização forçada. A limpeza de uma requisição pendente confere se ela ainda é a requisição ativa daquele ID.
- Imagem carrega independentemente do conteúdo do detalhe. O callback de imagem participa da instrumentação sem bloquear preço, título e ofertas.
- A instrumentação detalhada fica restrita ao modo de desenvolvimento e registra toque, navegação, montagem, conteúdo, rede e imagem.

## Teclado e formulários

No Xiaomi, o layout original usava `adjustResize`, `KeyboardAvoidingView` e `ScrollView`, mas o foco nos campos inferiores podia deixar o campo sob o teclado. A medição encontrou também uma diferença de origem entre `measureInWindow` e `keyboardDidShow`; a compensação considera a altura da barra de status. A rolagem agora consulta a referência do campo depois do foco, quando a referência nativa já está disponível.

Cadastro verificado no aparelho:

- Abertura do teclado e foco nos campos inferiores.
- Avanço de Senha para Confirmar senha pelo botão “Próximo”.
- Senha e confirmação inteiramente visíveis acima do teclado.
- Rolagem manual com teclado aberto até os campos inferiores e os botões “Cadastrar” e “Já tenho conta”.
- “Concluir” fecha o teclado sem enviar o cadastro.
- Toque em “Cadastrar” com o formulário vazio apresentou as mensagens locais de validação, manteve o teclado aberto e não enviou cadastro.

Login verificado no aparelho: o campo Senha permaneceu visível com o teclado aberto e a tecla “Concluir” o fechou. Não foram enviados dados de login inválidos ao backend nesta rodada.

Os campos mantiveram o fluxo com React Hook Form, validações existentes, autocomplete e ações de mostrar/ocultar senha. A configuração `android:windowSoftInputMode="adjustResize"` foi mantida. As rotas de edição de perfil e outros formulários não foram submetidas a uma auditoria individual nesta etapa.

## Navegação mobile

A barra inferior agora mostra quatro destinos: **Início, Favoritos, Perfil e Menu**. Buscar deixou a barra inferior; a pesquisa da Home continua disponível e Buscar permanece acessível pelo menu e pela rota `/search`.

No Xiaomi, foram abertas a Home, uma tela de detalhe, Favoritos, Perfil e o menu lateral. A lista existente de Favoritos mostrou zero itens; não foram adicionados ou removidos favoritos para proteger os dados da conta.

## Web e responsividade

O export Web passou. Uma captura Web inicial em 390 px revelou que o contêiner de conteúdo somava o padding à largura CSS e fazia o formulário de login ultrapassar a viewport. `Screen` agora usa `boxSizing: 'border-box'` no conteúdo e na navegação mobile.

O Edge headless capturou a tela de login antes desse ajuste. As tentativas de captura visual pós-ajuste não concluíram, pois os processos headless permaneceram ativos sem gravar os arquivos. Portanto, a ausência de overflow pós-ajuste foi inferida da correção do cálculo de caixa e do TypeScript/build Web, não validada por uma segunda captura. Não foi possível comprovar visualmente os quatro tamanhos 390, 768, 1440 e 1920 px nesta rodada. Também não há execução funcional iOS disponível neste ambiente.

## Verificações

| Verificação | Resultado |
| --- | --- |
| Jest completo | 16 suítes e 83 testes passaram |
| TypeScript (`npx tsc --noEmit`) | Passou |
| ESLint (`npm run lint`) | Passou |
| Export Expo Web | Passou |
| Export Expo Android | Passou |
| `git diff --check` | Passou; Git apenas avisou sobre normalização futura de LF/CRLF em arquivos locais já modificados |
| Gradle `:app:assembleDebug` (arm64-v8a) | Passou; APK debug gerado e instalado com `adb install -r`, sem desinstalar o pacote |
| Xiaomi Android 15 | Teclado, detalhe, imagem e navegação observados funcionalmente |
| iOS | Pendente: não há dispositivo/runtime iOS neste ambiente |

### Classificação das três correções

| Correção | Situação | Evidência/limite |
| --- | --- | --- |
| Abertura progressiva dos detalhes | Parcialmente validada | Toque pela Home, montagem, cache, API e imagem instrumentados em duas aberturas no Xiaomi. Aberturas por Busca/Favoritos, item frio, sem imagem e mudança rápida de ID não foram todas exercitadas nesta rodada. |
| Teclado e foco no cadastro/login | Validada no Xiaomi para os casos exercitados | Cadastro percorreu Senha/Confirmar senha, scroll com teclado e visibilidade dos botões; login manteve senha visível e fechou teclado por Concluir. Não foram enviados dados inválidos ao serviço. |
| Barra inferior com quatro opções | Parcialmente validada | Início, Favoritos, Perfil e Menu foram abertos no Xiaomi; Buscar ficou acessível pela Home/menu. Não houve matriz completa de tema e estados em todas as rotas. |

## Pendências e limites

- Não houve medição controlada em modo release nem comparação estatística p50/p95; só duas aberturas instrumentadas no cliente de desenvolvimento.
- Os testes de teclado foram feitos no Xiaomi real; outros tamanhos de tela e iOS ainda precisam de validação.
- A atualização por `adb install -r` manteve o pacote instalado, mas após o reinício foi exibida a tela Login. Como a restauração valida o token com `/users/me` e limpa a sessão ao falhar, não foi possível distinguir se o token estava ausente ou se a validação falhou. A persistência da sessão permanece pendente; não foram tentados login inválido, alteração de perfil ou mudanças de favoritos para evitar mutação da conta real.
- A captura Web posterior à correção do box model e as resoluções 768, 1440 e 1920 px continuam pendentes.
- O SDK real foi acessado temporariamente por uma unidade `Q:` para contornar o caminho Unicode do perfil do Windows; o build arm64 passou. `frontend/android/local.properties` foi restaurado byte a byte para o valor preexistente (`sdk.dir=C:\\Android`) e a unidade temporária foi removida. Nesse estado original, a compilação Gradle não encontra o SDK, pois `C:\\Android` não existe nesta máquina.

## Arquivos de código alterados nesta tarefa

- `frontend/src/app/(app)/medicine/[id].tsx`
- `frontend/src/app/(app)/home.tsx`
- `frontend/src/app/(app)/search.tsx`
- `frontend/src/app/(app)/favorites.tsx`
- `frontend/src/app/login.tsx`
- `frontend/src/app/signup.tsx`
- `frontend/src/components/MedicineImage.tsx`
- `frontend/src/components/Screen.tsx`
- `frontend/src/hooks/useCatalogState.ts`
- `frontend/src/services/medicineOpenPerformance.ts`
- `frontend/src/__tests__/catalog.test.ts`
- `frontend/src/__tests__/screen-navigation.test.tsx`

Capturas e dumps brutos usados na inspeção local estão em `frontend/reports/visual/android-performance-keyboard-navigation-2026-10-24/`; eles não são anexados aqui para evitar expor dados pessoais visíveis em algumas telas do aparelho.
