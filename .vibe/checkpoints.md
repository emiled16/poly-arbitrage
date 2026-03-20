# Checkpoints

## Current Checkpoint
- Name: Ingestion contract hardening complete
- Date: 2026-03-19
- Status: ingestion now persists jobs, schedules, and owner-scoped checkpoints in PostgreSQL through SQLAlchemy tables, record stores, a CRUD routing registry, and domain repositories; Alembic manages schema creation; RabbitMQ delivers work through job IDs and broker dead-letter queues; retries are scheduled in the jobs table and re-enqueued by the scheduler; recurring `polymarket_gamma/markets` uses full snapshot polling with no persisted recurring cursor; explicit Gamma backfills use offset pagination only in `mode=backfill`; schedule submission claims due work atomically and uses deterministic idempotency keys; raw batches land in provider-neutral object storage; worker, scheduler, and API entrypoints share the same source-handler interface; and the runtime can now be launched as a Docker Compose stack with a dedicated long-running scheduler service

## Completed
- Read execution contract
- Read product specification
- Created initial `.vibe` planning workspace
- Drafted first-pass plan and system-design outline
- Completed the implementation-planning blueprint
- Created the initial repository scaffold required for development
- Implemented Polymarket Gamma market discovery and CLOB price snapshot integration
- Refactored ingestion around dispatcher, raw-sink, and state-store interfaces
- Separated Polymarket ELT normalization from raw ingestion connectors
- Added tests covering dispatcher flow, raw connectors, and normalization
- Added a provider-neutral raw archive boundary with object-store-backed JSONL persistence
- Added local filesystem and MinIO-backed object-store adapters
- Added durable local ingestion success and failure logs
- Added Docker Compose-based local MinIO bootstrap
- Removed the thin dispatcher layer and made the worker the single connector-resolution boundary
- Replaced the local-only ingestion path with a Postgres-backed state store and RabbitMQ-backed worker delivery model
- Added runtime entrypoints for ingestion API, scheduler, worker, and storage bootstrap
- Simplified persistence by removing the extra Postgres state-store layer in favor of repositories and a record-routing registry
- Added Alembic migrations, DB-level idempotency, retry/dead-letter job handling, and ingestion admin endpoints
- Replaced recurring Gamma watermark semantics with full snapshot polling and restricted offset pagination to explicit backfills
- Scoped cursor advancement by workflow owner keys and added compare-and-set checkpoint updates
- Made due-schedule claiming atomic and schedule-run submission deterministic
- Removed the in-tree Polymarket ELT package and its dedicated tests so canonical/refined transforms are tracked as planned work instead of stale code

## Next Checkpoint
- Name: Raw archive reader and exploratory profiling integrated
- Exit criteria:
  - archived raw Gamma and CLOB batches can be read back from the raw archive layer
  - exploratory profiling reports payload shapes, nullability, and unknown fields from persisted archives
  - raw-to-canonical mapping notes are documented from observed payloads
  - the user reviews and approves the raw archive slice
