from __future__ import annotations

from typing import Protocol


class ObjectStore(Protocol):
    def ensure_container(self, container_name: str) -> None:
        """Ensure the named container exists."""

    def put_bytes(
        self,
        *,
        container_name: str,
        object_key: str,
        payload: bytes,
        content_type: str,
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Persist one object and return a stable object URI."""

    def get_bytes(self, *, container_name: str, object_key: str) -> bytes:
        """Read one object payload."""

