# Implementation Plan

## Version History
- v0.1.0 | 2026-03-18 | Initial planning baseline created from `AGENTS.md` and `polymarket_research_platform_spec.md`
- v0.1.1 | 2026-03-18 | Updated v1 scope to cover broader political markets, not elections only
- v0.1.2 | 2026-03-18 | Replaced reviewer workflow with single-user owner-facing risk flags for v1
- v0.1.3 | 2026-03-18 | Locked first-pass forecasting direction to binary classification with downstream ranking
- v0.1.4 | 2026-03-18 | Added explicit triage between near-realtime and offline feature groups
- v0.1.5 | 2026-03-18 | Defined the first model baseline stack and stable feature subset
- v0.1.6 | 2026-03-18 | Completed the implementation blueprint with ambiguity, reliability, agent, API, and infra planning
- v0.1.7 | 2026-03-18 | Reordered early execution around raw ingestion, dataset exploration, and schema/ELT refinement
- v0.1.8 | 2026-03-18 | Completed the first Polymarket ingestion implementation slice with Gamma and CLOB clients plus tests
- v0.1.9 | 2026-03-18 | Refactored ingestion around a raw dispatcher boundary and moved Polymarket normalization into a separate ELT module
- v0.1.10 | 2026-03-19 | Reorganized ingestion into entity-based packages for models, protocols, workers, queues, sinks, state stores, and source connectors
- v0.1.11 | 2026-03-19 | Reorganized Polymarket ELT into entity-based packages for models, parsers, normalizers, and builders
- v0.1.12 | 2026-03-19 | Split Polymarket HTTP concerns into dedicated protocol, error, and urllib transport modules

## Current Status
- Phase: Development session
- Overall status: first market-ingestion task completed and refactored to a raw-ingestion boundary for user review
- Blocking items: local `poetry` and `ruff` toolchain setup is still pending

## Planning Assumptions
- v1 is a private single-user research and alerting platform only
- v1 market scope is Polymarket broader political markets, including but not limited to elections
- strict point-in-time replay is a hard requirement from day one
- initial backend stack is Python + FastAPI + PostgreSQL
- initial frontend stack is Next.js
- mixed-language optimization is deferred until profiling justifies it

## Early Execution Strategy
- ingest source data and store it raw before committing too hard to refined schemas
- use observed payloads and update patterns to refine canonical tables, ELT logic, and feature definitions
- keep raw archives immutable enough to support replay and later reprocessing
- treat early canonical schema and ELT design as informed by sampled real data, not just spec assumptions

## Approved v1 Scope
- Include: elections and nominations
- Include: legislative control and major leadership races
- Include: cabinet appointments and confirmations
- Include: major court and regulatory decisions with clear political resolution criteria
- Include: high-salience geopolitical politics markets
- Exclude: purely local or municipal politics
- Exclude: vague opinion or sentiment markets
- Exclude: markets with highly subjective or unstable resolution wording
- Exclude: non-political markets

## Feature Roadmap

### F1. Project foundations
Status: in progress

Tasks:
- [done] Read execution contract and product spec
- [done] Establish `.vibe` planning workspace
- [done] Create initial repository skeleton aligned to `AGENTS.md`
- [todo] Define local development workflow with `poetry`, `pytest`, `ruff`, Docker, and env management
- [todo] Define release and CI expectations

### F2. Domain and data model
Status: in progress

Tasks:
- [done] Finalize v1 political subdomains and explicit exclusions
- [todo] Convert market, snapshot, entity, rule, evidence, claim, and research-run objects into SQL-ready schema after validating raw payload shapes
- [todo] Define versioning strategy for prompts, retrieval, features, forecasts, and reports
- [done] Define ambiguity scoring rubric and owner-facing risk-flag triggers
- [done] Define source reliability model and provenance requirements
- [todo] Refine canonical schema from observed raw source payloads and exploratory profiling

### F3. Market ingestion and storage
Status: in progress

Tasks:
- [done] Integrate Polymarket market and price ingestion
- [todo] Persist raw Polymarket payloads and source snapshots before heavy normalization
- [todo] Build exploratory profiling on raw payload shapes, nullability, and update frequency
- [todo] Refine canonical market records and time-series snapshots from the raw dataset
- [todo] Archive raw payloads for replay and reprocessing
- [todo] Define ingestion idempotency and retry rules
- [todo] Define freshness SLAs and lag monitoring

### F3a. Raw data exploration and ELT refinement
Status: todo

Tasks:
- [todo] Sample and inspect real market metadata, price, and rules payloads
- [todo] Document raw-to-canonical mappings and unknown fields
- [todo] Define bronze/silver-style ELT stages or equivalent raw/refined layers
- [todo] Identify schema drift risks and payload versioning strategy
- [todo] Use exploratory findings to refine downstream evidence and feature contracts

### F4. Retrieval and evidence substrate
Status: in progress

Tasks:
- [in-progress] Select first-pass source providers and legal/operational constraints
- [todo] Design raw artifact storage layout and metadata schema
- [todo] Implement evidence extraction contracts
- [todo] Model claim graph and contradiction tracking
- [todo] Define replay-safe retrieval behavior

## Proposed v1 Source Provider Shortlist

### Ship in first implementation
- Polymarket Gamma API for market discovery and metadata
- Polymarket CLOB public endpoints for prices, order book context, and price history
- GovInfo API, bulk data, and RSS for official Federal Register, Congressional Record, presidential, and other federal documents
- Congress.gov API for bill, member, and congressional activity metadata
- OpenFEC API plus FEC bulk/download surfaces for campaign finance and filing data
- Official campaign, government, court, and agency RSS or sitemap feeds where directly available
- GDELT DOC 2.0 as a broad news discovery layer, not a source-of-truth layer

### Add after the core substrate is stable
- YouTube Data API for political channel/video discovery and metadata collection
- Reddit API for read-only community signal gathering with strict provenance and low trust weighting
- AP Elections API as an optional paid add-on for election-night and delegate data

### Defer from default v1
- X API, unless a concrete paid-access budget and use case is approved
- Broad podcast ingestion beyond feeds or transcripts already exposed through supported providers
- Site-specific scraping that lacks clear operational or legal confidence

### F5. Multi-agent research workflow
Status: in progress

Tasks:
- [done] Define agent input/output contracts for parser, planner, retrieval, extractor, skeptic, hypothesis, forecaster, calibration, opportunity, and report agents
- [done] Define LangGraph state shape and transition rules
- [todo] Define prompt/version registry and audit trail format
- [todo] Define failure handling, retries, and partial-result persistence

## Proposed v1 Owner-Facing Risk Policy

### Default visibility mode
- all reports and opportunity records are visible to the owner by default
- every output retains full provenance, version references, and research-run trace data

### Risk-flag triggers
- ambiguity score above the configured threshold
- resolution rules mention edge cases, exceptions, or multi-condition outcomes that the parser cannot normalize confidently
- evidence set is dominated by low-trust or noisy sources
- skeptic output identifies a major unresolved contradiction
- forecast confidence is low or model disagreement exceeds threshold
- major market-moving event is detected but official confirmation is missing
- market family is newly introduced and not yet on the unattended allowlist

### Visibility outcomes
- `normal`
- `warning`
- `deemphasized`

### UI behavior
- all markets remain visible to the owner
- warning and deemphasized markets show explicit risk badges and rationale
- deemphasized markets rank lower in the main feed by default but remain searchable and inspectable
- there is no reviewer identity, review queue, or approval state in v1

### Operational recommendation for v1
- use automatic owner-facing publication only
- attach structured risk reasons to every non-normal output
- defer reviewer workflows until a real multi-user operating model exists

### F6. Feature store and forecasting
Status: in progress

Tasks:
- [in-progress] Define offline and near-realtime feature groups
- [todo] Choose initial feature-store pattern
- [done] Define first benchmark models and baselines
- [todo] Implement point-in-time feature generation strategy
- [todo] Define forecast calibration, confidence, and evaluation outputs

## First-Pass Forecasting Direction
- the primary forecasting task is binary classification for `P(YES resolves)`
- forecast models must emit probabilistic outputs, not just hard labels
- calibration is required before opportunity scoring
- opportunity ranking is downstream from classification and is not the primary predictive task in v1
- live Polymarket price remains a comparison baseline, not a training feature

## First Model Baseline Stack

### B0. Sanity baseline
- type: constant-probability classifier
- purpose: verify the training and replay pipeline against a trivial benchmark
- output: cohort-level base-rate probability for the relevant training slice

### B1. Interpretable baseline
- type: regularized logistic regression classifier
- purpose: first serious forecast model with transparent coefficients and debuggable behavior
- feature policy: stable structured features only

### B2. Stronger tabular baseline
- type: gradient-boosted tree classifier
- purpose: capture non-linear interactions that logistic regression misses
- feature policy: same stable feature subset as B1 in the first pass

### Calibration layer
- compare Platt scaling and isotonic regression on top of B1 and B2
- choose the calibration method by replay performance, not preference
- only calibrated probabilities flow into opportunity scoring

### Selection rule for v1
- always keep B0, B1, and B2 in evaluation
- prefer B1 as the first default production model unless B2 shows a clear calibrated advantage
- allow B2 to become default only if it improves replay metrics without materially degrading stability or debuggability

## Feature Triage Direction

### Near-realtime features
- cheap to recompute on market updates or new evidence arrival
- required for fast-path refreshes
- stored in a low-latency serving layer and versioned by observation time
- examples: recent price moves, latest source-mix counts, contradiction deltas, freshness signals

### Offline features
- expensive or history-dependent features built with point-in-time joins
- required for training, replay, and slower deep-refresh inference
- stored in reproducible batch tables or parquet-style datasets
- examples: long-window market trajectories, entity history, source reliability aggregates, event-distance features

### Planning rule
- every candidate feature must be classified as `near_realtime`, `offline`, or `derived_from_both`
- no feature should exist only in ad hoc notebook logic
- replay correctness takes precedence over convenience when deciding feature placement

## First-Pass Feature Catalog

### Stable near-realtime features for v1
- `rt_price_yes_last`: latest YES price from the newest market snapshot
- `rt_price_return_1h`: short-window YES price return over the last hour
- `rt_price_return_24h`: short-window YES price return over the last 24 hours
- `rt_price_volatility_24h`: realized short-window volatility from recent snapshots
- `rt_spread_latest`: latest bid/ask spread metadata for context and possible quality flags
- `rt_snapshot_age_seconds`: time since the latest market snapshot
- `rt_evidence_count_6h_high_trust`: count of high-trust evidence items arriving in the last 6 hours
- `rt_evidence_count_24h_all`: count of all evidence items arriving in the last 24 hours
- `rt_source_mix_low_trust_share_24h`: share of recent evidence attributed to low-trust sources
- `rt_contradiction_score_latest`: most recent contradiction burden from skeptic and evidence outputs
- `rt_time_since_last_deep_refresh`: freshness measure for the last deep research run

### Stable offline features for v1
- `of_market_duration_days`: time between market open and expected resolution
- `of_days_to_resolution`: point-in-time remaining days until expected resolution
- `of_market_type_one_hot`: encoded market family and subcategory
- `of_rules_length_chars`: proxy for rule complexity
- `of_ambiguity_score`: parser-derived ambiguity score
- `of_entity_count`: number of recognized entities linked to the market
- `of_entity_role_pattern`: encoded role pattern such as candidate-vs-candidate or nominee-vs-confirmation
- `of_long_return_7d`: 7-day market return built with replay-safe joins
- `of_long_volatility_30d`: 30-day realized volatility
- `of_source_reliability_mean_30d`: average reliability of evidence used in the lookback window
- `of_source_diversity_30d`: diversity of source families represented in evidence
- `of_contradiction_density_30d`: contradiction rate over the lookback window
- `of_evidence_recency_weighted_30d`: recency-weighted evidence intensity
- `of_event_calendar_distance`: days to or from a known relevant event date

### Provisional offline features for v1
- `of_entity_history_prior`: historical prior derived from similar entities or cohorts
- `of_polling_signal_summary`: polling-derived summary when the market class supports it
- `of_fec_activity_intensity`: fundraising or filing intensity for eligible election-related markets
- `of_legislative_activity_intensity`: bill or vote activity intensity for legislative markets
- `of_official_document_burst`: burstiness of official document issuance for relevant markets

### Derived-from-both features for v1
- `db_price_move_vs_30d_regime`: near-realtime price move normalized by historical volatility regime
- `db_recent_evidence_burst_vs_baseline`: current evidence arrival rate compared with historical norm
- `db_contradiction_vs_history`: current contradiction burden relative to historical contradiction density
- `db_snapshot_staleness_adjusted_confidence`: confidence adjustment using current freshness and historical update cadence

### Deferred features
- free-form embedding-heavy features as core model inputs
- graph neural or deep sequence features
- cross-platform social virality features that depend on deferred providers
- features that require unresolved legal or scraping assumptions

### Catalog rules
- every feature needs an owning raw input set and an explicit point-in-time definition
- provisional features can exist in the catalog before implementation, but they cannot block the first model baseline
- v1 model baselines should run with the stable feature subset even if provisional features are absent

## Stable Feature Subset For First Baselines
- `rt_price_return_1h`
- `rt_price_return_24h`
- `rt_price_volatility_24h`
- `rt_snapshot_age_seconds`
- `rt_evidence_count_6h_high_trust`
- `rt_evidence_count_24h_all`
- `rt_source_mix_low_trust_share_24h`
- `rt_contradiction_score_latest`
- `rt_time_since_last_deep_refresh`
- `of_market_duration_days`
- `of_days_to_resolution`
- `of_market_type_one_hot`
- `of_rules_length_chars`
- `of_ambiguity_score`
- `of_entity_count`
- `of_entity_role_pattern`
- `of_long_return_7d`
- `of_long_volatility_30d`
- `of_source_diversity_30d`
- `of_contradiction_density_30d`
- `of_evidence_recency_weighted_30d`
- `of_event_calendar_distance`
- `db_price_move_vs_30d_regime`
- `db_recent_evidence_burst_vs_baseline`
- `db_contradiction_vs_history`

## Features Excluded From First Baselines
- live market probability or price as a direct model input
- provisional polling, FEC, legislative, or official-document burst features
- liquidity and spread as predictive features in the first pass
- embedding-heavy and graph-neural features

## Baseline Evaluation Rules
- evaluate B0, B1, and B2 with strict point-in-time replay only
- primary metrics: Brier score, log loss, expected calibration error
- secondary metrics: reliability by market family and horizon, stability through time
- compare calibrated and uncalibrated variants separately
- store model version, feature version, and calibration version for every run

## Ambiguity Scoring Rubric

### Score range
- `0.00` to `1.00`
- higher means harder to interpret or resolve safely

### Component weights
- `0.25` resolution authority clarity
- `0.20` deadline and timing clarity
- `0.20` term-definition clarity
- `0.15` conditional-branch complexity
- `0.10` edge-case exposure
- `0.10` parser confidence penalty

### Rubric bands
- `0.00` to `0.19`: clear
- `0.20` to `0.39`: mild ambiguity
- `0.40` to `0.59`: material ambiguity
- `0.60` to `0.79`: high ambiguity
- `0.80` to `1.00`: severe ambiguity

### Policy effects
- `0.40+`: warning badge and ranking penalty
- `0.60+`: `needs_attention = true`
- `0.80+`: default `deemphasized` visibility

## Source Reliability Framework

### Reliability tiers
- `tier_1_official`
- `tier_2_institutional`
- `tier_3_aggregated`
- `tier_4_community`
- `tier_5_unverified`

### Suggested priors
- `tier_1_official = 0.90`
- `tier_2_institutional = 0.75`
- `tier_3_aggregated = 0.55`
- `tier_4_community = 0.35`
- `tier_5_unverified = 0.15`

### Score adjustments
- attribution quality
- document type
- recency relative to claim time
- corroboration from stronger sources
- contradiction from stronger sources

### Policy effects
- weak-source dominance increases attention level
- higher-tier contradiction outweighs lower-tier support
- all source material remains visible for audit even when reliability is low

## Deployment Direction
- local-first for the first delivery
- cloud-ready service boundaries and storage contracts
- Docker Compose for local orchestration
- no Kubernetes or managed-service dependency before the local vertical slice works

## Blueprint Completion Notes
- the planning blueprint is complete enough to begin repository scaffolding and migration-ready schema work
- remaining unknowns are implementation details, not blocking product-definition gaps

## Data-First Implementation Notes
- the first implementation slice should favor raw capture and reprocessable storage over premature canonicalization
- canonical schemas should stabilize only after inspecting real Polymarket payloads and observed update behavior
- ELT refinement should happen before downstream feature pipelines hard-code assumptions about field shape or data completeness

### F7. Opportunity engine
Status: todo

Tasks:
- [todo] Finalize EV-style formula and cost assumptions
- [todo] Define ranking score composition
- [todo] Define penalties for ambiguity, contradiction burden, and low evidence completeness
- [todo] Specify ranking refresh behavior for fast-path and deep-refresh updates

### F8. Product APIs and UI
Status: in progress

Tasks:
- [done] Convert market, opportunity, research, backtesting, and admin API ideas into endpoint contracts
- [todo] Define ranked dashboard information hierarchy
- [todo] Define market detail, report, and evidence explorer page contracts
- [todo] Define private single-user access patterns and future-compatible auth expansion

### F9. Replay, evaluation, and observability
Status: in progress

Tasks:
- [todo] Define replay engine inputs, outputs, and storage contracts
- [todo] Define offline evaluation reports and dashboards
- [done] Define structured logging, tracing, metrics, and alerting model
- [todo] Define success criteria for quality, latency, and auditability

## Execution Sequence
1. Foundations and raw ingestion scaffolding
2. Raw data capture, archive, and exploratory profiling
3. Canonical schema and ELT refinement from observed payloads
4. Retrieval and evidence layer
5. Agent graph and report generation
6. Feature store and forecasting
7. Opportunity ranking
8. APIs, UI, and real-time hardening

## Draft Milestones
- M1: Architecture blueprint + raw ingestion plan approved
- M2: Raw ingestion + replay archive + exploratory dataset working locally
- M3: Canonical schema + ELT refinement working from real payloads
- M4: Evidence pipeline + first research report path working
- M5: First forecast pipeline + evaluation harness working
- M6: Ranked opportunities dashboard + real-time hardening readiness

## Milestone Acceptance Criteria

### M1. Architecture blueprint + raw ingestion plan approved
- v1 market scope explicitly documented
- service boundaries and event flow documented
- raw ingestion and archive strategy documented
- milestone backlog accepted for implementation

### M2. Raw ingestion + replay archive + exploratory dataset working locally
- Polymarket market metadata and snapshot payloads are captured raw
- raw source payloads are archived for replay and reprocessing
- exploratory profiling exists for payload shape, nullability, and update frequency
- ingestion jobs are idempotent and observable locally

### M3. Canonical schema + ELT refinement working from real payloads
- raw-to-canonical mappings are documented
- canonical market and snapshot tables are implemented from observed payloads
- ELT layers or equivalent raw/refined transforms are working locally
- schema drift handling is defined for ingestion changes

### M4. Evidence pipeline + first research report path working
- retrieval pipeline stores raw artifacts and metadata
- evidence extraction creates evidence items and claims linked to markets
- skeptic stage produces contradiction output
- report generation produces a structured market report payload

### M5. First forecast pipeline + evaluation harness working
- offline and near-realtime feature definitions exist for first-pass model inputs
- at least one interpretable baseline and one ML baseline run end to end
- calibrated internal probabilities are stored with version references
- replay evaluation produces Brier, log loss, and calibration outputs

### M6. Ranked opportunities dashboard + real-time hardening readiness
- opportunity records are computed from internal probabilities and live market baseline
- APIs expose market, report, evidence, and opportunity views
- dashboard, market detail, and report pages render against live backend data
- access is private to the owner in v1
- fast-path and deep-refresh workflows are separated
- queueing and retry semantics are implemented for continuous operation
- metrics, logs, and traces cover ingestion, research, and forecasting flows
- staging deployment path is defined and tested

## Open Decisions Requiring Review
- no blocking planning decisions remain; review can focus on adjustments rather than missing blueprint sections
