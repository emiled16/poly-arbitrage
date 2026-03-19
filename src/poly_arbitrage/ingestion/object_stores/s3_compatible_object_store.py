from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from importlib import import_module
from typing import Any


@dataclass(slots=True)
class S3CompatibleObjectStore:
    endpoint_url: str
    access_key_id: str
    secret_access_key: str
    region_name: str = "us-east-1"
    session_token: str | None = None
    use_path_style: bool = True
    client_factory: Callable[[], Any] | None = None
    _client: Any = field(default=None, init=False, repr=False)

    def ensure_container(self, container_name: str) -> None:
        client = self._get_client()
        try:
            client.head_bucket(Bucket=container_name)
        except Exception:
            client.create_bucket(Bucket=container_name)

    def put_bytes(
        self,
        *,
        container_name: str,
        object_key: str,
        payload: bytes,
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> str:
        self.ensure_container(container_name)
        client = self._get_client()
        request: dict[str, Any] = {
            "Bucket": container_name,
            "Key": object_key,
            "Body": payload,
            "ContentType": content_type,
        }
        if metadata:
            request["Metadata"] = metadata
        client.put_object(**request)
        return f"s3://{container_name}/{object_key}"

    def get_bytes(self, *, container_name: str, object_key: str) -> bytes:
        response = self._get_client().get_object(Bucket=container_name, Key=object_key)
        return response["Body"].read()

    def _get_client(self) -> Any:
        if self._client is None:
            if self.client_factory is not None:
                self._client = self.client_factory()
            else:
                self._client = self._build_client()
        return self._client

    def _build_client(self) -> Any:
        boto3 = import_module("boto3")
        botocore_config = import_module("botocore.config")
        session = boto3.session.Session(
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            aws_session_token=self.session_token,
            region_name=self.region_name,
        )
        return session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            region_name=self.region_name,
            config=botocore_config.Config(
                signature_version="s3v4",
                s3={"addressing_style": "path" if self.use_path_style else "auto"},
            ),
        )
