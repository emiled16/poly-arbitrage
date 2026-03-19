# Polymarket Research & Opportunity Platform — Technical Spec Sheet

## 1. Purpose

Build a multi-user private platform that continuously monitors Polymarket political and election markets, runs a multi-agent research and forecasting workflow, estimates internally derived probabilities, compares those estimates to live market prices, and surfaces a ranked feed of opportunities with full research reports.

This is a research and alerting system in v1. It does not execute trades. It may later support paper trading only.

---

## 2. Product Scope

### 2.1 In scope for v1
- Continuous ingestion of Polymarket political/election markets
- Real-time market and metadata updates
- Multi-agent research workflow per market
- Broad-source retrieval across high-trust and noisy sources
- Full research report generation for each market
- Forecast generation using hybrid methods
- Ranked feed of opportunities
- Full evidence retention for auditability
- Strict point-in-time backtesting from day one
- Multi-user private web platform

### 2.2 Out of scope for v1
- Real-money trade execution
- Broker or wallet integration
- Portfolio management for actual capital
- Public multi-tenant SaaS onboarding
- Fully autonomous capital allocation

### 2.3 Future scope
- Paper trading only

---

## 3. Product Decisions Captured

- v1 mode: research + alerts only
- future scope: paper trading only, no live execution
- initial users: small private group, multi-user but controlled
- v1 market class: politics / elections
- market duration: short, medium, and long duration
- ambiguous markets: included but heavily penalized in scoring
- sources: broad coverage, including noisy sources
- output: full research reports with evidence and contradictions
- skeptic agent: mandatory for every market
- forecasting: hybrid, interpretable + ML from start
- market price usage: baseline only
- optimization target: balance forecast quality and opportunity quality
- opportunity definition: expected value after costs
- alerting mode: ranked feed of opportunities, no strict cutoff
- liquidity/spread: ignored in scoring by product choice
- runtime mode: fully real-time continuous system
- stack: mixed Python + Go/Rust for performance-sensitive parts
- interface: full polished product UI
- data retention: store all raw evidence
- evaluation: strict point-in-time backtesting from day one

---

## 4. Product Goals

### 4.1 Core goal
Surface prediction opportunities in political and election markets by combining market data, broad information retrieval, multi-agent research, feature engineering, and probability forecasting.

### 4.2 User-facing promise
For each relevant market, the platform should provide:
- a current internal probability estimate
- the current Polymarket implied price baseline
- an opportunity score or expected-value view
- a full research memo
- contradictory evidence and uncertainty signals
- a transparent evidence trail

### 4.3 Success metrics

#### Forecast quality
- Brier score
- Log loss
- Calibration error
- Reliability by market category and horizon

#### Opportunity quality
- Precision of top-ranked opportunities
- Simulated expected-value quality under historical replay
- Stability of ranking through time
- False positive rate driven by noisy sources

#### Product quality
- Time from market change to updated report
- Time from major external event to market thesis revision
- Percentage of reports with complete evidence trace
- User engagement with ranked feed and report views

---

## 5. System Overview

The system consists of seven major layers.

### 5.1 Market ingestion layer
Responsible for ingesting Polymarket markets, metadata, prices, orderbook or price snapshots, and market lifecycle changes.

### 5.2 Market understanding and triage layer
Parses market wording, identifies entities, classifies market type, flags ambiguity, and decides which research and feature pipelines to run.

### 5.3 Retrieval and evidence layer
Fetches broad-source evidence from trusted and noisy channels, stores raw artifacts, and builds searchable evidence objects.

### 5.4 Agentic research layer
Runs a graph of agents that plan research, retrieve, extract evidence, challenge hypotheses, and assemble a market thesis.

### 5.5 Forecasting and feature layer
Builds offline and online features, produces model predictions, and supports a path toward Bayesian or neural-Bayesian forecasting later.

### 5.6 Opportunity ranking layer
Compares internal probabilities to Polymarket implied probabilities, computes expected-value style opportunity metrics, and ranks markets.

### 5.7 Product and evaluation layer
Serves the UI, APIs, user access, observability, versioning, and point-in-time backtesting.

---

## 6. High-Level Architecture

### 6.1 Core components
- Market stream service
- Market metadata parser service
- Research orchestration service
- Evidence ingestion service
- Feature pipeline service
- Forecast service
- Opportunity ranking service
- Backtesting and replay service
- API gateway / backend service
- Web frontend

### 6.2 Storage components
- Postgres for canonical relational data
- Object storage for raw evidence and snapshots
- Vector database for retrieval and semantic evidence search
- Feature store with offline and online components
- Time-series tables for market snapshots and model outputs
- Cache / stream bus for real-time propagation

### 6.3 Suggested technology mapping
- Python: ML, data processing, agent workflows, backend services
- Go or Rust: low-latency ingestion, streaming, parsers, high-throughput services if required
- FastAPI: application backend APIs
- Next.js: polished web frontend
- PostgreSQL: transactional store
- Redis or NATS/Kafka: streaming/caching/event propagation
- Qdrant or Weaviate: vector retrieval
- Feast or custom feature store pattern: online/offline features
- Dagster or Temporal for orchestration; LangGraph for agent graph execution

### 6.4 Recommended initial orchestration split
- LangGraph: per-market research graph and multi-agent execution
- Dagster or Temporal: continuous scheduling, retries, backfills, replay workflows

---

## 7. External Data Sources

### 7.1 Primary market source
- Polymarket Gamma/Data APIs
- Polymarket CLOB / orderbook-related data where needed
- Optional indexed or subgraph-derived market history if useful

### 7.2 News and event sources
- Major news APIs and feeds
- GDELT for broad event/news indexing
- RSS aggregation across political publishers
- Official campaign sites and press releases
- Government pages and press offices

### 7.3 Noisy or alternative sources
- X / Twitter if accessible under product/legal constraints
- Reddit
- Podcasts and political commentary
- YouTube and transcript sources
- Blogs and newsletters

### 7.4 Structured political sources
- Polling aggregators and poll data sources
- Official election result sources
- Government election agencies
- Candidate filing and fundraising sources where available
- Public schedules, debate calendars, court calendars, legislative calendars

### 7.5 Cross-market or benchmarking sources
- Kalshi for external market comparison where relevant
- Manifold as sentiment-like reference, not price-equivalent benchmark

---

## 8. Market Domain Model

### 8.1 Market
Fields:
- market_id
- external_market_id
- platform
- title
- subtitle
- description
- rules_text
- resolution_source_text
- market_type
- category
- subcategory
- event_id
- event_title
- open_time
- close_time
- expected_resolution_time
- actual_resolution_time
- status
- is_resolved
- resolved_outcome
- ambiguity_score
- language
- created_at
- updated_at

### 8.2 Market snapshot
Fields:
- snapshot_id
- market_id
- observed_at
- yes_price
- no_price
- yes_bid
- yes_ask
- no_bid
- no_ask
- volume_24h
- liquidity
- spread
- market_prob_baseline
- source_payload_ref

### 8.3 Market entity map
Fields:
- market_entity_id
- market_id
- entity_name
- entity_type
- normalized_entity_id
- role_in_market
- confidence

### 8.4 Resolution rule object
Fields:
- resolution_rule_id
- market_id
- raw_rules_text
- parsed_resolution_conditions
- primary_resolution_authority
- deadline_condition
- ambiguity_flags
- human_review_required

---

## 9. Evidence and Knowledge Model

### 9.1 Raw source artifact
Fields:
- artifact_id
- source_type
- source_name
- source_url
- source_author
- source_published_at
- source_retrieved_at
- raw_content_location
- mime_type
- language
- content_hash
- retrieval_run_id

### 9.2 Evidence item
Fields:
- evidence_id
- artifact_id
- market_id
- extracted_text
- summary
- entities
- claims
- timestamps_found
- numeric_facts
- stance_toward_yes
- stance_confidence
- reliability_score
- relevance_score
- novelty_score
- contradiction_tags
- used_in_report
- extraction_version

### 9.3 Claim object
Fields:
- claim_id
- evidence_id
- claim_text
- claim_type
- subject_entity
- predicate
- object_value
- event_time
- confidence
- support_direction

### 9.4 Evidence graph edges
Fields:
- edge_id
- source_node_type
- source_node_id
- target_node_type
- target_node_id
- relation_type
- weight
- created_at

### 9.5 Research run
Fields:
- research_run_id
- market_id
- trigger_type
- started_at
- completed_at
- status
- graph_version
- prompt_version
- retrieval_version
- feature_version
- forecast_version
- report_version

---

## 10. Multi-Agent Graph

The agent system should be explicit and auditable rather than a vague swarm.

### 10.1 Agent 1 — Market Parser Agent
Responsibilities:
- parse market title and rules
- identify entities, timeline, thresholds, and event type
- create structured market schema
- flag ambiguity and potential resolution traps

Outputs:
- structured market object
- entity map
- ambiguity notes
- suggested research plan seed

### 10.2 Agent 2 — Research Planner Agent
Responsibilities:
- decide what evidence classes are needed
- select source families
- generate retrieval sub-queries
- define what would count as confirming vs disconfirming evidence

Outputs:
- source plan
- query plan
- evidence checklist
- contradiction checklist

### 10.3 Agent 3 — Retrieval Agent
Responsibilities:
- fetch documents, feeds, and source artifacts
- gather broad-source evidence
- enforce point-in-time constraints in replay/backtest mode
- save all raw artifacts

Outputs:
- raw artifact set
- retrieval metadata
- candidate evidence pool

### 10.4 Agent 4 — Evidence Extractor Agent
Responsibilities:
- chunk and analyze artifacts
- extract claims, entities, dates, numerical facts, sentiment or stance
- attach reliability and novelty signals

Outputs:
- evidence items
- claims
- supporting and opposing signal buckets

### 10.5 Agent 5 — Skeptic Agent
Responsibilities:
- attempt to disprove the current thesis
- search for contrary sources and missing assumptions
- identify narrative overreach and low-trust dependence
- surface alternative interpretations of resolution wording

Outputs:
- contradiction memo
- fragility list
- uncertainty amplifiers

### 10.6 Agent 6 — Hypothesis Builder Agent
Responsibilities:
- synthesize evidence into explicit hypotheses
- map causal chains and scenario branches
- distinguish prediction-relevant evidence from noise

Outputs:
- structured hypothesis set
- scenario tree
- feature hints for modeling

### 10.7 Agent 7 — Forecaster Agent
Responsibilities:
- generate probability estimate using available features and model outputs
- combine interpretable logic and ML outputs
- produce confidence and decomposition by feature family

Outputs:
- raw probability estimate
- model explanation payload
- uncertainty components

### 10.8 Agent 8 — Calibration and Risk Agent
Responsibilities:
- calibrate forecast probabilities
- account for ambiguity penalties
- evaluate source-quality concentration risk
- flag unstable outputs or high model disagreement

Outputs:
- calibrated probability
- penalty terms
- trust score

### 10.9 Agent 9 — Opportunity Agent
Responsibilities:
- compare calibrated probability against live market baseline
- compute expected-value style score after cost assumptions
- produce ranking features

Outputs:
- opportunity record
- expected-value estimate
- ranking score

### 10.10 Agent 10 — Report Agent
Responsibilities:
- assemble user-facing research report
- include evidence, contradictions, feature highlights, and methodology summary
- surface unresolved unknowns

Outputs:
- report document
- UI-friendly summary cards
- audit payload

---

## 11. Forecasting Strategy

### 11.1 Modeling philosophy
The platform will start with a hybrid approach:
- interpretable rules and structured heuristics
- classical ML models on engineered features
- eventual path toward Bayesian or neural-Bayesian prediction

### 11.2 Initial model path
Initial models may include:
- decision trees
- gradient boosted trees
- logistic regression on engineered features
- ranking models for opportunity prioritization

### 11.3 Later model path
Potential later additions:
- Bayesian logistic models
- hierarchical Bayesian event models
- neural networks with uncertainty estimation
- hybrid neural models that consume online and offline features
- posterior-updating layer over structured priors

### 11.4 Market price policy
Polymarket price is not used as a model feature or Bayesian prior in v1. It is used strictly as the external baseline against which internal probabilities are compared.

### 11.5 Prediction targets
- probability of YES resolution
- optional interval or uncertainty proxy
- opportunity score target for ranking

### 11.6 Forecast evaluation
- Brier score
- log loss
- expected calibration error
- calibration plots
- segment-level evaluation by horizon, topic, and source mix

---

## 12. Feature Store Design

The user explicitly wants online and offline features. The design should separate historical reproducibility from real-time serving.

### 12.1 Feature store goals
- support training and backtesting with point-in-time correctness
- support low-latency online inference
- unify agent-derived and structured features
- allow feature versioning and lineage

### 12.2 Offline feature groups
Examples:
- historical market trajectory features
- market wording and ambiguity features
- source reliability aggregates
- entity-level historical performance features
- polling or election-cycle features
- event calendar distance features
- topic momentum features
- contradiction density features
- source-diversity features
- recency-weighted evidence aggregates
- narrative-consensus vs narrative-conflict features

### 12.3 Online feature groups
Examples:
- most recent market price and movement statistics
- latest evidence arrival counts
- recent high-trust vs low-trust source mix
- near-real-time topic velocity
- breaking-news trigger indicators
- latest skeptic contradiction score
- latest ambiguity/rule-risk adjustments

### 12.4 Feature classes
- structured numerical features
- categorical features
- text-derived embedding features
- graph-derived features
- time-window aggregates
- model-generated meta-features

### 12.5 Candidate storage pattern
- offline features in parquet/data lake and warehouse-style tables
- online features in Redis / low-latency store
- registry for feature definitions and point-in-time joins

### 12.6 Candidate tooling
- Feast for feature definitions and online/offline coordination
- custom offline joins if more control is needed
- dbt for transformation layer where appropriate

---

## 13. Opportunity Definition and Scoring

The user defined opportunity as expected value after costs.

### 13.1 Base quantities
- internal_probability_yes
- market_probability_yes_baseline
- cost_assumption
- expected_value_yes
- expected_value_no if relevant from opposite-side framing

### 13.2 First-pass EV formula
For YES side:
- EV_yes = p_internal * payoff_if_yes - (1 - p_internal) * loss_if_no - transaction_costs

Where a market-price-compatible simplified framing can be used depending on quote conventions.

### 13.3 Ranking score design
A first ranking score can combine:
- expected value after costs
- calibrated confidence
- evidence completeness
- contradiction burden
- ambiguity penalty
- freshness of latest research

### 13.4 Important note
By explicit product choice, liquidity and spread are ignored in ranking. This should still be visible in the UI as contextual metadata because users may care operationally, even if the score does not penalize it.

---

## 14. Real-Time Pipeline Design

The runtime mode is fully real-time continuous.

### 14.1 Triggers
The following events can trigger a market pipeline update:
- new market appears
- market price changes materially
- market metadata or rules change
- major external evidence item arrives
- source-specific event triggers an entity-linked market refresh
- scheduled low-frequency recheck to prevent stale state

### 14.2 Pipeline stages
1. ingest market update
2. update market snapshots
3. detect affected entities and markets
4. dispatch retrieval and research workflow
5. refresh online features
6. run forecast
7. update opportunity rank
8. refresh report
9. push UI updates and notifications if needed

### 14.3 Streaming design candidates
- event bus via Kafka, Redpanda, or NATS
- consumer services for market updates, retrieval tasks, and forecasting tasks
- idempotent event handling
- dead-letter queues for failures

### 14.4 Real-time constraints
Political research and broad retrieval can be expensive. The system should support:
- fast path updates for price-only changes
- slower deep-research refresh for major evidence updates
- market priority queues to avoid recomputing everything equally

---

## 15. Backtesting and Replay

Backtesting is strict from day one.

### 15.1 Requirements
- no future documents visible at prediction time
- no feature leakage from future snapshots
- no model training on future labels relative to replay point
- report generation must use only available evidence at that historical timestamp

### 15.2 Replay engine responsibilities
- reconstruct market state at time T
- reconstruct available evidence corpus at time T
- rebuild features with point-in-time joins
- execute the same agent graph under replay constraints
- store historical predictions and ranks

### 15.3 Evaluation outputs
- forecast metrics over time
- opportunity ranking quality over time
- agent trace quality and failure analysis
- source-mix sensitivity analysis

---

## 16. API Design

### 16.1 Market APIs
- list markets
- get market detail
- get market snapshots
- get market report
- get market evidence timeline
- get market hypotheses

### 16.2 Opportunity APIs
- get ranked opportunities
- filter opportunities by topic, horizon, confidence, ambiguity, source mix
- get opportunity detail

### 16.3 Research APIs
- trigger manual market refresh
- view research runs
- inspect agent outputs
- inspect contradictions and unresolved unknowns

### 16.4 Backtesting APIs
- run replay for a market or cohort
- compare model versions
- fetch historical forecast metrics

### 16.5 Admin APIs
- source controls
- model version controls
- feature version registry view
- user and group access control

---

## 17. UI Structure

The interface must be a polished full product UI.

### 17.1 Main screens
- Ranked opportunities dashboard
- Market detail page
- Research report page
- Evidence explorer
- Historical odds and forecast timeline view
- Backtesting and model evaluation dashboard
- Admin / configuration console

### 17.2 Ranked opportunities dashboard
Should show:
- market title
- current market probability baseline
- internal probability
- EV estimate
- ambiguity score
- latest update time
- source mix summary
- contradiction intensity
- trend of opportunity score

### 17.3 Market detail page
Should show:
- market wording and rules
- live price history
- internal probability history
- evidence timeline
- hypothesis tree
- contradiction panel
- method summary
- linked entities and related markets

### 17.4 Research report page
Should show:
- executive summary
- full supporting evidence
- opposing evidence
- source references
- extracted claims
- major assumptions
- unresolved questions
- model explanation summary

### 17.5 Evidence explorer
Should support:
- source-type filters
- trust filters
- time filters
- query search
- artifact preview
- claim graph exploration

---

## 18. Infra and Deployment

### 18.1 Environment model
- local development with docker-compose or dev containers
- staging environment with replay and limited real-time ingestion
- production private deployment for the user group

### 18.2 Deployment targets
- Kubernetes or Nomad for multi-service orchestration
- object storage via S3-compatible backend
- managed Postgres if available
- Redis or stream bus as shared infra

### 18.3 Service split suggestion
- ingestion service
- retrieval service
- agent orchestration service
- forecasting service
- ranking service
- API/backend service
- frontend service
- replay/backtest worker pool

### 18.4 Mixed-language split suggestion
Python services:
- research and agent orchestration
- feature computation
- forecasting
- APIs

Go/Rust candidates:
- low-latency market ingestion
- stream consumers
- event routing
- parsers and high-throughput transformation utilities

### 18.5 Observability
- structured logs
- metrics per market pipeline
- tracing per research run
- model and prompt version tracking
- alerting on ingestion lag, retrieval failure, and stale markets

---

## 19. Security and Access

Because this is a private multi-user system, it should support:
- role-based access control
- audit logs for admin actions
- secrets management for APIs
- source usage controls and rate-limit handling
- private report access per group or team if needed later

---

## 20. Risks and Failure Modes

### 20.1 Resolution ambiguity risk
Political markets can hinge on wording and edge-case interpretations.
Mitigation:
- parsed rule objects
- ambiguity score
- contradiction review focused on resolution language

### 20.2 Noisy-source contamination
Broad source coverage can degrade quality fast.
Mitigation:
- reliability scoring
- source diversity tracking
- skeptic agent mandatory
- evidence weighting and provenance display

### 20.3 Hallucinated reasoning from LLM agents
Mitigation:
- evidence-linked extraction only
- explicit unsupported-claim detection
- report sections separating facts from hypotheses

### 20.4 Overfitting and backtest optimism
Mitigation:
- strict point-in-time replay
- versioned datasets, features, and prompts
- baseline comparisons

### 20.5 Real-time cost explosion
Broad retrieval and continuous updates can become expensive.
Mitigation:
- priority queues
- incremental recomputation
- separate fast and slow paths

### 20.6 Political domain complexity
Election markets can have long cycles, rumor-driven swings, and changing narratives.
Mitigation:
- explicit source trust layers
- long-horizon and short-horizon feature separation
- entity-centric monitoring

### 20.7 Product-level mismatch
Ignoring liquidity/spread may rank impractical opportunities highly.
Mitigation:
- show liquidity/spread in UI even if not scored
- retain optional future toggle for score penalty

---

## 21. Suggested MVP Roadmap

### Phase 0 — Foundations
- finalize domain scope for political/election subcategories
- build market ingestion
- define schema
- set up storage and raw evidence archive
- create strict replay design before model work

### Phase 1 — Research substrate
- implement market parser
- implement retrieval layer
- store artifacts and evidence items
- build first report generation flow
- add skeptic agent

### Phase 2 — Forecasting substrate
- define online/offline features
- stand up feature store pattern
- train first interpretable + ML models
- expose internal probability estimates
- add versioning and evaluation dashboards

### Phase 3 — Opportunity engine and UI
- compute EV-style opportunity metrics
- build ranked opportunities dashboard
- build market detail and report pages
- add user controls and filters

### Phase 4 — Continuous real-time system
- event streaming
- incremental refresh logic
- performance optimization with Go/Rust where necessary
- production hardening

### Phase 5 — Paper-trading groundwork
- not in v1, but keep interfaces compatible with future paper trading records

---

## 22. Open Design Questions for Next Iteration

These are the next design questions to resolve before implementation planning becomes ticket-ready.

1. Which political/election subdomains are in v1: US federal elections, party nominations, legislative control, cabinet appointments, court decisions, geopolitical politics, or all politics?
2. Which broad-source providers are legally and operationally feasible for ingestion?
3. What is the exact ambiguity scoring rubric?
4. How should source reliability be quantified and updated?
5. Which features are model inputs in the first ML baseline?
6. Which evidence-derived outputs should be hard features vs report-only annotations?
7. What real-time update frequency is acceptable per market tier?
8. How much human-in-the-loop review is desired for report publication in early versions?
9. What should be the first benchmark models and baselines?
10. What is the exact UI information hierarchy for opportunity ranking vs research depth?

---

## 23. Recommended Immediate Next Step

Translate this spec into an implementation blueprint with:
- component diagram
- event flow diagram
- concrete database schema (SQL-ready)
- feature definitions
- agent input/output contracts
- API endpoint contracts
- infra topology
- milestone backlog with acceptance criteria

That should be the next artifact.

