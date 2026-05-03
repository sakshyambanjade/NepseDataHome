"""Cloud Storage service placeholder for dataset downloads."""

from __future__ import annotations


class StorageService:
    """Future GCS-backed implementation for CSV/Parquet/DuckDB objects."""

    def __init__(self, bucket_name: str | None = None):
        self.bucket_name = bucket_name

    def is_configured(self) -> bool:
        return bool(self.bucket_name)

