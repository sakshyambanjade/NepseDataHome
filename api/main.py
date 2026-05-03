"""NepSense FastAPI application."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api.config import API_TITLE, API_VERSION
from api.routes import api_keys, auth, billing, coverage, devices, downloads, health, market, prices, symbols
from api.services.csv_service import ApiError

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=(
        "Historical NEPSE OHLCV data API for developers, researchers, brokers, "
        "and backtesting systems."
    ),
)


@app.exception_handler(ApiError)
def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    status_code = exc.status_code or (404 if exc.code.endswith("_NOT_FOUND") else 400)
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(api_keys.router)
app.include_router(devices.router)
app.include_router(billing.router)
app.include_router(symbols.router)
app.include_router(prices.router)
app.include_router(market.router)
app.include_router(coverage.router)
app.include_router(downloads.router)
