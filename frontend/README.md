# Preço Bão — Frontend

Aplicativo React Native com Expo Router, executável em Android, iOS e Web. A interface consome a API FastAPI configurada por `EXPO_PUBLIC_API_URL` no arquivo `.env` local.

## Desenvolvimento

```sh
npm install
npm run web
# ou
npm run android
```

No Android, use o endereço da API acessível pelo dispositivo ou emulador; `127.0.0.1` aponta para o próprio dispositivo.

## Verificações

```sh
npx tsc --noEmit
npm run lint
npm test
npx expo export --platform web
npx expo export --platform android
```

## Estrutura

- `src/hooks/useAuthSession.ts`: sessão, login, recuperação e edição de perfil.
- `src/hooks/useFavoritesState.ts`: favoritos persistidos por usuário e sincronização com a API.
- `src/hooks/useCatalogState.ts` e `src/services/catalog.ts`: catálogo paginado, busca, filtros, detalhes sob demanda e cache limitado.
- `src/context/AppContext.tsx`: composição dos contextos de sessão, catálogo e favoritos.
- `src/app/`: telas e fluxos de navegação.

O catálogo é consultado em páginas no servidor. Os detalhes e favoritos são carregados por identificador ou pela conta autenticada, sem depender da página atual. Filtros dentro da mesma categoria aceitam qualquer opção selecionada; categorias diferentes e os demais critérios são combinados em conjunto.

Histórico recente é mantido na sessão atual do aplicativo. Alertas de preço e preferências de idioma ainda não estão disponíveis; não há controles ativos para esses recursos.
