# poly-arbitrage

Initial local-first workspace for Polymarket market ingestion and downstream canonical-data work.

## Current slice

- production-oriented ingestion runtime backed by PostgreSQL, RabbitMQ, and MinIO/local object storage
- SQLAlchemy-backed database layer with separate table definitions, record stores, and domain repositories
- Alembic migration baseline plus explicit store initialization instead of runtime schema auto-creation
- shared source-handler interface for Polymarket today and additional providers later
- recurring `polymarket_gamma/markets` ingestion now uses full snapshot polling with no persisted recurring cursor
- explicit Gamma backfills use offset pagination only when `mode=backfill` is requested
- cursor-advancing workflows now scope checkpoints by owner key instead of sharing one global `(source, dataset)` cursor
- scheduler runs claim due schedules atomically and submit deterministic idempotency keys per schedule run window
- raw-first storage persistence with append-only JSONL batches stored in object storage
- DB-backed idempotency keys, retry scheduling, and dead-letter job states
- raw archive capture is in place; source-to-canonical transforms remain planned follow-on work
- FastAPI ingestion API plus dedicated worker and scheduler entrypoints, including admin list/redrive/run paths

## Local infrastructure

```bash
docker compose up -d postgres rabbitmq
```

## Initialize ingestion storage

```bash
poetry run python scripts/init_ingestion_store.py
```

This applies the Alembic migrations and ensures the raw object-store container exists.

## Run the ingestion stack in Docker Compose

```bash
docker compose up --build ingestion-api ingestion-worker ingestion-scheduler
```

This starts:

- `ingestion-init` once to run Alembic migrations and prepare raw storage
- `ingestion-api` on `http://127.0.0.1:8000`
- `ingestion-worker` as the RabbitMQ consumer
- `ingestion-scheduler` as a polling scheduler service

The scheduler service is intentionally simple: it polls PostgreSQL for due schedules and retry-ready jobs every `30` seconds by default, then republishes work to RabbitMQ. Override that interval with `POLY_ARB_INGESTION_SCHEDULER_INTERVAL_SECONDS`.

## Recurring production ingestion

Recurring Gamma schedules should use snapshot mode and should not carry `offset` or a recurring cursor:

```bash
curl -X POST http://127.0.0.1:8000/ingestion/schedules \
  -H 'content-type: application/json' \
  -d '{
    "name": "gamma-markets-snapshot",
    "source": "polymarket_gamma",
    "dataset": "markets",
    "cadence_seconds": 300,
    "params": {
      "limit": 100,
      "active": true,
      "closed": false,
      "mode": "snapshot"
    }
  }'
```

Each run archives a fresh raw market snapshot. Any downstream diffing or fan-out logic should operate on archived snapshots rather than a long-lived Gamma offset checkpoint.

## Explicit backfill ingestion

Use the CLI backfill mode only for manual offset-based pagination:

```bash
poetry run python scripts/ingest_polymarket.py \
  --source polymarket_gamma \
  --dataset markets \
  --limit 100 \
  --backfill \
  --offset 0
```

The default CLI path is snapshot mode. `--offset` is rejected unless `--backfill` is provided.

## Run the worker

```bash
poetry run python scripts/run_ingestion_worker.py
```

## Run the scheduler

```bash
poetry run python scripts/run_ingestion_scheduler.py
```

For long-running local orchestration, prefer the Docker Compose `ingestion-scheduler` service over repeatedly invoking the one-shot script.

## Run the API

```bash
poetry run python scripts/run_ingestion_api.py
```

## Environment

- `POLY_ARB_POSTGRES_DSN` defaults to `postgresql+psycopg://postgres:postgres@127.0.0.1:5432/poly_arbitrage`
- `POLY_ARB_RABBITMQ_URL` defaults to `amqp://guest:guest@127.0.0.1:5672/%2F`
- `POLY_ARB_RABBITMQ_DEAD_LETTER_EXCHANGE` defaults to `ingestion.dead_letter`
- `POLY_ARB_RABBITMQ_DEAD_LETTER_QUEUE` defaults to `ingestion.jobs.dead_letter`
- `POLY_ARB_INGESTION_MAX_ATTEMPTS` defaults to `3`
- `POLY_ARB_INGESTION_RETRY_BASE_DELAY` defaults to `30`
- `POLY_ARB_INGESTION_RETRY_MAX_DELAY` defaults to `300`
- `POLY_ARB_RAW_STORE_BACKEND` defaults to `local`
- `POLY_ARB_RAW_STORE_CONTAINER` defaults to `raw`
- `POLY_ARB_RAW_STORE_ROOT` defaults to `artifacts/datasets`
- `POLY_ARB_INGESTION_SCHEDULER_INTERVAL_SECONDS` defaults to `30` for the long-running scheduler service
- `POLY_ARB_INGESTION_SCHEDULER_LIMIT` defaults to `100` for each scheduler polling pass
- MinIO-backed raw storage uses `POLY_ARB_MINIO_ENDPOINT`, `POLY_ARB_MINIO_ACCESS_KEY`, and `POLY_ARB_MINIO_SECRET_KEY`

## Ingestion notes

- recurring Gamma schedules own their own checkpoint identity via schedule id, but snapshot-mode Gamma runs do not persist a recurring cursor
- manual backfills may provide a `checkpoint_key` through the API if they need isolated resumable state
- `polymarket_clob/book` and `polymarket_clob/midpoint` are detail snapshots keyed by `token_id`; they are operationally separate from Gamma market discovery
