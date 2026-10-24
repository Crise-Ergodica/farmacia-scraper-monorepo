# External pharmacy image references

Image URLs are stored in `backend/data/image_references/references.json`, separate from PostgreSQL. Docker mounts that host directory at `/app/data/image_references`; the file is atomically replaced after updates. No image bytes are downloaded or stored.

`BasePharmacyScraper` registers references after its commercial transaction commits. A new scraper inheriting from it only needs to return the normal `ProdutoExtraidoSchema` fields (`id`, `sku_interno`, optional `ean`, `link`, optional `imagem_url`). Relative image paths are resolved against `link`. A missing image leaves existing references untouched and does not prevent prices/offers from being saved.

A custom persistence scraper should follow the same order: commit catalog/offer data first, then call `upsert_image_reference` from `app.services.image_registry` with pharmacy ID/name, SKU, EAN, remote product ID, official offer URL, catalog ID, and offer ID. Registry errors are logged and do not roll back price data. The registry de-duplicates by exact offer ID; records without an offer ID include the catalog ID in their key.

The API resolves URLs from the registry by catalog ID and linked offer IDs and returns `imagem_urls`. It does not expose offer image columns. The frontend is source agnostic and attempts these URLs in order before showing its placeholder. Generic artwork is allowed; the registry enforces HTTPS, public-host/port checks, supported image extensions, and exact product association.

A one-time migration snapshot and SHA-256 sidecar are in `backend/reports/image-reference-migration-backup-2026-10-24.json` and `.sha256`. The migration is repeatable against an existing backup and registry.
