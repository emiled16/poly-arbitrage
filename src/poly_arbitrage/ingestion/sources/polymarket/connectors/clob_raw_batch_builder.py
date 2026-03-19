from __future__ import annotations

from collections.abc import Mapping

from poly_arbitrage.ingestion.factories.raw_record_factory import build_raw_record
from poly_arbitrage.ingestion.models.batch import IngestionBatch
from poly_arbitrage.ingestion.models.job import IngestionJob
from poly_arbitrage.ingestion.sources.polymarket.protocols.json_http_client import JsonHttpClient


def build_clob_batch(
    *,
    http_client: JsonHttpClient,
    base_url: str,
    source_name: str,
    dataset_name: str,
    job: IngestionJob,
) -> IngestionBatch:
    token_id = job.params.get("token_id")
    if not isinstance(token_id, str) or not token_id:
        raise ValueError("CLOB ingestion jobs require a non-empty token_id")

    endpoint = f"{base_url}/{dataset_name}"
    payload = http_client.get_json(
        endpoint,
        params={"token_id": token_id},
    )

    record = build_raw_record(
        source=source_name,
        dataset=dataset_name,
        job_id=job.job_id,
        endpoint=endpoint,
        request_params={"token_id": token_id},
        payload=payload,
        cursor=job.cursor,
        metadata={
            "response_shape": response_shape(payload),
            "token_id": token_id,
        },
    )

    return IngestionBatch(
        source=source_name,
        dataset=dataset_name,
        job_id=job.job_id,
        records=[record],
    )


def response_shape(payload: object) -> str:
    if isinstance(payload, list):
        return "list"
    if isinstance(payload, Mapping):
        return "object"
    return type(payload).__name__
