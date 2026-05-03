"""Download routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from api.config import ALL_PRICES_CSV, MASTER_DIR
from api.services.auth_dependency import require_credits
from api.services.csv_service import ApiError, symbol_csv_path

router = APIRouter(prefix="/api/v1/download", tags=["downloads"])


@router.get("/latest.csv")
def download_latest_csv() -> FileResponse:
    if not ALL_PRICES_CSV.exists():
        raise ApiError("DOWNLOAD_NOT_FOUND", "Latest CSV file is missing")
    return FileResponse(ALL_PRICES_CSV, media_type="text/csv", filename="nepsense_latest.csv")


@router.get("/latest.parquet")
def download_latest_parquet(_: dict = Depends(require_credits(1000))) -> FileResponse:
    path = MASTER_DIR / "nepsense_prices.parquet"
    if not path.exists():
        raise ApiError("DOWNLOAD_NOT_FOUND", "Latest Parquet file is missing")
    return FileResponse(path, media_type="application/octet-stream", filename="nepsense_latest.parquet")


@router.get("/{symbol}.csv")
def download_symbol_csv(symbol: str, _: dict = Depends(require_credits(20))) -> FileResponse:
    path = symbol_csv_path(symbol)
    return FileResponse(path, media_type="text/csv", filename=f"{symbol.upper()}.csv")
