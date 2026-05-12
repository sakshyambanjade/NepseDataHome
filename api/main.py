"""NepSense FastAPI application."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from api.config import API_TITLE, API_VERSION, WEB_DIST_DIR
from api.routes import api_keys, auth, billing, coverage, devices, downloads, health, market, platform, prices, symbols
from api.services.csv_service import ApiError

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
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
app.include_router(platform.router)


if WEB_DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIST_DIR / "assets"), name="web-assets")

    @app.get("/", include_in_schema=False)
    def web_root() -> FileResponse:
        return FileResponse(WEB_DIST_DIR / "index.html")

    @app.get(
        "/{full_path:path}",
        include_in_schema=False,
    )
    def web_spa(full_path: str) -> Response:
        if full_path.startswith("api/"):
            return JSONResponse(status_code=404, content={"error": {"code": "NOT_FOUND", "message": "Not found"}})
        return FileResponse(WEB_DIST_DIR / "index.html")
