# Brainstorming Context

## Problem Statement
Build a private platform that continuously monitors Polymarket political and election markets, produces internal probability estimates through auditable research and forecasting, and ranks opportunities against live market prices without executing trades.

## v1 Product Boundaries
- research and alerting only
- private single-user product
- broader political markets, including elections but not limited to them
- full evidence retention and auditability
- strict point-in-time replay from day one
- no live execution
- future compatibility with paper trading only

## Approved v1 Market Families
- elections and nominations
- legislative control and major leadership races
- cabinet appointments and confirmations
- major court and regulatory decisions with clear political resolution criteria
- high-salience geopolitical politics markets

## Explicit v1 Exclusions
- purely local or municipal politics
- vague opinion or sentiment markets
- markets with highly subjective or unstable resolution wording
- non-political markets

## Product Principles
- auditability over black-box automation
- evidence-linked reasoning over free-form agent output
- backtesting correctness over fast iteration shortcuts
- ranked opportunities over binary alert thresholds
- human-readable reports alongside model outputs
- noisy-source coverage is allowed, but skepticism and provenance are mandatory

## Technical Principles
- start simple in Python where possible
- defer Go/Rust until profiling proves a bottleneck
- keep services modular and contracts explicit
- separate offline reproducibility from online serving
- version prompts, retrieval logic, features, models, and reports
- treat replay safety as a first-class architecture concern
- ship local-first, but avoid local-only architecture dead ends

## Early Data Strategy
- capture raw source payloads first
- explore real payloads before locking refined schemas too early
- prefer reprocessable ELT layers over brittle one-shot normalization
- let observed data shape influence canonical tables and downstream contracts

## Forecasting Direction
- the initial modeling problem is binary classification
- the prediction target is probability of `YES` resolution
- ranking is a downstream scoring layer, not the first predictive objective
- calibration quality matters as much as raw discrimination

## Feature Triage Principle
- split features into near-realtime and offline paths from day one
- near-realtime features support fast-path inference and ranking refreshes
- offline features support training, replay, and history-aware modeling
- shared feature definitions should exist even when storage and computation paths differ

## First-Pass Feature Philosophy
- start with stable structured features before adding embedding-heavy or speculative ones
- prefer features with clear point-in-time semantics over clever but leaky proxies
- allow provisional political-domain features in the catalog without forcing them into the first training run

## First Baseline Philosophy
- begin with one trivial benchmark, one interpretable model, and one stronger tabular model
- keep the first serious comparison honest by using the same stable feature subset across B1 and B2
- do not use live market price as a model input in v1
- require calibrated probabilities before downstream ranking

## Working Assumptions
- initial backend service layer can be a Python monorepo
- FastAPI is the first API surface
- PostgreSQL is the canonical store
- object storage is required for raw artifacts and payload archives
- vector retrieval is useful, but can follow canonical evidence storage
- Redis or a stream bus is needed once continuous updates start

## Proposed v1 Source Strategy

### Primary market data
- Polymarket Gamma API
- Polymarket CLOB public endpoints

### Primary structured political data
- GovInfo API, bulk data, and RSS
- Congress.gov API
- OpenFEC API and FEC bulk/download surfaces
- Official campaign, government, court, and agency feeds where directly available

### Broad discovery layer
- GDELT DOC 2.0 for news discovery and query expansion

### Secondary or later-stage sources
- YouTube Data API
- Reddit API
- AP Elections API as an optional paid election-data add-on

### Deferred by default
- X API
- unsupported scraping-heavy sources

## Proposed v1 Owner-Facing Risk Policy
- all outputs are visible to the owner
- ambiguity, contradiction, low-confidence, and low-trust-dominated cases receive explicit risk flags
- risky outputs can be deemphasized in ranking, but not hidden from the owner by policy
- there is no separate reviewer workflow in v1

## Ambiguity And Reliability Philosophy
- ambiguity is a scored property of market wording and resolution logic, not an informal vibe check
- source reliability is tiered and adjustable, but weaker sources remain visible for audit
- stronger sources should outweigh weaker sources in both evidence interpretation and risk signaling

## Proposed First Planning Slice
1. Lock down the domain boundaries and first supported market cohort
2. Translate the spec into system design artifacts:
   component map, event flow, schema, contracts, milestone backlog
3. Build the repository skeleton and local development baseline
4. Implement raw ingestion and replay-safe storage before agent work
5. Explore the captured data and refine canonical schemas and ELT mappings before deeper modeling work

## Decisions Already Implied By The Spec
- market price is a comparison baseline, not a model feature in v1
- skeptic analysis is mandatory for every market
- liquidity and spread are displayed but not included in ranking score
- the UI is a first-class product deliverable, not an afterthought
- feature storage needs both offline and online paths

## Main Risks To Plan Around
- ambiguous market resolution wording
- noisy-source contamination
- agent hallucination detached from evidence
- leakage in replay/backtesting
- excessive real-time compute cost
- product complexity outrunning initial implementation capacity

## Questions To Resolve Early
- Which features belong in the first model baseline?
- What latency target separates fast-path updates from deep refresh?
