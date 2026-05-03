"""Health routes."""

from __future__ import annotations

from fastapi import APIRouter

from api.config import API_VERSION
from api.services.csv_service import load_manifest, now_nepal

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    manifest = load_manifest()
    return {
        "status": "ok",
        "version": API_VERSION,
        "dataset": {
            "rows": manifest.get("rows"),
            "symbols": manifest.get("symbols"),
            "date_range": manifest.get("date_range"),
        },
        "checked_at": now_nepal(),
    }

