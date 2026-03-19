# System Design

## Functional Requirements
- ingest and track Polymarket broader political markets continuously
- maintain point-in-time market and evidence history
- run an auditable multi-agent research workflow per market
- generate internal probability estimates and opportunity rankings
- expose reports, evidence, research traces, and historical evaluation through APIs and UI

## Forecasting Task Definition
- primary prediction task: binary classification
- prediction target: probability that a market resolves `YES`
- required output: calibrated probability estimate plus uncertainty metadata
- downstream use: opportunity ranking combines calibrated probabilities with EV and risk adjustments

## First Model Baseline Stack

### `B0_constant_rate`
- classifier type: constant-probability baseline
- role: pipeline sanity check and lower-bound benchmark
- feature usage: none

### `B1_logistic_regression`
- classifier type: regularized logistic regression
- role: interpretable default baseline
- feature usage: stable structured feature subset only

### `B2_gradient_boosted_trees`
- classifier type: gradient-boosted tree classifier
- role: non-linear tabular benchmark
- feature usage: same stable subset initially, with later controlled expansion

### Calibration
- calibration candidates: Platt scaling, isotonic regression
- calibration evaluation: replay-based only
- deployment rule: calibrated model outputs are the only probabilities exposed downstream

## Feature Triage Model

### Near-realtime features
- recomputed on price updates, new evidence arrival, or scheduled freshness checks
- available to fast-path inference and ranking updates
- stored in a low-latency online serving layer

### Offline features
- built with replay-safe historical joins and larger lookback windows
- used for training, backtesting, and deep-refresh inference
- stored in warehouse-style tables or parquet datasets

### Derived-from-both features
- computed by combining offline historical context with near-realtime deltas at inference time
- require explicit version lineage across both inputs

## v1 Domain Scope

### Included market families
- elections and nominations
- legislative control and major leadership races
- cabinet appointments and confirmations
- major court and regulatory decisions with clear political resolution criteria
- high-salience geopolitical politics markets

### Excluded market families
- purely local or municipal politics
- vague opinion or sentiment markets
- markets with highly subjective or unstable resolution wording
- non-political markets

## Non-Functional Requirements
- strict replay correctness
- explicit versioning and auditability
- support for private single-user access in v1
- modular services with room for later performance optimization
- observability for ingestion lag, stale markets, and workflow failures

## High-Level Architecture
- ingestion service
- canonical API/backend service
- retrieval and evidence service
- agent orchestration service
- forecasting service
- ranking service
- replay/backtest worker
- frontend service

## Deployment Direction
- local-first implementation
- cloud-ready service boundaries and storage contracts
- Docker Compose for local orchestration
- MinIO for the first local raw-object-store deployment
- staging and managed infrastructure after the local vertical slice proves the shape

## Data Handling Strategy
- land raw source payloads first
- separate raw archive storage from refined canonical tables
- treat canonical schema as downstream of observed payload profiling
- preserve enough raw context to support replay, reprocessing, and schema evolution
- keep raw storage behind a provider-neutral object-store interface so local MinIO, AWS S3, and later GCS backends can share the same ingestion boundary

## Recommended External Source Shortlist

### Tier 0: must-have for first implementation
- Polymarket Gamma API for market discovery, metadata, search, and tagging
- Polymarket CLOB public endpoints for price, midpoint, spread, and order book context
- GovInfo API plus bulk data and RSS for official federal documents
- Congress.gov API for legislative entities and activity
- OpenFEC API plus FEC bulk/download data for campaign-finance signals
- Official RSS and sitemap feeds from campaigns, agencies, courts, and government offices

### Tier 1: broad discovery and enrichment
- GDELT DOC 2.0 for broad news discovery and query fan-out
- YouTube Data API for political video/channel metadata and search
- Reddit API for community discussion retrieval

### Tier 2: optional paid enrichment
- AP Elections API for election-night results, turnout, and delegate data

### Deferred by default
- X API unless budgeted and explicitly approved
- unsupported scraping-dependent providers

## Core Entities
- market
- market_snapshot
- market_entity
- resolution_rule
- raw_source_artifact
- evidence_item
- claim
- evidence_graph_edge
- research_run
- forecast_output
- opportunity_record

## Draft Data Flow
1. ingest market metadata and price updates from Polymarket
2. persist raw payloads and raw source snapshots
3. profile raw data and refine raw-to-canonical mappings
4. persist canonical market state and historical snapshots
5. trigger fast-path or deep-refresh workflows based on event type
6. retrieve and archive source artifacts
7. extract evidence and claims linked to the market
8. run hypothesis, forecasting, calibration, and ranking stages
9. generate report payloads and serve updated UI/API views
10. store all outputs with version references for replay

## Event Flow
1. `market.discovered` creates or updates the canonical market record
2. `market.snapshot.recorded` appends a point-in-time price snapshot
3. a routing rule emits either `market.fast_refresh.requested` or `market.deep_refresh.requested`
4. deep refresh rebuilds offline-dependent features, then runs retrieval, extraction, skepticism, hypothesis, forecast, calibration, ranking, and report generation
5. risk policy evaluates attention triggers and assigns `normal`, `warning`, or `deemphasized`
6. fast refresh skips retrieval-heavy stages and refreshes near-realtime features, forecast, ranking, and report summary fields
7. every workflow writes versioned outputs keyed by market and research run
8. replay mode reconstructs the same flow constrained to artifacts and snapshots available at time `T`

## Agent Graph State Contract
- `market_context`: canonical market fields, parsed rules, entity map, latest snapshots
- `research_context`: source plan, query plan, retrieval metadata, evidence checklist
- `evidence_context`: artifacts, evidence items, claims, contradiction tags, reliability summaries
- `forecast_context`: feature values, model outputs, calibration outputs, uncertainty payloads
- `presentation_context`: report payloads, visibility decision, risk reasons, opportunity output

## Agent Input And Output Contracts

### Market Parser Agent
- inputs: raw market metadata, rules text, resolution source text
- outputs: parsed market object, entity map, parsed conditions, parser confidence, ambiguity notes

### Research Planner Agent
- inputs: parsed market object, entity map, ambiguity notes
- outputs: source families, query set, evidence checklist, contradiction checklist

### Retrieval Agent
- inputs: source plan, query plan, replay timestamp if applicable
- outputs: raw artifacts, retrieval metadata, source coverage summary

### Evidence Extractor Agent
- inputs: raw artifacts, parsed market object
- outputs: evidence items, claims, source-level summaries, stance signals

### Skeptic Agent
- inputs: evidence items, claims, parsed rules
- outputs: contradiction memo, fragility list, missing-assumption list, contradiction score

### Hypothesis Builder Agent
- inputs: evidence items, claims, skeptic memo
- outputs: hypothesis set, scenario tree, modeling hints

### Forecaster Agent
- inputs: feature set, hypothesis set, model versions
- outputs: raw probability, model explanation payload, uncertainty components

### Calibration And Risk Agent
- inputs: raw probability, ambiguity score, contradiction score, source-reliability aggregates
- outputs: calibrated probability, attention level, penalty terms, confidence score

### Opportunity Agent
- inputs: calibrated probability, market baseline, costs, penalties
- outputs: EV estimates, ranking score, visibility suggestion

### Report Agent
- inputs: evidence summaries, contradictions, hypothesis set, forecast outputs, visibility decision
- outputs: structured report, summary cards, audit payload

## SQL-Ready Core Schema Draft

### `markets`
- `id UUID PRIMARY KEY`
- `external_market_id TEXT NOT NULL UNIQUE`
- `platform TEXT NOT NULL`
- `title TEXT NOT NULL`
- `subtitle TEXT`
- `description TEXT`
- `rules_text TEXT NOT NULL`
- `resolution_source_text TEXT`
- `market_type TEXT NOT NULL`
- `category TEXT NOT NULL`
- `subcategory TEXT NOT NULL`
- `event_id TEXT`
- `event_title TEXT`
- `open_time TIMESTAMPTZ`
- `close_time TIMESTAMPTZ`
- `expected_resolution_time TIMESTAMPTZ`
- `actual_resolution_time TIMESTAMPTZ`
- `status TEXT NOT NULL`
- `is_resolved BOOLEAN NOT NULL DEFAULT FALSE`
- `resolved_outcome TEXT`
- `ambiguity_score NUMERIC(5,4)`
- `language TEXT NOT NULL DEFAULT 'en'`
- `created_at TIMESTAMPTZ NOT NULL`
- `updated_at TIMESTAMPTZ NOT NULL`

### `market_snapshots`
- `id UUID PRIMARY KEY`
- `market_id UUID NOT NULL REFERENCES markets(id)`
- `observed_at TIMESTAMPTZ NOT NULL`
- `yes_price NUMERIC(10,6)`
- `no_price NUMERIC(10,6)`
- `yes_bid NUMERIC(10,6)`
- `yes_ask NUMERIC(10,6)`
- `no_bid NUMERIC(10,6)`
- `no_ask NUMERIC(10,6)`
- `volume_24h NUMERIC(18,6)`
- `liquidity NUMERIC(18,6)`
- `spread NUMERIC(18,6)`
- `market_prob_baseline NUMERIC(10,6)`
- `source_payload_ref TEXT`
- `created_at TIMESTAMPTZ NOT NULL`
- `UNIQUE (market_id, observed_at)`

### `market_entities`
- `id UUID PRIMARY KEY`
- `market_id UUID NOT NULL REFERENCES markets(id)`
- `entity_name TEXT NOT NULL`
- `entity_type TEXT NOT NULL`
- `normalized_entity_id TEXT`
- `role_in_market TEXT NOT NULL`
- `confidence NUMERIC(5,4) NOT NULL`
- `created_at TIMESTAMPTZ NOT NULL`

### `resolution_rules`
- `id UUID PRIMARY KEY`
- `market_id UUID NOT NULL REFERENCES markets(id) UNIQUE`
- `raw_rules_text TEXT NOT NULL`
- `parsed_resolution_conditions JSONB NOT NULL`
- `primary_resolution_authority TEXT`
- `deadline_condition TEXT`
- `ambiguity_flags JSONB NOT NULL DEFAULT '[]'::jsonb`
- `needs_attention BOOLEAN NOT NULL DEFAULT FALSE`
- `created_at TIMESTAMPTZ NOT NULL`
- `updated_at TIMESTAMPTZ NOT NULL`

### `retrieval_runs`
- `id UUID PRIMARY KEY`
- `market_id UUID NOT NULL REFERENCES markets(id)`
- `trigger_type TEXT NOT NULL`
- `started_at TIMESTAMPTZ NOT NULL`
- `completed_at TIMESTAMPTZ`
- `status TEXT NOT NULL`
- `retrieval_version TEXT NOT NULL`
- `query_plan JSONB`
- `created_at TIMESTAMPTZ NOT NULL`

### `raw_source_artifacts`
- `id UUID PRIMARY KEY`
- `retrieval_run_id UUID NOT NULL REFERENCES retrieval_runs(id)`
- `source_type TEXT NOT NULL`
- `source_name TEXT NOT NULL`
- `source_url TEXT NOT NULL`
- `source_author TEXT`
- `source_published_at TIMESTAMPTZ`
- `source_retrieved_at TIMESTAMPTZ NOT NULL`
- `raw_content_location TEXT NOT NULL`
- `mime_type TEXT`
- `language TEXT`
- `content_hash TEXT NOT NULL`
- `metadata JSONB NOT NULL DEFAULT '{}'::jsonb`
- `created_at TIMESTAMPTZ NOT NULL`

### `research_runs`
- `id UUID PRIMARY KEY`
- `market_id UUID NOT NULL REFERENCES markets(id)`
- `trigger_type TEXT NOT NULL`
- `started_at TIMESTAMPTZ NOT NULL`
- `completed_at TIMESTAMPTZ`
- `status TEXT NOT NULL`
- `graph_version TEXT NOT NULL`
- `prompt_version TEXT NOT NULL`
- `retrieval_version TEXT NOT NULL`
- `feature_version TEXT NOT NULL`
- `forecast_version TEXT NOT NULL`
- `report_version TEXT NOT NULL`
- `visibility_decision TEXT`
- `attention_level TEXT`
- `run_metadata JSONB NOT NULL DEFAULT '{}'::jsonb`
- `created_at TIMESTAMPTZ NOT NULL`

### `evidence_items`
- `id UUID PRIMARY KEY`
- `artifact_id UUID NOT NULL REFERENCES raw_source_artifacts(id)`
- `market_id UUID NOT NULL REFERENCES markets(id)`
- `research_run_id UUID REFERENCES research_runs(id)`
- `extracted_text TEXT NOT NULL`
- `summary TEXT`
- `entities JSONB NOT NULL DEFAULT '[]'::jsonb`
- `claims JSONB NOT NULL DEFAULT '[]'::jsonb`
- `timestamps_found JSONB NOT NULL DEFAULT '[]'::jsonb`
- `numeric_facts JSONB NOT NULL DEFAULT '[]'::jsonb`
- `stance_toward_yes TEXT`
- `stance_confidence NUMERIC(5,4)`
- `reliability_score NUMERIC(5,4)`
- `relevance_score NUMERIC(5,4)`
- `novelty_score NUMERIC(5,4)`
- `contradiction_tags JSONB NOT NULL DEFAULT '[]'::jsonb`
- `used_in_report BOOLEAN NOT NULL DEFAULT FALSE`
- `extraction_version TEXT NOT NULL`
- `created_at TIMESTAMPTZ NOT NULL`

### `claims`
- `id UUID PRIMARY KEY`
- `evidence_id UUID NOT NULL REFERENCES evidence_items(id)`
- `claim_text TEXT NOT NULL`
- `claim_type TEXT NOT NULL`
- `subject_entity TEXT`
- `predicate TEXT`
- `object_value TEXT`
- `event_time TIMESTAMPTZ`
- `confidence NUMERIC(5,4) NOT NULL`
- `support_direction TEXT NOT NULL`
- `created_at TIMESTAMPTZ NOT NULL`

### `forecast_outputs`
- `id UUID PRIMARY KEY`
- `market_id UUID NOT NULL REFERENCES markets(id)`
- `research_run_id UUID REFERENCES research_runs(id)`
- `feature_version TEXT NOT NULL`
- `forecast_version TEXT NOT NULL`
- `model_name TEXT NOT NULL`
- `raw_probability_yes NUMERIC(10,6) NOT NULL`
- `calibrated_probability_yes NUMERIC(10,6)`
- `confidence_score NUMERIC(5,4)`
- `uncertainty_payload JSONB NOT NULL DEFAULT '{}'::jsonb`
- `explanation_payload JSONB NOT NULL DEFAULT '{}'::jsonb`
- `generated_at TIMESTAMPTZ NOT NULL`
- `created_at TIMESTAMPTZ NOT NULL`

### `opportunity_records`
- `id UUID PRIMARY KEY`
- `market_id UUID NOT NULL REFERENCES markets(id)`
- `forecast_output_id UUID NOT NULL REFERENCES forecast_outputs(id)`
- `snapshot_id UUID REFERENCES market_snapshots(id)`
- `market_probability_yes_baseline NUMERIC(10,6) NOT NULL`
- `internal_probability_yes NUMERIC(10,6) NOT NULL`
- `cost_assumption NUMERIC(10,6) NOT NULL`
- `expected_value_yes NUMERIC(12,6)`
- `expected_value_no NUMERIC(12,6)`
- `ranking_score NUMERIC(12,6) NOT NULL`
- `ambiguity_penalty NUMERIC(10,6) NOT NULL DEFAULT 0`
- `contradiction_penalty NUMERIC(10,6) NOT NULL DEFAULT 0`
- `evidence_completeness_score NUMERIC(5,4)`
- `freshness_score NUMERIC(5,4)`
- `visibility_status TEXT NOT NULL DEFAULT 'visible'`
- `risk_reason_codes JSONB NOT NULL DEFAULT '[]'::jsonb`
- `created_at TIMESTAMPTZ NOT NULL`

## Immediate Backlog
1. turn the schema draft into migration-ready DDL
2. translate the drafted ambiguity rubric into code-level scoring functions and tests
3. translate the drafted source reliability framework into provider metadata and scoring rules
4. translate the drafted agent contracts into LangGraph state and node interfaces
5. implement the first offline and near-realtime feature pipelines for binary classification
6. convert API contracts into FastAPI route schemas and response models

## First-Pass Feature Buckets

### Near-realtime candidates
- short-window price returns and volatility
- price jump and momentum flags
- evidence arrival counts by trust tier
- latest contradiction score
- time since last deep refresh
- freshness decay metrics

### Offline candidates
- long-window market trajectory summaries
- entity historical hit-rate or category priors
- source reliability aggregates
- event calendar distance features
- market wording and ambiguity features
- contradiction density over historical windows

### Derived-from-both candidates
- current market move relative to historical regime
- current evidence burst relative to baseline source activity
- present contradiction burden relative to historical norm

## First-Pass Feature Catalog

### Near-realtime features
- `rt_price_yes_last`
  Purpose: latest market-implied state snapshot
  Inputs: `market_snapshots.yes_price`
  Status: stable
- `rt_price_return_1h`
  Purpose: short-horizon price direction
  Inputs: point-in-time joined `market_snapshots`
  Status: stable
- `rt_price_return_24h`
  Purpose: short-horizon momentum
  Inputs: point-in-time joined `market_snapshots`
  Status: stable
- `rt_price_volatility_24h`
  Purpose: recent instability signal
  Inputs: recent `market_snapshots`
  Status: stable
- `rt_spread_latest`
  Purpose: contextual market quality metadata
  Inputs: latest `yes_bid`, `yes_ask`, `no_bid`, `no_ask`, `spread`
  Status: stable
- `rt_snapshot_age_seconds`
  Purpose: detect stale market data
  Inputs: latest snapshot timestamp and inference time
  Status: stable
- `rt_evidence_count_6h_high_trust`
  Purpose: near-term high-quality information arrival
  Inputs: `evidence_items.created_at`, source trust tier
  Status: stable
- `rt_evidence_count_24h_all`
  Purpose: overall recent evidence intensity
  Inputs: `evidence_items.created_at`
  Status: stable
- `rt_source_mix_low_trust_share_24h`
  Purpose: detect low-trust dominance in recent evidence
  Inputs: `evidence_items.reliability_score`, source trust tier
  Status: stable
- `rt_contradiction_score_latest`
  Purpose: latest disagreement and fragility pressure
  Inputs: skeptic output and contradiction-tagged evidence
  Status: stable
- `rt_time_since_last_deep_refresh`
  Purpose: freshness of the expensive research path
  Inputs: `research_runs.completed_at`
  Status: stable

### Offline features
- `of_market_duration_days`
  Purpose: capture horizon effects
  Inputs: `markets.open_time`, `markets.expected_resolution_time`
  Status: stable
- `of_days_to_resolution`
  Purpose: point-in-time remaining horizon
  Inputs: replay time plus `markets.expected_resolution_time`
  Status: stable
- `of_market_type_one_hot`
  Purpose: encode market family structure
  Inputs: `markets.market_type`, `category`, `subcategory`
  Status: stable
- `of_rules_length_chars`
  Purpose: coarse proxy for rule complexity
  Inputs: `markets.rules_text`
  Status: stable
- `of_ambiguity_score`
  Purpose: explicit resolution ambiguity signal
  Inputs: parser output, `resolution_rules`
  Status: stable but rubric-dependent
- `of_entity_count`
  Purpose: market complexity proxy
  Inputs: `market_entities`
  Status: stable
- `of_entity_role_pattern`
  Purpose: encode structural market shape
  Inputs: `market_entities.role_in_market`
  Status: stable
- `of_long_return_7d`
  Purpose: medium-horizon trend
  Inputs: point-in-time joined `market_snapshots`
  Status: stable
- `of_long_volatility_30d`
  Purpose: medium-horizon instability regime
  Inputs: point-in-time joined `market_snapshots`
  Status: stable
- `of_source_reliability_mean_30d`
  Purpose: quality of recent evidence corpus
  Inputs: `evidence_items.reliability_score`
  Status: stable but scoring-method-dependent
- `of_source_diversity_30d`
  Purpose: protect against monoculture evidence
  Inputs: source family counts from artifacts and evidence
  Status: stable
- `of_contradiction_density_30d`
  Purpose: persistent disagreement signal
  Inputs: contradiction tags over historical windows
  Status: stable
- `of_evidence_recency_weighted_30d`
  Purpose: weighted evidence intensity over time
  Inputs: evidence timestamps with decay weighting
  Status: stable
- `of_event_calendar_distance`
  Purpose: proximity to known scheduled catalysts
  Inputs: event calendar table plus market/entity linkage
  Status: stable

### Provisional offline features
- `of_entity_history_prior`
  Purpose: cohort-based prior for recurring entities
  Inputs: historical resolved market cohorts
  Status: provisional
- `of_polling_signal_summary`
  Purpose: structured election signal
  Inputs: polling providers not yet finalized
  Status: provisional
- `of_fec_activity_intensity`
  Purpose: finance/activity proxy for election-related markets
  Inputs: OpenFEC and filing-derived aggregates
  Status: provisional
- `of_legislative_activity_intensity`
  Purpose: live policy-process signal
  Inputs: Congress.gov and related official activity
  Status: provisional
- `of_official_document_burst`
  Purpose: official document momentum
  Inputs: GovInfo and other official-document feeds
  Status: provisional

### Derived-from-both features
- `db_price_move_vs_30d_regime`
  Purpose: contextualize a fresh move against market history
  Inputs: `rt_price_return_1h`, `of_long_volatility_30d`
  Status: stable
- `db_recent_evidence_burst_vs_baseline`
  Purpose: detect abnormal information arrival
  Inputs: `rt_evidence_count_24h_all`, `of_evidence_recency_weighted_30d`
  Status: stable
- `db_contradiction_vs_history`
  Purpose: detect abnormal disagreement spikes
  Inputs: `rt_contradiction_score_latest`, `of_contradiction_density_30d`
  Status: stable
- `db_snapshot_staleness_adjusted_confidence`
  Purpose: lower trust in stale inference contexts
  Inputs: `rt_snapshot_age_seconds`, historical update cadence
  Status: provisional

## Feature Definition Rules
- every feature must have a raw input contract, point-in-time definition, and owner service
- near-realtime features must be computable without scanning the full historical corpus
- offline features must be replay-safe and batch reproducible
- provisional features are optional for the first model baseline
- the first model baseline must run end to end using only stable features

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

## First-Baseline Exclusions
- `market_prob_baseline` and any direct live market-price feature
- provisional political-domain features until their upstream inputs stabilize
- liquidity and spread as training features in the initial pass
- embedding-heavy or graph-heavy learned representations

## Ambiguity Scoring Rubric

### Weighted components
- resolution authority clarity: `0.25`
- deadline and timing clarity: `0.20`
- term-definition clarity: `0.20`
- conditional-branch complexity: `0.15`
- edge-case exposure: `0.10`
- parser confidence penalty: `0.10`

### Score bands
- `0.00` to `0.19`: clear
- `0.20` to `0.39`: mild ambiguity
- `0.40` to `0.59`: material ambiguity
- `0.60` to `0.79`: high ambiguity
- `0.80` to `1.00`: severe ambiguity

### System effects
- `0.40+` warning badge and ranking penalty
- `0.60+` `needs_attention = true`
- `0.80+` default `visibility_status = deemphasized`

## Source Reliability Framework

### Reliability tiers
- `tier_1_official`
- `tier_2_institutional`
- `tier_3_aggregated`
- `tier_4_community`
- `tier_5_unverified`

### Score construction
- prior by tier
- attribution adjustment
- document-type adjustment
- recency adjustment
- corroboration adjustment
- contradiction adjustment

### Example priors
- `tier_1_official = 0.90`
- `tier_2_institutional = 0.75`
- `tier_3_aggregated = 0.55`
- `tier_4_community = 0.35`
- `tier_5_unverified = 0.15`

## Visibility Policy Draft
- all outputs are visible to the owner by default
- ambiguous or low-confidence outputs receive warning or deemphasized status
- non-normal outputs include structured risk reasons
- no reviewer queue or approval state exists in v1

## API Endpoint Contracts

### `GET /markets`
- purpose: list markets with current state and latest visibility summary
- query params: `category`, `subcategory`, `status`, `attention_level`, `limit`, `cursor`
- returns: paginated market summaries

### `GET /markets/{market_id}`
- purpose: fetch canonical market detail
- returns: market object, parsed rules, entity map, latest forecast summary

### `GET /markets/{market_id}/snapshots`
- purpose: retrieve historical market snapshots
- query params: `from`, `to`, `interval`
- returns: ordered snapshot series

### `GET /markets/{market_id}/report`
- purpose: fetch the latest structured report payload
- returns: executive summary, supporting evidence, opposing evidence, assumptions, risk reasons

### `GET /markets/{market_id}/evidence`
- purpose: browse evidence for a market
- query params: `trust_tier`, `source_type`, `from`, `to`, `stance`, `limit`, `cursor`
- returns: paginated evidence items and linked artifacts

### `GET /opportunities`
- purpose: list ranked opportunities
- query params: `category`, `attention_level`, `min_ev`, `limit`, `cursor`
- returns: paginated opportunity records with score components

### `GET /opportunities/{market_id}`
- purpose: fetch the latest opportunity view for a market
- returns: EV estimate, score components, penalties, latest forecast linkage

### `POST /research-runs/{market_id}/refresh`
- purpose: trigger a manual refresh
- body: `{"mode":"fast|deep","reason":"string"}`
- returns: accepted research-run descriptor

### `GET /research-runs`
- purpose: inspect recent research runs
- query params: `market_id`, `status`, `trigger_type`, `limit`, `cursor`
- returns: paginated research-run summaries

### `POST /replay-runs`
- purpose: create a replay job for a market or cohort
- body: replay window, market filters, model version, feature version
- returns: accepted replay-run descriptor

## Infra Topology
- PostgreSQL for canonical relational data
- object storage for raw payloads, artifacts, and replay archives
- Redis for near-realtime feature serving and queue coordination
- Python worker processes for ingestion, retrieval, orchestration, forecasting, and replay
- Next.js frontend served separately from the API service

## ELT Layering Direction
- raw landing layer for immutable or append-only payload capture
- refined canonical layer for normalized market, snapshot, and evidence tables
- feature-ready layer for training, inference, and replay joins
- transformations should be rerunnable from raw data when schema assumptions change

## Observability Model
- structured logs keyed by `market_id`, `research_run_id`, and `replay_run_id`
- metrics for ingestion lag, snapshot freshness, artifact retrieval failures, and stale reports
- model metrics for Brier, log loss, ECE, and segment-level reliability
- traces spanning ingestion, research, forecasting, ranking, and report generation

## Implementation-Ready Next Artifacts
- migration-ready DDL
- repository skeleton and local orchestration files
- feature-definition registry stubs
- agent prompt/version registry stubs
