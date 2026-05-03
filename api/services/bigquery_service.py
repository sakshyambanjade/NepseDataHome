"""BigQuery service placeholder for the cloud phase."""

from __future__ import annotations


class BigQueryService:
    """Future BigQuery-backed implementation of the market data service."""

    def __init__(self, project_id: str | None = None, dataset: str | None = None):
        self.project_id = project_id
        self.dataset = dataset

    def is_configured(self) -> bool:
        return bool(self.project_id and self.dataset)

