# Imagens do Preço Bão: persistência, portabilidade e manutenção

## Como a imagem fica armazenada

O PostgreSQL armazena referências HTTPS e metadados; as fotografias continuam nas
CDNs das farmácias. `catalogo_base` guarda a referência principal, sua origem, SKU/EAN
de evidência, tipo de associação, horários e falhas recentes. `ofertas_farmacia`
guarda as URLs alternativas associadas ao medicamento e à página/SKU da oferta.
Não há dependência de cache local, arquivos temporários ou memória do processo para
encontrar a referência.

No Compose, o serviço `db` usa o volume nomeado `backend_postgres_data`. Reiniciar
contêineres preserva esse volume. **Não use `docker compose down -v`** em um ambiente
que contém dados que deseja manter: `-v` remove volumes. Migrações são aditivas e
devem ser aplicadas com `alembic upgrade head`.

As referências atuais foram exportadas para
`backend/reports/image-references-v1-post-check-2026-10-11.json` (versão 1, 4.109
registros, 3.640 URLs únicas). O arquivo contém nomes, EANs, URLs, origem e SKUs/
identificadores de ofertas; não contém preços, favoritos, contas, credenciais,
tokens, cookies ou sessões. As URLs são referências públicas às fontes, não cópias
das imagens.

## Preparar um ambiente

No Windows PowerShell, na pasta do repositório:

```powershell
cd C:\dev\farmacia-scraper-monorepo\backend
poetry install
docker compose up -d db
docker compose ps
```

Configure `DATABASE_URL` para o endereço alcançável pelo processo que executará
Alembic. No host Windows, a porta publicada pelo Compose é `4242`; dentro dos
contêineres, use o nome do serviço `db` e a porta `5432`:

```powershell
$env:DATABASE_URL = "postgresql+psycopg2://<usuario>:<senha-url-encoded>@127.0.0.1:4242/<banco>"
poetry run alembic upgrade head
```

Mantenha `.env` fora do Git e configure `DATABASE_URL`, `DATABASE_URL_DOCKER`,
`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `JWT_SECRET` e CORS por
ambiente. O Compose mantém valores de desenvolvimento compatíveis com o ambiente
local existente; em servidor, substitua-os por valores próprios e consistentes com
o volume já inicializado. Se a senha contiver caracteres especiais, use sua forma
percent-encoded em uma URL SQLAlchemy. Não troque a senha do serviço PostgreSQL
apenas alterando a variável de ambiente: em um volume já inicializado, a variável
não altera a senha já gravada no PostgreSQL.

Para executar a API localmente:

```powershell
poetry run uvicorn app.main:app --reload
```

O frontend usa `EXPO_PUBLIC_API_URL`. No navegador local, a configuração atual é
`http://localhost:8000`; no emulador Android use o endereço de host alcançável pelo
emulador (Android Emulator normalmente usa `http://10.0.2.2:8000`); em dispositivo
físico use o IP LAN do computador; em servidor use o domínio HTTPS público. Não
empacote `localhost` para um aplicativo que será usado em outro dispositivo.

## Exportar e importar referências

Crie um arquivo novo; o exportador se recusa a sobrescrever arquivos existentes:

```powershell
poetry run python scripts/portar_referencias_imagens.py export `
  --output reports/image-references-v1-$(Get-Date -Format yyyyMMdd-HHmmss).json
```

No computador destino, primeiro prepare as migrations e carregue o catálogo pelas
fontes/rotinas normais do projeto. O importador **não cria medicamentos** e não usa
IDs locais como identidade. Ele associa por EAN/GTIN, ou por farmácia + SKU + URL
oficial da oferta. Para grupos legados sem esses identificadores, usa somente uma
correspondência de nome exato quando todos os itens do grupo de origem têm o mesmo
SKU de farmácia, a mesma imagem e a cardinalidade do grupo coincide; conflito ou
ambiguidade permanece no relatório.

```powershell
$env:DATABASE_URL = "postgresql+psycopg2://<usuario>:<senha-url-encoded>@<host>:<porta>/<banco-destino>"
poetry run alembic upgrade head
poetry run python scripts/portar_referencias_imagens.py import `
  --input C:\caminho\seguro\image-references-v1.json `
  --report reports/image-reference-import-$(Get-Date -Format yyyyMMdd-HHmmss).json
```

A operação é idempotente. Não substitui uma imagem diferente que já exista no
destino. O relatório lista associações, itens já presentes, conflitos, registros
sem correspondência e URLs rejeitadas por segurança. Uma importação com pendências
retorna código de saída `2`; consulte o relatório e não force associações por ID.
Referências importadas são marcadas como pendentes de verificação local, mas a API
as entrega imediatamente enquanto a URL respeitar a allowlist HTTPS.

### Limite de portabilidade encontrado

O teste isolado executou a cadeia completa de Alembic sobre um PostgreSQL vazio,
preparou um catálogo fixture com os mesmos 4.109 itens, importou duas vezes e
consultou cada endpoint aplicável. Foram restauradas **4.091/4.109 referências**;
as 4.091 rotas responderam com o destino esperado. Houve **0 conflitos**, **18
sem correspondência segura** e **0 URLs inválidas**. As 18 pendências estão em três
grupos sem EAN nem ofertas no catálogo original:

- Dipirona Monoidratada 500mg Neo Química 20ml (4 registros; fontes variam dentro do
  grupo completo).
- Alopurinol 100mg Prati Genérico com 30 Comprimidos (7 registros; fontes variam).
- Glyxambi 25mg + 5mg com 30 Comprimidos (7 registros; fontes variam).

Como o grupo contém SKUs/imagens diferentes e o destino não tem SKU/EAN de oferta
para identificar cada linha, o importador deixa esses 18 itens sem imagem. Isso é
intencional: escolher por nome ou ID poderia transferir uma embalagem para outro
registro. A evidência está em
`backend/reports/image-reference-restore-test-post-check-2026-10-11.json`.

Para reproduzir **todos** os dados e os 4.109 vínculos locais exatamente, restaure
um backup integral do PostgreSQL em um banco novo e protegido. Um dump integral
também pode conter contas/favoritos e outros dados pessoais; mantenha-o privado e
não o use como arquivo de portabilidade pública de imagens. O backup feito antes
das migrations desta tarefa está fora do repositório, em
`%LOCALAPPDATA%\PrecoBaoBackups\farmacia_db-pre-image-maintenance-20261011.dump`.
Seu SHA-256 está em `backend/reports/image-db-backup-manifest-2026-10-11.json`.

## Cobertura local

Relatório local, sem chamadas de rede:

```powershell
poetry run python scripts/verificar_cobertura_referencias_imagens.py
```

Ele mede catálogo, URLs presentes, allowlist/tipo, vínculo de identidade, URLs
únicas e marcadores conhecidos de imagem genérica. A classificação “não marcada
como genérica” não é uma prova visual de fotografia específica.

Para validar a disponibilidade HTTP e as rotas da API, use a auditoria retomável
existente. Ela limita concorrência e retoma resultados gravados:

```powershell
poetry run python scripts/validar_imagens_catalogo.py --resume
```

Ela percorre o catálogo completo; não deve ser executada a cada abertura da Home.

## Imagens de novos medicamentos

Os scrapers Indiana e Araujo já chamam `register_image_candidate` ao persistir o
catálogo e a oferta. A associação é registrada sem fazer download durante o ciclo
de scraping; a URL passa pelos validadores de host, HTTPS e identidade. Imagens
genéricas de uma oferta podem ser exibidas quando vinculadas ao produto correto.
Se o scraper não encontrar imagem, a oferta permanece no banco e a rotina
`recover-pending` procura candidatos disponíveis sem bloquear a coleta de preços.

Execute uma tentativa manual limitada:

```powershell
poetry run python scripts/manter_imagens_catalogo.py recover-pending --limit 100
```

## Verificação e recuperação periódica

O monitor consulta um lote limitado, com no máximo quatro requisições concorrentes
por execução e intervalo mínimo entre requisições do mesmo host. Registra tentativa,
última validação bem-sucedida, status HTTP/motivo e falhas consecutivas no
PostgreSQL. Timeout/erro de rede recebe uma segunda tentativa e não troca a imagem
na primeira falha; alternativa é tentada em 403/404 ou após o limite de falhas.
A alternativa só é persistida depois de passar identidade e validação HTTP. Sem
alternativa, o URL original é preservado.

Execução manual:

```powershell
poetry run python scripts/manter_imagens_catalogo.py check --limit 100
```

Para um worker periódico no Docker Compose:

```powershell
docker compose --profile maintenance up -d --build image-maintenance
docker compose logs -f image-maintenance
```

O perfil roda lotes e recuperação de pendentes a cada 24 horas por padrão. Configure
`IMAGE_MAINTENANCE_INTERVAL_SECONDS`, `IMAGE_MONITOR_BATCH_SIZE`,
`IMAGE_MONITOR_RECHECK_HOURS`, `IMAGE_MONITOR_CONCURRENCY` e
`IMAGE_MONITOR_HOST_INTERVAL` no ambiente. Desative as verificações com
`IMAGE_MONITOR_ENABLED=false` e a recuperação com `IMAGE_RECOVERY_ENABLED=false`;
para parar o worker, use `docker compose --profile maintenance stop image-maintenance`.
O perfil não inicia junto com a aplicação normal. Em Windows sem Docker, agende os
dois comandos Poetry no Agendador de Tarefas do Windows com intervalo diário e
`Start in` apontando para `backend`.

## Fallback do frontend

`MedicineImage` tenta, nesta ordem, a referência versionada do catálogo, imagens
específicas de ofertas do mesmo catálogo, referências sem classificação e imagens
genéricas dessas ofertas. Cada erro avança uma única vez; ao terminar a lista,
aparece o placeholder. A imagem usa `contain`. Alterar a URL da referência muda o
hash da rota da API e reinicia o cursor de fallback, evitando cache antigo. Hosts
aceitos são explícitos; a API só redireciona para HTTPS e origens permitidas, sem
aceitar URL arbitrária fornecida pelo cliente.

## Backup e restauração integral

Antes de migrations ou mudanças operacionais relevantes, grave e valide um dump
fora do repositório. Os comandos abaixo são para PostgreSQL em Docker; ajuste o
nome do contêiner e banco conforme o ambiente real:

```powershell
docker exec farmacia_postgres pg_dump -U <usuario> -d <banco> -Fc -f /tmp/pre-change.dump
docker cp farmacia_postgres:/tmp/pre-change.dump C:\caminho\seguro\pre-change.dump
docker exec farmacia_postgres pg_restore --list /tmp/pre-change.dump
docker exec farmacia_postgres rm -f /tmp/pre-change.dump
```

Para restaurar, crie um PostgreSQL e um banco **novos e vazios**, copie o dump para
eles e então execute `pg_restore --no-owner --dbname=<banco-novo> <dump>`. Não use
`--clean` no banco atual. Em um restore de volume, mantenha a cópia original até
validar migrations, contagens e endpoints. A restauração integral replica também
os dados privados presentes naquele dump.

## Android

O export do Expo não comprova uso funcional. `adb devices` deve listar um emulador
ou dispositivo. Configure `EXPO_PUBLIC_API_URL` para um host acessível por ele,
inicie a API e execute `npx expo run:android`; valide Home, busca, detalhe, favoritos
e troca de imagem no dispositivo. Sem dispositivo conectado, limite o resultado ao
export Android.
