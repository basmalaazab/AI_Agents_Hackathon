"""Read-only connector for Stripe customers, products, and PaymentIntents."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import httpx

from app.connectors.base import BaseConnector
from app.config import get_settings


_ZERO_DECIMAL_CURRENCIES = frozenset(
    {"bif", "clp", "djf", "gnf", "jpy", "kmf", "krw", "mga", "pyg", "rwf", "ugx", "vnd", "vuv", "xaf", "xof", "xpf"}
)
_THREE_DECIMAL_CURRENCIES = frozenset({"bhd", "kwd", "omr", "jod", "tnd"})


class StripeConnector(BaseConnector):
    """Fetch Stripe resources and map them to the shared business schema."""

    source_type = "stripe"
    supported_record_types = frozenset({"customer", "order", "product"})
    base_url = "https://api.stripe.com/v1"

    def __init__(self, source_name: str, config: dict[str, Any] | None = None):
        super().__init__(source_name, config)
        self.secret_key = get_settings().stripe_secret_key

    def fetch(
        self,
        record_type: str,
        since: str | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        if record_type not in self.supported_record_types:
            raise ValueError(
                f"Stripe does not support record_type={record_type!r}; "
                f"supported types: {sorted(self.supported_record_types)}."
            )

        endpoint = {
            "customer": "customers",
            "order": "payment_intents",
            "product": "products",
        }[record_type]
        params: dict[str, Any] = {"limit": 100}
        if record_type == "product":
            params["active"] = "true"
            params["expand[]"] = "data.default_price"
        if record_type == "order":
            params["expand[]"] = "data.latest_charge"
        if record_type == "order" and since:
            params["created[gte]"] = self._to_unix_timestamp(since)

        objects = self._list_objects(endpoint, params)
        mappers = {
            "customer": self._map_customer,
            "order": self._map_payment_intent,
            "product": self._map_product,
        }
        mapped = [mappers[record_type](item) for item in objects]
        if record_type == "order":
            return [
                row
                for row in mapped
                if row["status"] in {"completed", "cancelled", "refunded"}
            ]
        return mapped

    def _list_objects(
        self, endpoint: str, initial_params: dict[str, Any]
    ) -> list[dict[str, Any]]:
        if not self.secret_key:
            raise ValueError("STRIPE_SECRET_KEY is required for Stripe sources.")
        objects: list[dict[str, Any]] = []
        params = dict(initial_params)
        seen_cursors: set[str] = set()

        with httpx.Client(
            timeout=30,
            auth=(self.secret_key, ""),
        ) as client:
            while True:
                response = client.get(f"{self.base_url}/{endpoint}", params=params)
                response.raise_for_status()
                page = response.json()
                data = page.get("data", [])
                objects.extend(data)
                if not page.get("has_more") or not data:
                    break
                cursor = data[-1].get("id")
                if not cursor or cursor in seen_cursors:
                    break
                seen_cursors.add(cursor)
                params["starting_after"] = cursor

        return objects

    @staticmethod
    def _map_customer(record: dict[str, Any]) -> dict[str, Any]:
        name_parts = (record.get("name") or "").strip().split(maxsplit=1)
        address = record.get("address") or record.get("shipping", {}).get("address") or {}
        return {
            "customer_id": str(record["id"]),
            "email": record.get("email"),
            "first_name": name_parts[0] if name_parts else None,
            "last_name": name_parts[1] if len(name_parts) > 1 else None,
            "phone": record.get("phone"),
            "city": address.get("city"),
            "country": address.get("country"),
            "raw_payload": record,
        }

    @classmethod
    def _map_payment_intent(cls, record: dict[str, Any]) -> dict[str, Any]:
        currency = str(record.get("currency") or "usd").lower()
        charge = record.get("latest_charge")
        charge = charge if isinstance(charge, dict) else {}
        amount_received = int(record.get("amount_received", 0) or 0)
        amount_refunded = int(charge.get("amount_refunded", 0) or 0)
        is_succeeded = record.get("status") == "succeeded"
        amount_minor = (
            max(0, amount_received - amount_refunded)
            if is_succeeded
            else record.get("amount", 0)
        )
        customer = record.get("customer")
        if isinstance(customer, dict):
            customer = customer.get("id")
        if is_succeeded and amount_refunded > 0 and amount_refunded >= amount_received:
            status = "refunded"
        elif is_succeeded:
            status = "completed"
        elif record.get("status") == "canceled":
            status = "cancelled"
        else:
            status = "pending"
        return {
            "order_id": str(record["id"]),
            "customer_id": str(customer) if customer else None,
            "order_date": datetime.fromtimestamp(
                record["created"], tz=timezone.utc
            ).isoformat(),
            "total_amount": str(cls._major_units(amount_minor, currency)),
            "currency": currency.upper(),
            "status": status,
            "raw_payload": record,
        }

    @classmethod
    def _map_product(cls, record: dict[str, Any]) -> dict[str, Any]:
        price = record.get("default_price")
        if isinstance(price, str):
            price = None
        unit_amount = price.get("unit_amount") if isinstance(price, dict) else None
        currency = price.get("currency") if isinstance(price, dict) else None
        return {
            "product_id": str(record["id"]),
            "product_name": record.get("name"),
            "description": record.get("description"),
            "unit_price": (
                str(cls._major_units(unit_amount, currency))
                if unit_amount is not None and currency
                else None
            ),
            "currency": str(currency).upper() if currency else "USD",
            "raw_payload": record,
        }

    @staticmethod
    def _major_units(amount: int, currency: str) -> Decimal:
        exponent = 0 if currency in _ZERO_DECIMAL_CURRENCIES else 3 if currency in _THREE_DECIMAL_CURRENCIES else 2
        return Decimal(amount).scaleb(-exponent)

    @staticmethod
    def _to_unix_timestamp(value: str) -> int:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return int(parsed.timestamp())

    def health_check(self) -> bool:
        try:
            self._list_objects("customers", {"limit": 1})
            return True
        except Exception:
            return False
