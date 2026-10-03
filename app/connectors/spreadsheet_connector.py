"""
Spreadsheet connector — interface for spreadsheet-based data sources.

Currently implemented for local CSV/Excel files.
Provides an extension point for Google Sheets integration.

To enable Google Sheets:
1. Set GOOGLE_SHEETS_CREDENTIALS_FILE and GOOGLE_SHEETS_TOKEN_FILE in .env
2. Install: pip install google-auth google-auth-oauthlib google-api-python-client
3. Implement the _fetch_google_sheets() method below
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from app.connectors.base import BaseConnector
from app.config import get_settings

logger = logging.getLogger(__name__)


class SpreadsheetConnector(BaseConnector):
    """
    Connector for spreadsheet data sources.

    Supported backends:
    - local_excel: reads a local .xlsx / .xls file
    - google_sheets: [NOT YET IMPLEMENTED — requires Google API credentials]
    """

    source_type = "spreadsheet"

    def fetch(
        self,
        record_type: str,
        file_path: str | Path | None = None,
        sheet_name: str | int = 0,
        spreadsheet_id: str | None = None,
        **kwargs,
    ) -> list[dict]:
        settings = get_settings()

        if file_path is not None:
            return self._fetch_local_excel(file_path, sheet_name)

        if spreadsheet_id is not None:
            if (
                settings.google_sheets_credentials_file
                and Path(settings.google_sheets_credentials_file).exists()
            ):
                return self._fetch_google_sheets(spreadsheet_id, sheet_name)
            else:
                raise NotImplementedError(
                    "Google Sheets integration requires GOOGLE_SHEETS_CREDENTIALS_FILE "
                    "and GOOGLE_SHEETS_TOKEN_FILE to be configured. "
                    "See connectors/spreadsheet_connector.py for setup instructions."
                )

        raise ValueError(
            "SpreadsheetConnector.fetch requires file_path or spreadsheet_id."
        )

    def _fetch_local_excel(
        self, file_path: str | Path, sheet_name: str | int
    ) -> list[dict]:
        df = pd.read_excel(str(file_path), sheet_name=sheet_name, dtype=str)
        logger.info(
            "SpreadsheetConnector read %d rows from %s (sheet=%s)",
            len(df),
            file_path,
            sheet_name,
        )
        return df.to_dict(orient="records")

    def _fetch_google_sheets(
        self, spreadsheet_id: str, sheet_name: str | int
    ) -> list[dict]:
        """
        Extension point for Google Sheets.

        To implement:
        1. pip install google-auth google-auth-oauthlib google-api-python-client
        2. Follow OAuth 2.0 setup at:
           https://developers.google.com/sheets/api/quickstart/python
        3. Use build('sheets', 'v4', credentials=creds).spreadsheets().values().get(...)
        """
        raise NotImplementedError(
            "Google Sheets fetch is not yet implemented. "
            "See the docstring in _fetch_google_sheets() for instructions."
        )
