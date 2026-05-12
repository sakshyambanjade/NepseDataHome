"""Configuration for NepSense."""

from pathlib import Path
from typing import Final
from zoneinfo import ZoneInfo

# Project paths
PROJECT_ROOT = Path.cwd()
DATA_DIR: Final = PROJECT_ROOT / "data"
RAW_DIR: Final = DATA_DIR / "raw"
NORMALIZED_DIR: Final = DATA_DIR / "normalized"
ADJUSTED_DIR: Final = DATA_DIR / "adjusted"
METADATA_DIR: Final = DATA_DIR / "metadata"
MASTER_DIR: Final = DATA_DIR / "master"
DASHBOARD_DIR: Final = PROJECT_ROOT / "web" / "public" / "data"
QUALITY_DIR: Final = DATA_DIR / "quality"

# Timezone
NEPAL_TZ: Final = ZoneInfo("Asia/Kathmandu")

# Data sources
SHARESANSAR_TODAY_URL: Final = "https://www.sharesansar.com/today-share-price"
SHARESANSAR_HISTORICAL_URL: Final = "https://www.sharesansar.com/company/{symbol}/price-history"
MEROLAGANI_COMPANY_LIST_URL: Final = "https://merolagani.com/CompanyList.aspx"

# Standard schemas
STANDARD_OHLCV_COLUMNS: Final = [
    "date",
    "symbol",
    "open",
    "high",
    "low",
    "close",
    "company_name",
    "sector",
    "volume",
    "turnover",
    "transactions",
    "source",
    "source_confidence",
]

STANDARD_ADJUSTED_COLUMNS: Final = STANDARD_OHLCV_COLUMNS + [
    "adjusted_open",
    "adjusted_high",
    "adjusted_low",
    "adjusted_close",
    "adjustment_factor",
]

# Source confidence scale
SOURCE_CONFIDENCE_SCALE = {
    "official": 1.00,           # Licensed/official data
    "reliable": 0.90,           # Reliable public source
    "archive": 0.70,            # Scraped archive
    "manual": 0.50,             # Manually recovered
    "uncertain": 0.20,          # Uncertain source
}

COMPANY_MASTER_COLUMNS: Final = [
    "symbol",
    "company_name",
    "sector",
    "listed_shares",
    "paidup_value",
    "total_paidup",
    "status",
    "first_seen",
    "last_seen",
]

SYMBOL_EVENTS_COLUMNS: Final = [
    "old_symbol",
    "new_symbol",
    "event_type",
    "event_date",
    "notes",
]

CORPORATE_ACTIONS_COLUMNS: Final = [
    "symbol",
    "book_close_date",
    "announcement_date",
    "action_type",
    "bonus_percent",
    "cash_dividend_percent",
    "right_ratio",
    "right_price",
    "source_url",
    "verified",
]

# Event types
EVENT_TYPES = {
    "IPO",
    "MERGER",
    "DELISTED",
    "RENAMED",
    "SUSPENDED",
    "SECTOR_CHANGED",
    "PROMOTER_TO_PUBLIC",
}

# Action types
ACTION_TYPES = {
    "BONUS",
    "RIGHT",
    "CASH_DIVIDEND",
    "SPLIT",
    "MERGER_SWAP",
    "FACE_VALUE_CHANGE",
}

# API configuration
API_HOST: Final = "0.0.0.0"
API_PORT: Final = 8000
API_WORKERS: Final = 4

# Logging
LOG_LEVEL: Final = "INFO"
LOG_FORMAT: Final = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
