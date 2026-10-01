"""
Mock API Connector — calls the local mock e-commerce REST API.

The mock API simulates data from an external e-commerce platform.
This connector is clearly labelled as mock / synthetic data.
No real external platform credentials are required.

To add a real integration (e.g. Shopify), create a new connector that
inherits from BaseConnector and implements the fetch() method using
the platform's official API.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.connectors.base import BaseConnector
from app.config import get_settings

logger = logging.getLogger(__name__)


class MockAPIConnector(BaseConnector):
    """
    Connector for the local mock e-commerce REST API.

    ⚠️  THIS IS SYNTHETIC DATA — NOT CONNECTED TO ANY REAL PLATFORM.
    """

    source_type = "mock_api"

    ENDPOINTS: dict[str, str] = {
        "order": "/orders",
        "customer": "/customers",
        "product": "/products",
    }

    def __init__(self, source_name: str, config: dict[str, Any] | None = None):
        super().__init__(source_name, config)
        settings = get_settings()
        self.base_url = self.config.get("base_url", settings.mock_api_url)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        reraise=True,
    )
    def fetch(self, record_type: str, since: str | None = None, **kwargs) -> list[dict]:
        """
        Fetch records from the mock API.

        Args:
            record_type: 'order', 'customer', or 'product'.
            since: ISO datetime string for incremental ingestion (optional).
        """
        endpoint = self.ENDPOINTS.get(record_type)
        if endpoint is None:
            raise ValueError(
                f"MockAPIConnector does not support record_type={record_type!r}. "
                f"Valid types: {list(self.ENDPOINTS)}"
            )

        params: dict[str, str] = {}
        if since:
            params["since"] = since

        url = f"{self.base_url}{endpoint}"
        logger.info("MockAPIConnector fetching %s from %s", record_type, url)

        with httpx.Client(timeout=15) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        records = data if isinstance(data, list) else data.get("data", [])
        logger.info(
            "MockAPIConnector [%s] fetched %d %s record(s).",
            self.source_name,
            len(records),
            record_type,
        )
        return records

    def health_check(self) -> bool:
        try:
            with httpx.Client(timeout=5) as client:
                r = client.get(f"{self.base_url}/health")
                return r.status_code == 200
        except Exception:
            return False
