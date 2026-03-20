# Key Decisions

## 2026-03-18

### Broaden v1 market scope beyond elections
Rationale:
The planning session established that the first release should cover broader political markets rather than limiting scope to election-only contracts.

### Approve the initial included and excluded political market families
Rationale:
The planning session narrowed v1 to broader but still bounded political coverage so schema and pipeline work can proceed without supporting every possible market type.

### Prefer official and public structured political sources for the first implementation
Rationale:
The initial source shortlist should prioritize stable official feeds and APIs for market truth, then layer broad discovery sources on top with lower trust weighting.

### Defer X from the default v1 source set
Rationale:
The current X developer platform is usage-priced, so it should not be treated as a default dependency before the product proves the value of that spend.

### Use owner-facing risk flags instead of reviewer gating in v1
Rationale:
The initial release targets a single owner, so a reviewer queue adds operational complexity without value. The system should surface risk explicitly while still showing all outputs to the owner.

### Keep v1 private and single-user
Rationale:
The current operating model is one user, so access, workflow, and UI assumptions should not pretend there is already a team moderation or review process.

### Treat v1 forecasting as binary classification
Rationale:
The core product output is the probability that a market resolves YES, so the primary predictive task is classification with calibrated probabilistic output. Ranking is a downstream optimization layer.

### Triage features into near-realtime and offline paths from the start
Rationale:
Fast-path updates and replay-safe training have different constraints. The feature design should make that split explicit early so low-latency inference does not compromise historical correctness.

### Make the first model baseline depend only on stable structured features
Rationale:
The initial system needs an end-to-end forecast path that is reproducible and debuggable before adding more speculative domain-specific or embedding-heavy features.

### Start with logistic regression and gradient-boosted trees as the first serious baselines
Rationale:
This gives one interpretable model and one stronger non-linear tabular benchmark while keeping the first training stack practical, standard, and easy to compare under replay.

### Keep live market price out of first-pass model inputs
Rationale:
The internal forecast is meant to stand on independently constructed evidence and features. Market price remains the external comparison baseline for opportunity scoring rather than a shortcut feature.

### Adopt a weighted ambiguity rubric for v1
Rationale:
Ambiguity affects ranking, risk flags, and model features. A fixed weighted rubric is simpler to audit and revise than free-form case-by-case judgment.

### Use tiered source reliability scoring
Rationale:
Broad political-source coverage is valuable, but the platform needs a consistent way to separate official signals from community noise while keeping all evidence auditable.

### Build local-first with a cloud-ready shape
Rationale:
The fastest path to a working vertical slice is local orchestration, but service boundaries, storage contracts, and deployment assumptions should not require a redesign before staging.

### Start implementation with raw ingestion and exploration before hardening schemas
Rationale:
Observed payload shape, nullability, drift, and update cadence will materially affect the canonical schema and ELT design. Capturing raw data first reduces the risk of overfitting the schema to the spec instead of the real source.

### Adopt v1 as research and alerting only
Rationale:
The product spec explicitly excludes live trade execution and keeps future scope limited to paper trading compatibility.

### Treat replay correctness as a first-class requirement
Rationale:
The spec requires strict point-in-time backtesting from day one, so schema, storage, and workflow design must preserve historical correctness.

### Keep the first implementation Python-first
Rationale:
The spec allows Go/Rust for performance-sensitive components, but the planning baseline should optimize for delivery speed and architectural clarity until profiling proves otherwise.

### Use market price as an external baseline only
Rationale:
The spec explicitly excludes Polymarket price from v1 model inputs and uses it only for comparison and opportunity scoring.

### Use dependency-light stdlib HTTP clients for the first ingestion slice
Rationale:
The local repository did not yet have the planned `poetry` environment or third-party packages installed. Using `urllib` for the first Polymarket clients kept the initial ingestion task shippable and testable without blocking on environment bootstrap, while still leaving room to swap in `httpx` later if needed.

### Keep ingestion raw and move normalization into ELT
Rationale:
The system design already prioritizes landing raw payloads before canonicalization. Keeping normalization out of ingestion preserves replay fidelity, reduces coupling to source-specific assumptions, and lets Spark own source-stage and canonical transformations cleanly.

### Adopt a dispatcher pattern for source ingestion
Rationale:
Multiple sources will need a shared ingestion contract without collapsing their source-specific fetch behavior into one service. A dispatcher plus connector interface keeps queue execution, storage, retries, and source logic decoupled while preserving a uniform operational path.

### Organize ingestion code by entity-oriented packages instead of flat modules
Rationale:
The raw-ingestion boundary introduced enough concepts that a flat package became harder to scan. Grouping code by entity and responsibility makes it easier to navigate workers, queues, sinks, state stores, source connectors, and factories without mixing unrelated concerns in the same files.

### Mirror the same entity-oriented organization on the ELT side
Rationale:
Keeping ingestion and ELT structurally similar reduces navigation cost and makes the raw-to-refined boundary clearer. Models, parsers, source normalizers, and builders each serve distinct roles and are easier to reason about when they are not collapsed into a couple of large files.

### Separate Polymarket transport protocol, errors, and HTTP implementation
Rationale:
The source transport layer should follow the same separation of concerns as the rest of the package. Keeping the HTTP protocol, source-specific exceptions, and urllib implementation in distinct modules reduces mixed responsibilities and makes it easier to swap transports later without moving unrelated code.

## 2026-03-19

### Put raw payload bodies behind a provider-neutral object-store boundary
Rationale:
Raw payload storage needs to support local development on MinIO today while preserving a clean migration path to AWS S3 and future GCS support. The application boundary should talk in terms of containers, object keys, and storage URIs rather than MinIO- or S3-specific client details.

### Use MinIO as the first local raw-object-store backend
Rationale:
MinIO gives the project a concrete local object-store target that is operationally close to AWS S3 without forcing cloud infrastructure into the first implementation slice. It also keeps local replay and archive inspection aligned with the eventual production storage shape.

### Persist ingestion manifests and failures outside process memory
Rationale:
Raw object persistence alone is not sufficient for replay or operational debugging if job results disappear when the process exits. Even before the full database layer is in place, local durable state logs provide traceability across runs and make the raw archive materially more useful.

### De-emphasize the dispatcher layer and let the worker own connector resolution
Rationale:
The current dispatcher had become a thin validation-and-enqueue wrapper that duplicated connector knowledge already required by the worker. Removing that validation stage keeps queue admission simpler, makes execution-time failures flow through one consistent boundary, and better respects single responsibility.

Caveat:
A separate admission or routing layer may still be justified later if ingestion requests need fan-out, deduplication, prioritization, recurring scheduling, or rate-limit-aware routing. If that happens, it should be reintroduced for those explicit responsibilities rather than as a thin queue wrapper.

### Make PostgreSQL the source of truth and RabbitMQ delivery-only for ingestion
Rationale:
The earlier in-memory queue shape blurred state and transport. PostgreSQL should own durable job state, schedules, cursors, and completion metadata, while RabbitMQ should only deliver work to consumers. That separation keeps retries, auditing, and operator visibility out of broker-specific message state and makes the queue disposable.

### Collapse the ingestion runtime around a small set of strong modules
Rationale:
The previous ingestion package had too many tiny abstractions for a flow that still ran in one local process. Consolidating the runtime around `contracts.py`, `service.py`, `scheduler.py`, `runtime.py`, and a small number of source and adapter modules keeps the system organized without making navigation cumbersome.

### Separate SQLAlchemy schema and record persistence from ingestion state semantics
Rationale:
The Postgres state store should not also own table declarations and raw SQL updates. Table definitions belong in a dedicated database layer, and SQLAlchemy-backed record stores should manage persisted rows for jobs, cursors, and schedules. That keeps `state/postgres.py` focused on translating ingestion-domain actions into persisted record changes instead of mixing storage schema with state semantics.

### Remove the extra Postgres state-store layer and let use cases depend on repositories directly
Rationale:
The intermediate state-store adapter added another hop without adding meaningful behavior. Job execution, schedule enqueueing, and API handlers are easier to follow when they depend directly on `JobRepository`, `CursorRepository`, and `ScheduleRepository`, while SQLAlchemy-facing record stores remain isolated behind a small CRUD routing registry.

### Keep one thin CRUD routing registry for persisted record classes
Rationale:
Simple save and delete flows should not require each repository to hand-wire every record store call. A small registry that routes `IngestionJobRecord`, `IngestionCursorRecord`, and `IngestionScheduleRecord` by class keeps standard CRUD concise, while complex reads still live on explicit repositories where the domain behavior is visible.

### Schedule retries in PostgreSQL instead of relying on delayed broker features
Rationale:
Retry eligibility is part of job state, not message transport. Persisting retry timing in the jobs table keeps retry behavior auditable, makes it easy to inspect pending retries through admin queries, and avoids coupling correctness to RabbitMQ-specific delayed-delivery plugins.

### Use idempotency keys at the job-record boundary
Rationale:
Duplicate ingestion submissions should be prevented where jobs are persisted, not only in API or CLI callers. A unique database constraint on `(source, dataset, idempotency_key)` plus repository lookup-on-create keeps submission behavior deterministic across entrypoints and protects against accidental duplicate writes.

### Let each source own its checkpoint format and semantics
Rationale:
An ingestion cursor is only meaningful if the source handler actually interprets it. Gamma market ingestion now owns a source-specific cursor format based on `updatedAt` and `id`, with `offset` retained only as transient sweep state inside a watermark-driven fetch cycle. That keeps checkpoint logic close to the API behavior it depends on and avoids pretending that a generic cursor string can be source-agnostic.

Caveat:
A single persisted cursor per `(source, dataset)` should be treated as a serialized checkpoint, not as a coordination primitive for concurrent workers. If the system later runs multiple in-flight jobs that can advance the same checkpoint, it will need explicit protection against lost updates, such as one active cursor-advancing pipeline per source/dataset, compare-and-set cursor writes, or explicit work partitioning by shard/range.

### Treat schedule-level cursors as bootstrap seeds, not persistent overrides
Rationale:
A schedule definition should not permanently outrank the latest persisted checkpoint, or forward progress can stall indefinitely. Renaming the schedule field to `bootstrap_cursor` makes its purpose explicit and lets normal recurring runs prefer the repository-backed cursor state after the first successful fetch.

### Use a dedicated polling scheduler service for the composed local stack
Rationale:
The current ingestion runtime already persists schedule cadence and retry timing in PostgreSQL, so the missing piece is only a long-running trigger loop. A small scheduler container that calls `enqueue_due_work()` every N seconds keeps scheduling logic inside the application boundary, avoids pulling in Airflow or Dagster before there is multi-step workflow complexity, and is simpler than layering OS cron into a containerized local stack.

Caveat:
If the system later needs calendar-aware workflows, task fan-out across heterogeneous pipelines, dependency graphs, or operator-managed backfills, an external orchestrator can still be added on top. For the current ingestion runtime, that would be a scale-up in operational scope rather than a correction to the scheduling model.

### Use full snapshot polling for recurring `polymarket_gamma/markets`
Rationale:
Recurring Gamma polling should have one obvious production behavior. Full snapshot polling avoids the unsafe combination of persisted offset pagination plus a live descending feed and keeps market discovery semantics easy to reason about. Raw snapshot diffs belong downstream of archive storage, not inside the recurring checkpoint model.

### Restrict Gamma offset pagination to explicit backfill mode
Rationale:
Offset-based pagination is still useful for manual archive sweeps, but it should not be the default or an accidental side effect of normal job submission. Making backfill mode explicit in the CLI and API removes ambiguity and prevents recurring schedules from drifting into legacy behavior.

### Scope checkpoints by workflow owner
Rationale:
One cursor row per `(source, dataset)` was not sufficient once multiple schedules or manual backfills could coexist. Checkpoints now belong to an explicit owner key, with recurring schedules deriving that owner from `schedule_id`, so independent workflows no longer overwrite each other's progress.

### Use compare-and-set cursor advancement
Rationale:
If two jobs try to advance the same owner-scoped checkpoint from different starting states, the later stale write must fail instead of silently overwriting newer progress. Compare-and-set keeps checkpoint advancement safe without requiring a heavyweight distributed lock manager in this slice.

### Claim due schedules atomically and submit deterministic idempotency keys
Rationale:
Selecting due schedules with a plain read then updating them later made duplicate enqueueing too easy. Atomic claiming closes that race, and deterministic idempotency keys derived from schedule identity plus due time ensure duplicate submission attempts collapse safely if they still happen.

### Keep market discovery separate from token detail snapshots
Rationale:
Gamma market discovery, order-book snapshots, and midpoint snapshots are operationally different datasets. Discovery should own discovery cadence and archive capture only, while `book` and `midpoint` remain separate token-scoped detail jobs rather than sharing the discovery checkpoint model.

### Remove the in-tree Polymarket ELT package until canonical transforms are ready to be owned properly
Rationale:
The repository now has a production-oriented ingestion runtime, but the old ELT code was an isolated normalization slice that no longer matched the active ingestion direction and was not part of the current operational path. Removing it reduces dead surface area and makes it explicit that raw-to-canonical work is still planned follow-on work rather than a supported in-repo subsystem.
