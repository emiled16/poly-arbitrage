from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import create_engine

from poly_arbitrage.ingestion.api import build_ingestion_api
from poly_arbitrage.ingestion.contracts import ObjectStore
from poly_arbitrage.ingestion.database.database import IngestionDatabase
from poly_arbitrage.ingestion.database.registry import RepositoryRegistry
from poly_arbitrage.ingestion.object_stores.local import LocalFilesystemObjectStore
from poly_arbitrage.ingestion.object_stores.s3 import S3CompatibleObjectStore
from poly_arbitrage.ingestion.queue.rabbitmq import RabbitMqQueue
from poly_arbitrage.ingestion.raw_storage.raw_batch_storage import RawBatchStorage
from poly_arbitrage.ingestion.registry import build_registry
from poly_arbitrage.ingestion.repositories.cursors import CursorRepository
from poly_arbitrage.ingestion.repositories.jobs import JobRepository
from poly_arbitrage.ingestion.repositories.schedules import ScheduleRepository
from poly_arbitrage.ingestion.scheduler import IngestionScheduler
from poly_arbitrage.ingestion.service import IngestionService
from poly_arbitrage.ingestion.settings import IngestionSettings
from poly_arbitrage.ingestion.sources.polymarket.handlers import build_polymarket_handlers
from poly_arbitrage.ingestion.workers.consumer import IngestionWorkerConsumer


@dataclass(slots=True)
class IngestionRuntime:
    database: IngestionDatabase
    repository_registry: RepositoryRegistry
    job_repository: JobRepository
    cursor_repository: CursorRepository
    schedule_repository: ScheduleRepository
    job_queue: RabbitMqQueue
    ingestion_service: IngestionService
    scheduler: IngestionScheduler
    worker: IngestionWorkerConsumer


def build_runtime(settings: IngestionSettings) -> IngestionRuntime:
    engine = create_engine(settings.postgres.dsn, future=True)
    database = IngestionDatabase(engine=engine)
    repository_registry = RepositoryRegistry(
        job_records=database.jobs,
        cursor_records=database.cursors,
        schedule_records=database.schedules,
    )
    job_repository = JobRepository(registry=repository_registry)
    cursor_repository = CursorRepository(registry=repository_registry)
    schedule_repository = ScheduleRepository(registry=repository_registry)
    job_queue = RabbitMqQueue(
        url=settings.rabbitmq.url,
        queue_name=settings.rabbitmq.queue_name,
        dead_letter_exchange=settings.rabbitmq.dead_letter_exchange,
        dead_letter_queue_name=settings.rabbitmq.dead_letter_queue_name,
    )
    source_registry = build_registry(build_polymarket_handlers())
    raw_storage = RawBatchStorage(
        object_store=build_object_store(settings),
        container_name=settings.raw_storage.container_name,
    )
    ingestion_service = IngestionService(
        job_repository=job_repository,
        cursor_repository=cursor_repository,
        source_registry=source_registry,
        raw_storage=raw_storage,
        retry_settings=settings.retry,
        job_queue=job_queue,
    )
    scheduler = IngestionScheduler(
        schedule_repository=schedule_repository,
        job_repository=job_repository,
        cursor_repository=cursor_repository,
        ingestion_service=ingestion_service,
    )
    worker = IngestionWorkerConsumer(
        job_queue=job_queue,
        ingestion_service=ingestion_service,
        worker_id=settings.worker_id,
    )
    return IngestionRuntime(
        database=database,
        repository_registry=repository_registry,
        job_repository=job_repository,
        cursor_repository=cursor_repository,
        schedule_repository=schedule_repository,
        job_queue=job_queue,
        ingestion_service=ingestion_service,
        scheduler=scheduler,
        worker=worker,
    )


def build_object_store(settings: IngestionSettings) -> ObjectStore:
    if settings.raw_storage.backend == "local":
        return LocalFilesystemObjectStore(root_directory=settings.raw_storage.local_root)

    if not settings.raw_storage.s3_access_key or not settings.raw_storage.s3_secret_key:
        raise ValueError("S3-compatible raw storage requires access key and secret key")

    return S3CompatibleObjectStore(
        endpoint_url=settings.raw_storage.s3_endpoint,
        access_key_id=settings.raw_storage.s3_access_key,
        secret_access_key=settings.raw_storage.s3_secret_key,
        region_name=settings.raw_storage.s3_region,
        session_token=settings.raw_storage.s3_session_token,
    )


def build_api_app(settings: IngestionSettings):
    runtime = build_runtime(settings)
    return build_ingestion_api(
        ingestion_service=runtime.ingestion_service,
        scheduler=runtime.scheduler,
        job_repository=runtime.job_repository,
        schedule_repository=runtime.schedule_repository,
    )
