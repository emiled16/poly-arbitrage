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
