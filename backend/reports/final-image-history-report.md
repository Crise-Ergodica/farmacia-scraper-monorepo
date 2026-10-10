# Preço Bão — imagens e histórico

Data da auditoria: 2026-10-09. Ambiente: PostgreSQL local em Docker; nenhum banco de produção foi usado.

## Cobertura das imagens

| Medida | Antes | Depois |
| --- | ---: | ---: |
| Produtos no catálogo | 4.109 | 4.109 |
| Imagens verificadas | 21 (0,51%) | 2.724 (66,29%) |
| Itens sem imagem verificada | 4.088 | 1.385 (33,71%) |
| Itens com alguma imagem em oferta | 3.638 | — |
| Itens sem imagem em oferta | 471 | — |

O processamento verificou 2.696 associações da Indiana e 28 da Araújo. O cadastro contém 3.607 EANs com dígito verificador válido e 3.638 medicamentos com oferta que fornece SKU e URL de produto.

A consulta pública paginada da Indiana foi tentada novamente, mas retornou HTTP 400 ao continuar no offset 2.550. A varredura de imagens locais foi concluída para os 4.109 medicamentos; a cobertura da fonte pública permanece incompleta. Por isso, produtos sem correspondência exata continuam `pendente`, em vez de serem marcados como definitivamente sem imagem.

Motivos registrados para os 1.385 itens restantes:

- 738 candidatos eram ícones, embalagens genéricas ou imagens promocionais.
- 450 não foram cobertos pela busca pública incompleta da Indiana.
- 154 candidatos tinham EAN divergente.
- 27 tinham SKU divergente da página do produto.
- 13 falharam na conferência de EAN da consulta por SKU exato.
- 3 usavam formato não aceito como imagem de produto.

O detalhamento item a item está em [image-audit.json](image-audit.json). O processamento é retomável com `poetry run python -m scripts.processar_imagens`; use `--retry-discovery` para repetir a paginação da fonte a partir do offset salvo.

## Histórico de preços

O backend registra uma observação da oferta em cada coleta válida e cria eventos históricos na primeira observação após a migration ou quando o preço muda. Uma coleta repetida com preço igual atualiza a data de observação da oferta, sem criar ponto ou variação fictícia. Os eventos históricos anteriores foram preservados.

O endpoint `GET /api/v1/medicines/{id}/history` retorna séries cronológicas por farmácia, período, filtro de farmácia e estatísticas. A página usa esses dados reais, mostra ofertas atuais em seção separada e mantém navegação direta pelo ID. O gráfico posiciona datas reais e evita ligar pontos separados por mais de 45 dias.

## Validação

- Backend: Ruff passou; Pytest passou (20 testes); Alembic está em `3a72d8ce1f40 (head)`.
- Frontend: Jest passou (13 testes); TypeScript e ESLint passaram.
- Expo: export Web passou; export Android passou. `adb devices` não encontrou emulador, portanto não foi feito teste funcional Android.
- Navegador: telas capturadas em 360, 390, 768, 1280 e 1440 px; erros JavaScript/falhas de requisição registrados: nenhum nos fluxos capturados.
- Fluxos locais: cadastro/login, busca paginada, filtro, detalhe, favorito, remoção, logout/login, persistência do favorito, edição persistente do perfil e isolamento entre duas contas passaram.
- API local: catálogo retornou 4.109 produtos; endpoint de imagem retornou redirect HTTPS permitido; histórico retornou eventos e estatísticas reais.

As capturas Web estão em `frontend/reports/visual/`. Destaques: `home-360.png`, `home-390.png`, `home-768.png`, `home-1440.png`, `search-360.png`, `search-390.png`, `favorites-auth-390.png`, `profile-auth-390.png`, `history-top-390.png` e `history-bottom-390.png`.

## Limitações conhecidas

- Ainda há 1.385 medicamentos sem imagem verificada; não foi usada imagem aproximada para aumentar cobertura.
- A listagem pública Indiana limita a paginação e responde HTTP 400 no offset 2.550. A retomada continuará útil quando esse limite ou a fonte mudar.
- As referências validadas usam URLs HTTPS dos domínios permitidos e são servidas por uma rota estável da API que redireciona à origem. Não há armazenamento próprio das imagens, pois não foi confirmado direito de redistribuição/cópia.
- Não há emulador Android disponível para validar teclado, toque e fluxos no dispositivo.
