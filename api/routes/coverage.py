"""Coverage and credibility routes."""

from __future__ import annotations

from fastapi import APIRouter

from api.services.csv_service import anomalies, coverage, data_quality, load_manifest, sources

router = APIRouter(prefix="/api/v1", tags=["coverage"])


@router.get("/coverage")
def coverage_report() -> dict:
    return coverage()


@router.get("/metadata")
def metadata() -> dict:
    return {"meta": {}, "data": load_manifest()}


@router.get("/data-quality")
def quality() -> dict:
    return data_quality()


@router.get("/sources")
def source_distribution() -> dict:
    return sources()


@router.get("/anomalies")
def anomaly_report() -> dict:
    return anomalies()

