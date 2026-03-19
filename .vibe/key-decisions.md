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
