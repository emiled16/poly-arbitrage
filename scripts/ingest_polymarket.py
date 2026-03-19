from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    from poly_arbitrage.ingestion.dispatchers.ingestion_dispatcher import IngestionDispatcher
    from poly_arbitrage.ingestion.models.request import IngestionRequest
    from poly_arbitrage.ingestion.queues.in_memory_job_queue import InMemoryJobQueue
    from poly_arbitrage.ingestion.raw_sinks.object_store_raw_sink import ObjectStoreRawSink
    from poly_arbitrage.ingestion.sources.polymarket.connector_registry import (
        build_polymarket_connector_registry,
    )
    from poly_arbitrage.ingestion.state_stores.local_jsonl_state_store import (
        LocalJsonlStateStore,
    )
    from poly_arbitrage.ingestion.utils.serialization import serialize_value
    from poly_arbitrage.ingestion.workers.ingestion_worker import IngestionWorker

    parser = argparse.ArgumentParser(
        description="Dispatch and process one raw Polymarket ingestion job."
    )
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
        "--raw-store-backend",
        default="local",
        choices=["local", "minio"],
        help="Raw object-store backend to use.",
    )
    parser.add_argument(
        "--raw-store-root",
        default="artifacts/datasets",
        help="Root directory used by the local object-store backend.",
    )
    parser.add_argument(
        "--raw-store-container",
        default="raw",
        help="Container or bucket name used for raw payload archives.",
    )
    parser.add_argument(
        "--state-dir",
        default="artifacts/state/ingestion",
        help="Directory where durable local ingestion state logs are appended.",
    )
    parser.add_argument(
        "--minio-endpoint",
        default=os.getenv("POLY_ARB_MINIO_ENDPOINT", "http://127.0.0.1:9000"),
        help="MinIO S3-compatible endpoint URL.",
    )
    parser.add_argument(
        "--minio-access-key",
        default=os.getenv("POLY_ARB_MINIO_ACCESS_KEY"),
        help="MinIO access key. Falls back to POLY_ARB_MINIO_ACCESS_KEY.",
    )
    parser.add_argument(
        "--minio-secret-key",
        default=os.getenv("POLY_ARB_MINIO_SECRET_KEY"),
        help="MinIO secret key. Falls back to POLY_ARB_MINIO_SECRET_KEY.",
    )
    parser.add_argument(
        "--minio-region",
        default=os.getenv("POLY_ARB_MINIO_REGION", "us-east-1"),
        help="Region name used by the MinIO S3-compatible client.",
    )
    parser.add_argument(
        "--minio-session-token",
        default=os.getenv("POLY_ARB_MINIO_SESSION_TOKEN"),
        help="Optional MinIO session token.",
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
    state_store = LocalJsonlStateStore(root_directory=ROOT / args.state_dir)
    raw_sink = ObjectStoreRawSink(
        object_store=_build_object_store(args),
        container_name=args.raw_store_container,
    )
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


def _build_object_store(args: argparse.Namespace) -> object:
    from poly_arbitrage.ingestion.object_stores.local_filesystem_object_store import (
        LocalFilesystemObjectStore,
    )
    from poly_arbitrage.ingestion.object_stores.s3_compatible_object_store import (
        S3CompatibleObjectStore,
    )

    if args.raw_store_backend == "local":
        return LocalFilesystemObjectStore(root_directory=ROOT / args.raw_store_root)

    if not args.minio_access_key or not args.minio_secret_key:
        raise ValueError("MinIO backend requires both access key and secret key")

    return S3CompatibleObjectStore(
        endpoint_url=args.minio_endpoint,
        access_key_id=args.minio_access_key,
        secret_access_key=args.minio_secret_key,
        region_name=args.minio_region,
        session_token=args.minio_session_token,
    )


if __name__ == "__main__":
    main()
