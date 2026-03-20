from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class LocalFilesystemObjectStore:
    root_directory: Path

    def ensure_container(self, container_name: str) -> None:
        self._resolve_container_path(container_name).mkdir(parents=True, exist_ok=True)

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
        path = self._resolve_object_path(container_name=container_name, object_key=object_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)

        metadata_path = path.with_name(f"{path.name}.metadata.json")
        metadata_path.write_text(
            json.dumps(
                {
                    "content_type": content_type,
                    "metadata": metadata or {},
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        return path.resolve().as_uri()

    def get_bytes(self, *, container_name: str, object_key: str) -> bytes:
        path = self._resolve_object_path(container_name=container_name, object_key=object_key)
        return path.read_bytes()

    def _resolve_container_path(self, container_name: str) -> Path:
        return self.root_directory / container_name

    def _resolve_object_path(self, *, container_name: str, object_key: str) -> Path:
        normalized_parts = [part for part in object_key.split("/") if part and part != "."]
        return self._resolve_container_path(container_name).joinpath(*normalized_parts)
