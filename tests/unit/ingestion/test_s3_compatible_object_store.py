from __future__ import annotations

from poly_arbitrage.ingestion.object_stores.s3_compatible_object_store import (
    S3CompatibleObjectStore,
)


class FakeBody:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload

    def read(self) -> bytes:
        return self.payload


class FakeS3Client:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []
        self.container_exists = False

    def head_bucket(self, **kwargs: object) -> None:
        self.calls.append(("head_bucket", kwargs))
        if not self.container_exists:
            raise RuntimeError("missing bucket")

    def create_bucket(self, **kwargs: object) -> None:
        self.calls.append(("create_bucket", kwargs))
        self.container_exists = True

    def put_object(self, **kwargs: object) -> None:
        self.calls.append(("put_object", kwargs))

    def get_object(self, **kwargs: object) -> dict[str, object]:
        self.calls.append(("get_object", kwargs))
        return {"Body": FakeBody(b"payload")}


def test_s3_compatible_object_store_creates_container_and_puts_object() -> None:
    client = FakeS3Client()
    store = S3CompatibleObjectStore(
        endpoint_url="http://127.0.0.1:9000",
        access_key_id="minioadmin",
        secret_access_key="minioadmin",
        client_factory=lambda: client,
    )

    uri = store.put_bytes(
        container_name="raw",
        object_key="source=polymarket_gamma/dataset=markets/batch=batch-1.jsonl",
        payload=b"{}",
        content_type="application/x-ndjson",
        metadata={"job_id": "job-1"},
    )

    assert uri == "s3://raw/source=polymarket_gamma/dataset=markets/batch=batch-1.jsonl"
    assert client.calls[0] == ("head_bucket", {"Bucket": "raw"})
    assert client.calls[1] == ("create_bucket", {"Bucket": "raw"})
    assert client.calls[2][0] == "put_object"
    assert client.calls[2][1]["Bucket"] == "raw"
    assert client.calls[2][1]["Metadata"] == {"job_id": "job-1"}


def test_s3_compatible_object_store_reads_object_bytes() -> None:
    client = FakeS3Client()
    client.container_exists = True
    store = S3CompatibleObjectStore(
        endpoint_url="http://127.0.0.1:9000",
        access_key_id="minioadmin",
        secret_access_key="minioadmin",
        client_factory=lambda: client,
    )

    payload = store.get_bytes(
        container_name="raw",
        object_key="source=polymarket_gamma/dataset=markets/batch=batch-1.jsonl",
    )

    assert payload == b"payload"
