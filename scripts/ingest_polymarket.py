from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from poly_arbitrage.ingestion.dispatchers.ingestion_dispatcher import IngestionDispatcher
from poly_arbitrage.ingestion.models.request import IngestionRequest
from poly_arbitrage.ingestion.queues.in_memory_job_queue import InMemoryJobQueue
from poly_arbitrage.ingestion.raw_sinks.local_jsonl_raw_sink import LocalJsonlRawSink
from poly_arbitrage.ingestion.sources.polymarket.connector_registry import (
    build_polymarket_connector_registry,
)
from poly_arbitrage.ingestion.state_stores.in_memory_state_store import InMemoryStateStore
from poly_arbitrage.ingestion.utils.serialization import serialize_value
from poly_arbitrage.ingestion.workers.ingestion_worker import IngestionWorker


def main() -> None:
    parser = argparse.ArgumentParser(description="Dispatch and process one raw Polymarket ingestion job.")
    parser.add_argument(
        "--source",
        default="polymarket_gamma",
        choices=["polymarket_gamma", "polymarket_clob"],
        help="Source connector to run.",
    )
    parser.add_argument(
        "--dataset",
        default="markets",
        choices=["markets", "book", "midpoint"],
        help="Dataset for the selected source.",
    )
    parser.add_argument("--limit", type=int, default=5, help="Number of Gamma markets to fetch.")
    parser.add_argument("--offset", type=int, default=0, help="Gamma pagination offset.")
    parser.add_argument("--token-id", help="Token id for CLOB book or midpoint ingestion.")
    parser.add_argument(
        "--output-dir",
        default="artifacts/datasets/raw",
        help="Local raw sink root used as a stand-in for object storage.",
    )
    args = parser.parse_args()

    if args.source == "polymarket_gamma" and args.dataset != "markets":
        parser.error("polymarket_gamma only supports the markets dataset")

    if args.source == "polymarket_clob" and args.dataset not in {"book", "midpoint"}:
        parser.error("polymarket_clob only supports the book and midpoint datasets")

    if args.source == "polymarket_clob" and not args.token_id:
        parser.error("--token-id is required for polymarket_clob jobs")

    params = _build_params(args)
    connectors = build_polymarket_connector_registry()
    queue = InMemoryJobQueue()
    dispatcher = IngestionDispatcher(connectors=connectors, job_queue=queue)
    state_store = InMemoryStateStore()
    raw_sink = LocalJsonlRawSink(root_directory=ROOT / args.output_dir)
    worker = IngestionWorker(
        connectors=connectors,
        job_queue=queue,
        raw_sink=raw_sink,
        state_store=state_store,
    )
    job = dispatcher.dispatch(
        IngestionRequest(
            source=args.source,
            dataset=args.dataset,
            params=params,
        )
    )
    processed = worker.process_next()
    print(json.dumps(serialize_value({"job": job, "processed": processed}), indent=2))


def _build_params(args: argparse.Namespace) -> dict[str, object]:
    if args.source == "polymarket_gamma":
        return {
            "active": True,
            "closed": False,
            "limit": args.limit,
            "offset": args.offset,
        }
    return {"token_id": args.token_id}


if __name__ == "__main__":
    main()
