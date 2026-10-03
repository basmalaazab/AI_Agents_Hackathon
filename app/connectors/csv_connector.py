"""
CSV Connector — reads CSV files (uploaded or from disk) and returns
raw record dicts for ingestion.

Supports:
    - Sales / orders CSV
    - Customer records CSV
    - Product CSV
"""
from __future__ import annotations

import logging
from io import BytesIO, StringIO
from pathlib import Path
from typing import Any, Union

import pandas as pd

from app.connectors.base import BaseConnector

logger = logging.getLogger(__name__)


class CSVConnector(BaseConnector):
    """Connector for CSV file uploads and CSV files on disk."""

    source_type = "csv"

    def fetch(
        self,
        record_type: str,
        file_path: str | Path | None = None,
        file_content: bytes | None = None,
        **kwargs,
    ) -> list[dict]:
        """
        Parse a CSV into a list of raw dicts.

        Provide exactly one of `file_path` or `file_content`.
        """
        if file_content is not None:
            df = self._read_bytes(file_content)
        elif file_path is not None:
            df = pd.read_csv(str(file_path), dtype=str, keep_default_na=True)
        else:
            raise ValueError("CSVConnector.fetch requires file_path or file_content.")

        logger.info(
            "CSVConnector [%s] read %d rows for record_type=%s",
            self.source_name,
            len(df),
            record_type,
        )
        return df.to_dict(orient="records")

    @staticmethod
    def _read_bytes(content: bytes) -> pd.DataFrame:
        try:
            return pd.read_csv(BytesIO(content), dtype=str, keep_default_na=True)
        except UnicodeDecodeError:
            return pd.read_csv(
                BytesIO(content), dtype=str, keep_default_na=True, encoding="latin-1"
            )
