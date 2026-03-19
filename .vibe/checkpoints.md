# Checkpoints

## Current Checkpoint
- Name: Provider-neutral raw archive boundary complete
- Date: 2026-03-19
- Status: raw payload persistence now runs through a provider-neutral object-store boundary with local and MinIO-backed adapters, durable local ingestion-state logs, and a simplified direct enqueue path that leaves connector resolution to the worker

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

## Next Checkpoint
- Name: Raw archive reader and exploratory profiling integrated
- Exit criteria:
  - archived raw Gamma and CLOB batches can be read back from the raw archive layer
  - exploratory profiling reports payload shapes, nullability, and unknown fields from persisted archives
  - raw-to-canonical mapping notes are documented from observed payloads
  - the user reviews and approves the raw archive slice
