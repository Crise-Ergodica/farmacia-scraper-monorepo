# Preço Bão — pendências de qualidade de dados

Data: 25/10/2026 · Branch `ana` · Auditoria somente leitura.

## Prioridade alta — identidade e informações farmacológicas

| Caso | Evidência disponível | Próxima ação segura |
|---|---|---|
| Glyxambi ID 2 (`7896026307925`) | Cadastro de 25 mg + 5 mg/30 comprimidos informa ativo pendente e laboratório não informado. Oferta Indiana `IND122816`; a imagem de sua URL contém EAN `7896026306751` e foi confirmada como arte genérica ANVISA da farmácia. API agora não a entrega como foto. | Consultar fonte regulatória/cadastral oficial para ativo, titular/laboratório e EAN da apresentação exata. Atualizar PostgreSQL somente após confirmação e autorização explícita. |
| Glyxambi ID 3103 (`7896026306751`) | Apresentação e EAN diferem do ID 2. Cadastro tem empagliflozina/linagliptina e Boehringer. Candidata Araújo é promoção/arte genérica visualmente confirmada; Pacheco associada ao produto também serve arte ilustrativa. | Confirmar se ID 2 é cadastro duplicado, mudança histórica ou apresentação distinta. Não unificar nem transferir EAN/imagem até prova oficial. |
| Mounjaro IDs 1, 3, 43, 413, 778 e 136 | EANs e dosagens distintas; cada produto ligado corretamente às ofertas pelo SKU/EAN, mas os ativos observados de Araújo/Pacheco são montagens promocionais e Indiana usa imagem genérica. | Procurar fotos oficiais de cada apresentação individual em fonte do fabricante/distribuidor autorizado. Manter placeholder até revisão visual exata. |

## Prioridade média — referências de imagem ainda não confirmadas

- Infralax ID 619 (30 comprimidos) e 1209 (15 comprimidos): arte Indiana OTC e template Pacheco foram confirmados como genéricos e bloqueados. As referências Araújo trazem EAN/SKU e páginas de produto correspondentes, mas ainda exigem inspeção manual de pixels e confirmação de oferta ativa/apresentação antes de exibir como foto segura.
- Outras imagens com EAN no nome divergente: 750 URLs foram detectadas. Resolver cada caso com a identidade cadastrada e a oferta, sem inferir apenas pelo nome do arquivo.
- O inventário de 18.910 referências não passou por verificação HTTP completa. URLs não consultadas continuam “não verificadas”, não “quebradas”.
- A análise identificou 12.932 URLs como genéricas, promocionais ou placeholders segundo marcadores e ativos conhecidos. A classificação é política de bloqueio e merece revisão por lotes para evitar falso positivo/negativo.

## Pendências de catálogo

- 514 dos 13.103 registros não têm EAN.
- 4.499 não têm princípio ativo útil; 4.493 não têm laboratório útil.
- 116 grupos de nomes normalizados coincidentes precisam comparação de EAN, força, forma e quantidade; coincidência de nome não prova duplicidade.
- A base contém 4.109 `imagem_url`: 1.474 com status `verificada`, 2.635 `pendente`, 8.994 sem status. Status existente não foi reescrito nem tratado como prova independente.
- A simulação da política atual encontrou 4.629 referências elegíveis por oferta e 3.517 medicamentos com pelo menos uma imagem potencialmente segura. Estes valores não significam que todos os arquivos foram baixados ou inspecionados.

## Dependências de dados e ações

- Fonte oficial de registro/produto para completar Glyxambi ID 2 e investigar a divergência com ID 3103.
- Revisão manual de cada foto Araújo de Infralax antes de liberar a exibição.
- Fotos autênticas de cada apresentação Mounjaro; candidatos promocionais permanecem bloqueados.
- Se dados oficiais confirmarem mudanças, fazer proposta de migração separada para revisão antes de qualquer escrita em PostgreSQL/JSON.
- Rodar auditoria HTTP controlada por lote apenas com endpoints públicos permitidos, limitando taxa e retomada. Nenhuma coleta foi iniciada nesta tarefa.
- APK atual foi compilado, assinatura v2 verificada, instalado por atualização e aberto no Xiaomi sem Metro. Falta repetir teste conectado: o aparelho não alcança `192.168.2.110:8001` (TCP timeout); Windows recusou regra de firewall temporária por falta de privilégio administrativo. A Home mostrou retry/erro em vez de conteúdo; isso não valida imagens no dispositivo.

Nenhuma alteração de cadastro, EAN, preço, histórico, oferta ou registro JSON foi feita. Nenhum scraper foi iniciado.
