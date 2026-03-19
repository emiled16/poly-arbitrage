# poly-arbitrage

Initial local-first workspace for Polymarket market ingestion and downstream ELT.

## Current slice

- dispatcher-based raw ingestion contracts
- raw Polymarket Gamma and CLOB connectors
- separate ELT normalization layer for source-to-canonical transforms
- provider-agnostic raw archive boundary with local and MinIO-backed object-store adapters
- durable local ingestion manifest and failure logs

## Quickstart

```bash
PYTHONPATH=src python3 scripts/ingest_polymarket.py --source polymarket_gamma --dataset markets --limit 3
```

## MinIO

Start local MinIO with Docker Compose:

```bash
docker compose up -d minio
```

Then ingest into the MinIO-backed raw archive:

```bash
export POLY_ARB_MINIO_ACCESS_KEY=minioadmin
export POLY_ARB_MINIO_SECRET_KEY=minioadmin
PYTHONPATH=src python3 scripts/ingest_polymarket.py \
  --raw-store-backend minio \
  --raw-store-container raw \
  --source polymarket_gamma \
  --dataset markets \
  --limit 3
```
