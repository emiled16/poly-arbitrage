from __future__ import annotations

from uuid import uuid4

from poly_arbitrage.ingestion.models.job import IngestionJob
from poly_arbitrage.ingestion.models.request import IngestionRequest


def create_job(request: IngestionRequest) -> IngestionJob:
    return IngestionJob(
        job_id=uuid4().hex,
        source=request.source,
        dataset=request.dataset,
        params=dict(request.params),
        cursor=request.cursor,
    )
