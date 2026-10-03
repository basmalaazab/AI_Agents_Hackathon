"""Read-only connector for HubSpot CRM contacts and products."""
from __future__ import annotations

from typing import Any

import httpx

from app.connectors.base import BaseConnector
from app.config import get_settings


class HubSpotConnector(BaseConnector):
    """Fetch HubSpot CRM records and map them to the shared business schema."""

    source_type = "hubspot"
    supported_record_types = frozenset({"customer", "product"})
    base_url = "https://api.hubapi.com"

    def __init__(self, source_name: str, config: dict[str, Any] | None = None):
        super().__init__(source_name, config)
        self.access_token = get_settings().hubspot_access_token

    def fetch(self, record_type: str, **kwargs: Any) -> list[dict[str, Any]]:
        if record_type not in self.supported_record_types:
            raise ValueError(
                f"HubSpot does not support record_type={record_type!r}; "
                f"supported types: {sorted(self.supported_record_types)}."
            )

        object_type = "contacts" if record_type == "customer" else "products"
        properties = (
            "email,firstname,lastname,phone,city,country"
            if record_type == "customer"
            else "name,description,hs_sku,price"
        )
        records = self._list_records(object_type, properties)
        if record_type == "customer":
            return [self._map_contact(record) for record in records]
        return [self._map_product(record) for record in records]

    def _list_records(self, object_type: str, properties: str) -> list[dict[str, Any]]:
        if not self.access_token:
            raise ValueError("HUBSPOT_ACCESS_TOKEN is required for HubSpot sources.")
        headers = {"Authorization": f"Bearer {self.access_token}"}
        params: dict[str, str | int] = {"limit": 100, "properties": properties}
        records: list[dict[str, Any]] = []
        seen_cursors: set[str] = set()

        with httpx.Client(timeout=30) as client:
            while True:
                response = client.get(
                    f"{self.base_url}/crm/v3/objects/{object_type}",
                    headers=headers,
                    params=params,
                )
                response.raise_for_status()
                page = response.json()
                records.extend(page.get("results", []))
                cursor = page.get("paging", {}).get("next", {}).get("after")
                if not cursor or cursor in seen_cursors:
                    break
                seen_cursors.add(cursor)
                params["after"] = cursor

        return records

    @staticmethod
    def _map_contact(record: dict[str, Any]) -> dict[str, Any]:
        properties = record.get("properties") or {}
        return {
            "customer_id": str(record["id"]),
            "email": properties.get("email"),
            "first_name": properties.get("firstname"),
            "last_name": properties.get("lastname"),
            "phone": properties.get("phone"),
            "city": properties.get("city"),
            "country": properties.get("country"),
            "raw_payload": record,
        }

    @staticmethod
    def _map_product(record: dict[str, Any]) -> dict[str, Any]:
        properties = record.get("properties") or {}
        return {
            "product_id": str(record["id"]),
            "product_name": properties.get("name"),
            "sku": properties.get("hs_sku"),
            "description": properties.get("description"),
            "unit_price": None,
            "currency": "USD",
            "raw_payload": record,
        }

    def health_check(self) -> bool:
        try:
            self._list_records("contacts", "email")
            return True
        except Exception:
            return False
