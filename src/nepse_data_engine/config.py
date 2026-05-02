from pathlib import Path

PROJECT_ROOT = Path.cwd()

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
CLEAN_DIR = DATA_DIR / "clean"
ADJUSTED_DIR = DATA_DIR / "adjusted"
MASTER_DIR = DATA_DIR / "master"
QUALITY_DIR = DATA_DIR / "quality"
CORPORATE_ACTIONS_DIR = DATA_DIR / "corporate_actions"

TODAY_SHARE_PRICE_URL = "https://www.sharesansar.com/today-share-price"

STANDARD_COLUMNS = [
"date",
"symbol",
"company_name",
"sector",
"open",
"high",
"low",
"close",
"volume",
"turnover",
"transactions",
"source",
]
