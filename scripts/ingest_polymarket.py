from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    from poly_arbitrage.ingestion.models.request import IngestionRequest
    from poly_arbitrage.ingestion.runtime import build_runtime
    from poly_arbitrage.ingestion.settings import IngestionSettings

    parser = argparse.ArgumentParser(description="Submit one Polymarket ingestion job.")
    parser.add_argument(
        "--source",
        default="polymarket_gamma",
        choices=["polymarket_gamma", "polymarket_clob"],
    )
    parser.add_argument(
        "--dataset",
        default="markets",
        choices=["markets", "book", "midpoint"],
    )
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--offset", type=int)
    parser.add_argument(
        "--backfill",
        action="store_true",
        help="Use explicit offset-based Gamma backfill mode.",
    )
    parser.add_argument("--checkpoint-key")
    parser.add_argument("--token-id")
    parser.add_argument("--trigger", default="cli")
    args = parser.parse_args()

    if args.source == "polymarket_gamma" and args.dataset != "markets":
        parser.error("polymarket_gamma only supports the markets dataset")

    if args.source == "polymarket_clob" and args.dataset not in {"book", "midpoint"}:
        parser.error("polymarket_clob only supports the book and midpoint datasets")

    if args.source == "polymarket_clob" and not args.token_id:
        parser.error("--token-id is required for polymarket_clob jobs")

    if args.source != "polymarket_gamma" and args.backfill:
        parser.error("--backfill is only supported for polymarket_gamma markets jobs")

    if args.source == "polymarket_gamma" and args.dataset != "markets" and args.backfill:
        parser.error("--backfill is only supported for polymarket_gamma markets jobs")

    if (
        args.source == "polymarket_gamma"
        and args.dataset == "markets"
        and args.offset is not None
        and not args.backfill
    ):
        parser.error("--offset requires --backfill")

    runtime = build_runtime(IngestionSettings())
    job = runtime.ingestion_service.submit_request(
        IngestionRequest(
            source=args.source,
            dataset=args.dataset,
            params=build_params(args),
            checkpoint_key=args.checkpoint_key,
            trigger=args.trigger,
        )
    )
    print(json.dumps({"job_id": job.job_id, "status": job.status.value}, indent=2))


def build_params(args: argparse.Namespace) -> dict[str, object]:
    if args.source == "polymarket_gamma":
        params: dict[str, object] = {
            "active": True,
            "closed": False,
            "limit": args.limit,
            "mode": "backfill" if args.backfill else "snapshot",
        }
        if args.backfill:
            params["offset"] = args.offset or 0
        return params
    return {"token_id": args.token_id}


if __name__ == "__main__":
    main()
