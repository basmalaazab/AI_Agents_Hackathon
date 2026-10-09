"""
Data cleaner — normalises values after validation passes.

Handles:
- Timestamp parsing and UTC normalisation
- Currency string stripping (→ Decimal)
- Name normalisation (strip, title-case)
- Missing optional value defaults
- Deduplication within a batch
"""
from __future__ import annotations

import logging
import re
import threading
import time
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

_CURRENCY_STRIP_RE = re.compile(r"[£€$,\s]")


def clean_amount(value: Any) -> Decimal | None:
    """Convert a currency string or numeric to a Decimal, or None if unparseable."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    cleaned = _CURRENCY_STRIP_RE.sub("", str(value))
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


EXCHANGE_RATES_TO_USD: dict[str, Decimal] = {
    "USD": Decimal("1.0"),
    "EUR": Decimal("1.08"),
    "GBP": Decimal("1.27"),
    "EGP": Decimal("0.021"),
    "SAR": Decimal("0.267"),
    "AED": Decimal("0.272"),
    "KWD": Decimal("3.26"),
    "CAD": Decimal("0.74"),
    "AUD": Decimal("0.66"),
    "JPY": Decimal("0.0067"),
}
_exchange_rate_refresh_after = 0.0
_exchange_rate_lock = threading.Lock()


def _refresh_exchange_rates() -> None:
    """Refresh USD base rates periodically; keep references available while offline."""
    global _exchange_rate_refresh_after
    now = time.monotonic()
    if now < _exchange_rate_refresh_after:
        return
    with _exchange_rate_lock:
        now = time.monotonic()
        if now < _exchange_rate_refresh_after:
            return
        # Avoid hammering the provider if this runtime has no outbound network.
        _exchange_rate_refresh_after = now + 24 * 60 * 60
        try:
            import httpx
            response = httpx.get("https://open.er-api.com/v6/latest/USD", timeout=2.5)
            response.raise_for_status()
            payload = response.json()
            if payload.get("result") != "success":
                return
            rates = payload.get("rates", {})
            for currency, units_per_usd in rates.items():
                try:
                    units = Decimal(str(units_per_usd))
                    if units > 0:
                        EXCHANGE_RATES_TO_USD[currency.upper()] = Decimal("1") / units
                except Exception:
                    continue
        except Exception as exc:
            logger.info("Using bundled exchange-rate references (%s)", type(exc).__name__)


def convert_to_usd(amount: Any, currency: str = "USD") -> Decimal | None:
    """Convert amount in given currency to USD using refreshed or bundled rates."""
    if amount is None:
        return None
    try:
        dec_amount = Decimal(str(amount))
    except Exception:
        return None
    curr_upper = (currency or "USD").upper().strip()
    if curr_upper != "USD":
        _refresh_exchange_rates()
    rate = EXCHANGE_RATES_TO_USD.get(curr_upper)
    if rate is None:
        logger.warning("No USD conversion rate configured for currency %s", curr_upper)
        return None
    return round(dec_amount * rate, 2)



def clean_date(value: Any) -> pd.Timestamp | None:
    """Parse a date/datetime value into a UTC-aware Timestamp."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        ts = pd.to_datetime(value, utc=True)
        return ts
    except (ValueError, TypeError):
        return None


def clean_string(value: Any, title_case: bool = False) -> str | None:
    """Strip whitespace from strings; return None for blank/NaN values."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()
    if not s:
        return None
    return s.title() if title_case else s


def clean_currency_code(value: Any) -> str:
    """Normalise currency code to uppercase 3-letter ISO code, defaulting to USD."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "USD"
    code = str(value).strip().upper()
    if len(code) == 3:
        return code
    return "USD"


def deduplicate_by_column(df: pd.DataFrame, column: str) -> tuple[pd.DataFrame, int]:
    """
    Remove intra-batch duplicates based on `column`.
    Returns (deduplicated_df, duplicate_count).
    """
    before = len(df)
    df = df.drop_duplicates(subset=[column], keep="first")
    duplicates = before - len(df)
    if duplicates:
        logger.info("Removed %d intra-batch duplicate(s) on column '%s'.", duplicates, column)
    return df, duplicates


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all cleaning transformations to an orders DataFrame."""
    df = df.copy()

    df["order_id"] = df["order_id"].astype(str).str.strip()
    df["order_date"] = df["order_date"].apply(clean_date)
    df["total_amount"] = df["total_amount"].apply(clean_amount)
    df["currency"] = df.get("currency", pd.Series(["USD"] * len(df))).apply(
        clean_currency_code
    )

    # Convert total amount to USD using exchange rates
    def _convert_row(row):
        amt = row.get("total_amount")
        curr = row.get("currency") or "USD"
        return convert_to_usd(amt, curr)

    df["total_amount_usd"] = df.apply(_convert_row, axis=1)

    # Optional fields
    if "customer_id" in df.columns:
        df["customer_id"] = df["customer_id"].astype(str).str.strip()
    if "status" in df.columns:
        df["status"] = (
            df["status"]
            .fillna("completed")
            .astype(str)
            .str.strip()
            .str.lower()
        )
    else:
        df["status"] = "completed"

    return df


def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all cleaning transformations to a customers DataFrame."""
    df = df.copy()

    df["customer_id"] = df["customer_id"].astype(str).str.strip()
    if "email" in df.columns:
        df["email"] = df["email"].astype(str).str.strip().str.lower()
        df["email"] = df["email"].where(df["email"].str.contains("@"), None)
    if "first_name" in df.columns:
        df["first_name"] = df["first_name"].apply(lambda v: clean_string(v, title_case=True))
    if "last_name" in df.columns:
        df["last_name"] = df["last_name"].apply(lambda v: clean_string(v, title_case=True))
    if "phone" in df.columns:
        df["phone"] = df["phone"].apply(clean_string)
    if "city" in df.columns:
        df["city"] = df["city"].apply(lambda v: clean_string(v, title_case=True))
    if "country" in df.columns:
        df["country"] = df["country"].apply(lambda v: clean_string(v, title_case=True))

    return df


def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all cleaning transformations to a products DataFrame."""
    df = df.copy()

    df["product_id"] = df["product_id"].astype(str).str.strip()
    df["product_name"] = df["product_name"].apply(clean_string)
    if "unit_price" in df.columns:
        df["unit_price"] = df["unit_price"].apply(clean_amount)
    if "currency" in df.columns:
        df["currency"] = df["currency"].apply(clean_currency_code)
    else:
        df["currency"] = "USD"
    if "sku" in df.columns:
        df["sku"] = df["sku"].apply(clean_string)
    if "category" in df.columns:
        df["category"] = df["category"].apply(clean_string)
    for column in ("stock_quantity", "reorder_point"):
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
            df[column] = df[column].where(df[column].isna() | (df[column] >= 0))

    return df
