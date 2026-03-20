# Next Steps: Ingestion Refactor

Date: 2026-03-19

Purpose:
This file is the implementation checklist for making the current ingestion code production-grade and materially cleaner, based on the findings in [review.md](/Users/emdim/dev/poly-arbitrage/review.md).

## Phase 1: Lock The Intended Behavior

### Task 1. Choose one ingestion contract per dataset
- Decide, per dataset, whether production behavior is:
  - recurring full snapshot polling
  - recurring incremental change capture
- Do not keep the current hybrid behavior for recurring Gamma ingestion.
- Record the decision in:
  - `.vibe/key-decisions.md`
  - `.vibe/system-design.md`
  - `README.md`

Suggested default:
- `polymarket_gamma/markets`: choose either full snapshot polling or strict watermark-based incremental polling
- `polymarket_clob/book`: define separately from market discovery
- `polymarket_clob/midpoint`: define separately from market discovery

### Task 2. Define the ingestion invariants in writing
- Write a short architecture note that states:
  - who owns a checkpoint
  - when a cursor may advance
  - whether offset is allowed in recurring runs
  - whether paginated sweeps must complete in one logical run
  - how retries interact with cursor advancement
- Store this in `.vibe/system-design.md` or a dedicated ingestion design note under `docs/`.

## Phase 2: Fix Cursor And Checkpoint Semantics

### Task 3. Remove legacy offset mode from recurring Gamma ingestion
- Stop using persistent `offset` as the checkpoint for recurring scheduled Gamma runs.
- Keep offset pagination only for explicit backfill workflows if still needed.
- Make recurring Gamma runs default to the chosen production mode without compatibility ambiguity.

### Task 4. Split checkpoint ownership by workflow
- Replace the current global cursor model keyed only by `(source, dataset)`.
- Introduce a checkpoint key that reflects the actual owner of the cursor.

Acceptable ownership models:
- per schedule
- per logical partition/filter
- per source + dataset + normalized params hash

Non-goal:
- manual backfills and recurring schedules must not share the same checkpoint row.

### Task 5. Add concurrency-safe cursor advancement
- Prevent two workers or two schedule runs from racing the same checkpoint.
- Implement one of:
  - compare-and-set cursor updates
  - schedule-level exclusive ownership
  - one-active-job-per-checkpoint enforcement
  - explicit partitioned work assignment
- Add tests for stale writes and lost-update prevention.

## Phase 3: Simplify Gamma Ingestion Model

### Task 6. If incremental polling is kept, make one run drain the full sweep
- A paginated watermark sweep must complete inside one logical ingestion run.
- Do not fetch page 1 now and page 2 on the next schedule tick.
- Only persist the final committed watermark after the sweep is complete.
- Ensure retry behavior for partial sweeps is explicitly defined.

### Task 7. If full snapshot polling is chosen, remove persisted recurring cursors for Gamma markets
- Each recurring run should start from a clean query.
- Store the raw snapshot as an immutable archive artifact.
- Let downstream ELT or diffing logic detect changes between snapshots.
- Do not keep recurring state in the form of a growing offset cursor.

### Task 8. Remove dead hybrid paths after the contract is chosen
- Delete or isolate compatibility logic that keeps the handler in an ambiguous state.
- Minimize the number of code paths in:
  - `src/poly_arbitrage/ingestion/sources/polymarket/handlers.py`
  - `scripts/ingest_polymarket.py`
  - scheduler submission logic

Goal:
- one obvious production path
- one explicit backfill path if needed

## Phase 4: Fix Submission Paths And Schedule Execution

### Task 9. Fix CLI defaults to match the production ingestion contract
- Remove implicit `offset=0` from normal Gamma job submission.
- Introduce an explicit backfill flag or mode if offset pagination remains supported.
- Make the CLI behavior consistent with the documentation.

### Task 10. Fix API defaults to match the production ingestion contract
- Review schedule creation and manual job submission paths.
- Ensure API-created recurring Gamma schedules do not accidentally enter legacy offset mode.
- Validate incompatible parameter combinations early.

### Task 11. Make due-schedule claiming atomic
- Prevent duplicate enqueueing when multiple scheduler processes or repeated admin calls exist.
- Claim and advance the schedule in one transactional step, or use row-level locking.
- Ensure the same due schedule cannot be enqueued twice for the same intended run.

### Task 12. Add deterministic idempotency keys for scheduler-created jobs
- Scheduled jobs should have deterministic keys derived from:
  - schedule identity
  - run window / due time
  - logical partition if relevant
- Use this to collapse duplicate enqueue attempts safely.

## Phase 5: Separate Dataset Responsibilities

### Task 13. Separate discovery ingestion from per-market or per-token detail ingestion
- Treat market discovery datasets differently from token-level detail datasets.
- Do not force `markets`, `book`, and `midpoint` into the same checkpointing model.

Expected outcome:
- `markets` or `events` ingestion has one clearly defined cadence and checkpoint strategy
- `book` and `midpoint` have their own operational strategy

### Task 14. Define downstream fan-out boundaries
- Decide how market discovery drives downstream detail fetches.
- Define whether new or changed markets produce follow-up jobs for:
  - token order books
  - token midpoint snapshots
- Keep this orchestration separate from the checkpoint semantics of the discovery feed itself.

## Phase 6: Add Production-Grade Observability

### Task 15. Add structured metrics and logs for ingestion correctness
- Record per run:
  - checkpoint before
  - checkpoint after
  - query mode
  - page count
  - rows fetched
  - rows kept after filtering
  - rows dropped as already-seen
  - `has_more`
  - duration
  - retries
  - duplicate enqueue events

### Task 16. Add freshness and lag monitoring
- Define freshness expectations for each dataset.
- Track:
  - last successful run time
  - time since last successful ingestion
  - backlog depth
  - repeated retry/dead-letter events

## Phase 7: Expand Test Coverage Around Real Failure Modes

### Task 17. Add tests for checkpoint isolation
- Multiple schedules on the same source/dataset with different params
- Manual backfill and recurring schedule coexisting
- Independent checkpoint progression without overwrite

### Task 18. Add tests for multi-page Gamma behavior
- Full sweep draining in one logical run
- Safe behavior when new items arrive at the top during pagination
- Retry semantics for a partially completed multi-page sweep

### Task 19. Add tests for scheduler race conditions
- Duplicate due schedule selection
- Atomic claim behavior
- Idempotency behavior for scheduler-generated jobs

### Task 20. Add tests for submission-mode correctness
- CLI default path for recurring Gamma
- API default path for recurring Gamma
- Explicit backfill mode behavior
- Validation of invalid param combinations

### Task 21. Add tests for cursor update safety
- Compare-and-set failures
- stale checkpoint writes
- concurrent worker attempts against the same checkpoint owner

## Phase 8: Documentation And Cleanup

### Task 22. Update the README after behavior is fixed
- Document the actual production behavior.
- Remove any wording that implies watermark mode while the CLI or API still defaults to offset mode.
- Include one canonical example for:
  - normal recurring production ingestion
  - backfill ingestion

### Task 23. Update `.vibe` project records
- Record the final checkpoint strategy in `.vibe/key-decisions.md`.
- Update `.vibe/system-design.md` with the final ingestion flow.
- Update `.vibe/plan.md` with the refactor work breakdown and status.
- Log progress after each completed implementation slice in `.vibe/logs.md`.

### Task 24. Remove obsolete code paths after verification
- After tests pass and behavior is stable:
  - remove stale cursor branches
  - remove unused compatibility helpers
  - remove misleading config or docs

Goal:
- the production ingestion path should be small, explicit, and easy to reason about.

## Suggested Execution Order

1. Decide the contract for `polymarket_gamma/markets`
2. Define checkpoint ownership model
3. Fix CLI/API defaults
4. Refactor Gamma run semantics around the chosen model
5. Make scheduler claiming atomic and idempotent
6. Add concurrency-safe cursor advancement
7. Expand tests around races, sweeps, and schedule isolation
8. Update docs and remove dead branches

## Definition Of Done

The refactor is done when all of the following are true:

- recurring Gamma ingestion has one clear production mode
- manual backfills do not interfere with recurring production checkpoints
- due schedules cannot be duplicated by scheduler races
- cursor advancement is safe under concurrent execution
- CLI/API defaults match the documented behavior
- tests cover multi-page sweeps, schedule isolation, and duplicate enqueue prevention
- the production ingestion path is materially simpler than the current hybrid implementation
