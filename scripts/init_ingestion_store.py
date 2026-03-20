from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> None:
    from alembic import command
    from alembic.config import Config
    from poly_arbitrage.ingestion.runtime import build_object_store
    from poly_arbitrage.ingestion.settings import IngestionSettings

    settings = IngestionSettings()
    alembic_config = Config(str(ROOT / "alembic.ini"))
    alembic_config.set_main_option("script_location", str(ROOT / "alembic"))
    alembic_config.set_main_option("sqlalchemy.url", settings.postgres.dsn)
    command.upgrade(alembic_config, "head")

    object_store = build_object_store(settings)
    object_store.ensure_container(settings.raw_storage.container_name)


if __name__ == "__main__":
    main()
