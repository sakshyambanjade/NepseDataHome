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
WEB_DIST_DIR = PROJECT_ROOT / "web" / "dist"
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
ESEWA_MERCHANT_CODE = os.getenv("ESEWA_MERCHANT_CODE", "EPAYTEST")
ESEWA_SECRET_KEY = os.getenv("ESEWA_SECRET_KEY", "")
ESEWA_INIT_URL = os.getenv(
    "ESEWA_INIT_URL",
    "https://rc-epay.esewa.com.np/api/epay/main/v2/form",
)
ESEWA_VERIFY_URL = os.getenv(
    "ESEWA_VERIFY_URL",
    "https://rc-epay.esewa.com.np/api/epay/transaction/status/",
)
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

AUTH_TOKEN_SECRET = os.getenv("NEPSENSE_AUTH_TOKEN_SECRET", "dev-insecure-change-me")
AUTH_TOKEN_EXP_MINUTES = int(os.getenv("NEPSENSE_AUTH_TOKEN_EXP_MINUTES", "10080"))
