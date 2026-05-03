"""API configuration."""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
HISTORY_DIR = DATA_DIR / "history"
MASTER_DIR = DATA_DIR / "master"
METADATA_DIR = DATA_DIR / "metadata"
QUALITY_DIR = DATA_DIR / "quality"
BILLING_DB = Path(os.getenv("NEPSENSE_BILLING_DB", DATA_DIR / "billing.sqlite3"))

ALL_PRICES_CSV = HISTORY_DIR / "nepse_all_prices.csv"
MANIFEST_JSON = HISTORY_DIR / "manifest.json"
COMPANY_MASTER_CSV = METADATA_DIR / "company_master.csv"

API_TITLE = "NepSense Historical Market Data API"
API_VERSION = "0.1.0"
API_SOURCE_NAME = "NepSense"
NEPAL_TIMEZONE = "Asia/Kathmandu"

MAX_QUERY_LIMIT = int(os.getenv("NEPSENSE_MAX_QUERY_LIMIT", "10000"))
DEFAULT_QUERY_LIMIT = int(os.getenv("NEPSENSE_DEFAULT_QUERY_LIMIT", "5000"))

APP_BASE_URL = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:8000")
KHALTI_SECRET_KEY = os.getenv("KHALTI_SECRET_KEY", "")
KHALTI_PUBLIC_KEY = os.getenv("KHALTI_PUBLIC_KEY", "")
KHALTI_INIT_URL = os.getenv(
    "KHALTI_INIT_URL",
    "https://dev.khalti.com/api/v2/epayment/initiate/",
)
KHALTI_LOOKUP_URL = os.getenv(
    "KHALTI_LOOKUP_URL",
    "https://dev.khalti.com/api/v2/epayment/lookup/",
)
