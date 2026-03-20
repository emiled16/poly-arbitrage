from __future__ import annotations

from argparse import Namespace
from uuid import uuid4

import pytest

from poly_arbitrage.ingestion.models.request import IngestionRequest
from poly_arbitrage.ingestion.models.schedule import IngestionSchedule
from poly_arbitrage.ingestion.submission import normalize_request, validate_schedule
from scripts.ingest_polymarket import build_params


def test_cli_build_params_defaults_gamma_to_snapshot_mode() -> None:
    params = build_params(
        Namespace(
            source="polymarket_gamma",
            backfill=False,
            limit=100,
            offset=None,
            token_id=None,
        )
    )

    assert params == {
        "active": True,
        "closed": False,
        "limit": 100,
        "mode": "snapshot",
    }


def test_cli_build_params_supports_explicit_gamma_backfill_mode() -> None:
    params = build_params(
        Namespace(
            source="polymarket_gamma",
            backfill=True,
            limit=100,
            offset=250,
            token_id=None,
        )
    )

    assert params == {
        "active": True,
        "closed": False,
        "limit": 100,
        "mode": "backfill",
        "offset": 250,
    }


def test_snapshot_request_rejects_offset_mode_inputs() -> None:
    with pytest.raises(ValueError, match="offset"):
        normalize_request(
            IngestionRequest(
                source="polymarket_gamma",
                dataset="markets",
                params={"limit": 100, "offset": 0},
            )
        )


def test_schedule_validation_rejects_gamma_backfill_mode() -> None:
    with pytest.raises(ValueError, match="snapshot mode"):
        validate_schedule(
            IngestionSchedule(
                schedule_id=uuid4().hex,
                name="gamma-backfill",
                source="polymarket_gamma",
                dataset="markets",
                cadence_seconds=60,
                params={"limit": 100, "mode": "backfill", "offset": 0},
            )
        )
