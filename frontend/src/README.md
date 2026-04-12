# Preço Bão frontend base

Estrutura enxuta em **Expo Router + React Native** para rodar em **Android, iOS e web**.

## O que já está pronto

- Login opcional com entrada como convidado.
- Home com busca, filtro, vistos recentemente e mais baratos.
- Busca com listagem de resultados.
- Detalhe do medicamento.
- Histórico de preços.
- Filtros.
- Menu lateral.
- Favoritos.
- Perfil, configurações, farmácias inclusas e página "saiba mais".
- Dados mockados para você conectar depois no backend.

## Estrutura

```text
app/
  _layout.tsx
  index.tsx
  login.tsx
  (app)/
    _layout.tsx
    home.tsx
    search.tsx
    filters.tsx
    favorites.tsx
    profile.tsx
    settings.tsx
    included-pharmacies.tsx
    about.tsx
    medicine/[id].tsx
    history/[id].tsx
components/
  AppDrawerContent.tsx
  BottomNav.tsx
  FavoriteCard.tsx
  FilterChip.tsx
  HistoryChart.tsx
  MedicineCard.tsx
  OfferRow.tsx
  Screen.tsx
  SearchBar.tsx
context/
  AppContext.tsx
data/
  mockData.ts
theme.ts
```

## Como usar

1. Crie um projeto novo com Expo.
2. Ative Expo Router no projeto base.
3. Copie estes arquivos para dentro do projeto.
4. Rode no celular ou na web.

## Próximo passo recomendado

Quando o backend estiver pronto, troque o arquivo `data/mockData.ts` por chamadas reais de API mantendo a mesma estrutura de dados.


## Para o back

GET /medicines?search=
GET /medicines/:id
GET /medicines/:id/prices
GET /medicines/:id/history
GET /favorites
POST /favorites
DELETE /favorites/:id