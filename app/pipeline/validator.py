"""
Data validator — checks required fields, types, and business rules.

Returns a ValidationResult with valid rows and error details for invalid rows.
Does NOT silently discard records; errors are captured and persisted.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Required column definitions per record type
# ---------------------------------------------------------------------------

ORDER_REQUIRED_COLUMNS: list[str] = [
    "order_id",
    "order_date",
    "total_amount",
]

CUSTOMER_REQUIRED_COLUMNS: list[str] = [
    "customer_id",
]

PRODUCT_REQUIRED_COLUMNS: list[str] = [
    "product_id",
    "product_name",
]


@dataclass
class ValidationResult:
    valid_rows: pd.DataFrame
    errors: list[dict[str, Any]] = field(default_factory=list)

    @property
    def valid_count(self) -> int:
        return len(self.valid_rows)

    @property
    def error_count(self) -> int:
        return len(self.errors)


# ---------------------------------------------------------------------------
# Column name normalisation map — handles common naming inconsistencies
# ---------------------------------------------------------------------------

_ORDER_COLUMN_ALIASES: dict[str, str] = {
    "id": "order_id",
    "order_no": "order_id",
    "order_number": "order_id",
    "sale_id": "order_id",
    "date": "order_date",
    "sale_date": "order_date",
    "purchase_date": "order_date",
    "amount": "total_amount",
    "total": "total_amount",
    "revenue": "total_amount",
    "sale_amount": "total_amount",
    "grand_total": "total_amount",
    "cust_id": "customer_id",
    "client_id": "customer_id",
    "buyer_id": "customer_id",
    "curr": "currency",
    "qty": "quantity",
    "product": "product_name",
    "item_name": "product_name",
}

_CUSTOMER_COLUMN_ALIASES: dict[str, str] = {
    "id": "customer_id",
    "cust_id": "customer_id",
    "client_id": "customer_id",
    "name": "first_name",
    "full_name": "first_name",
    "email_address": "email",
    "mail": "email",
    "mobile": "phone",
    "telephone": "phone",
}

_PRODUCT_COLUMN_ALIASES: dict[str, str] = {
    "id": "product_id",
    "name": "product_name",
    "title": "product_name",
    "price": "unit_price",
    "cost": "unit_price",
    "stock": "stock_quantity",
    "inventory_quantity": "stock_quantity",
    "quantity_on_hand": "stock_quantity",
    "low_stock_threshold": "reorder_point",
}


def normalize_columns(df: pd.DataFrame, record_type: str) -> pd.DataFrame:
    """Lowercase and rename columns to canonical names."""
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

    alias_map = {
        "order": _ORDER_COLUMN_ALIASES,
        "customer": _CUSTOMER_COLUMN_ALIASES,
        "product": _PRODUCT_COLUMN_ALIASES,
    }.get(record_type, {})

    rename = {k: v for k, v in alias_map.items() if k in df.columns}
    df = df.rename(columns=rename)
    return df


def validate_orders(df: pd.DataFrame) -> ValidationResult:
    return _validate(df, "order", ORDER_REQUIRED_COLUMNS)


def validate_customers(df: pd.DataFrame) -> ValidationResult:
    return _validate(df, "customer", CUSTOMER_REQUIRED_COLUMNS)


def validate_products(df: pd.DataFrame) -> ValidationResult:
    return _validate(df, "product", PRODUCT_REQUIRED_COLUMNS)


def _validate(
    df: pd.DataFrame, record_type: str, required_cols: list[str]
) -> ValidationResult:
    df = normalize_columns(df, record_type)
    errors: list[dict[str, Any]] = []
    valid_indices: list[int] = []

    missing_required = [c for c in required_cols if c not in df.columns]
    if missing_required:
        # Whole-batch error — we cannot proceed at all
        for idx, row in df.iterrows():
            errors.append(
                {
                    "row_index": idx,
                    "error_type": "missing_required_column",
                    "error_message": f"Required columns missing from dataset: {missing_required}",
                    "raw_data": row.to_dict(),
                }
            )
        return ValidationResult(valid_rows=pd.DataFrame(), errors=errors)

    for idx, row in df.iterrows():
        row_errors = _check_row(row, record_type, required_cols, idx)
        if row_errors:
            errors.extend(row_errors)
        else:
            valid_indices.append(idx)

    valid_df = df.loc[valid_indices].reset_index(drop=True) if valid_indices else pd.DataFrame(columns=df.columns)
    logger.debug(
        "Validation [%s]: %d valid, %d invalid out of %d",
        record_type,
        len(valid_indices),
        len(errors),
        len(df),
    )
    return ValidationResult(valid_rows=valid_df, errors=errors)


def _check_row(
    row: pd.Series, record_type: str, required_cols: list[str], idx: int
) -> list[dict[str, Any]]:
    row_errors: list[dict[str, Any]] = []

    # 1. Required fields present and non-null
    for col in required_cols:
        val = row.get(col)
        if val is None or (isinstance(val, float) and pd.isna(val)) or str(val).strip() == "":
            row_errors.append(
                {
                    "row_index": idx,
                    "error_type": "missing_required_field",
                    "error_message": f"Required field '{col}' is missing or empty.",
                    "raw_data": row.to_dict(),
                }
            )

    if row_errors:
        return row_errors

    # 2. Type-specific checks
    if record_type == "order":
        # Validate order_date is parseable
        try:
            pd.to_datetime(row["order_date"])
        except (ValueError, TypeError):
            row_errors.append(
                {
                    "row_index": idx,
                    "error_type": "invalid_date",
                    "error_message": f"order_date '{row['order_date']}' cannot be parsed.",
                    "raw_data": row.to_dict(),
                }
            )

        # Validate total_amount is numeric and positive
        try:
            val = float(str(row["total_amount"]).replace(",", "").replace("$", "").strip())
            if val < 0:
                row_errors.append(
                    {
                        "row_index": idx,
                        "error_type": "invalid_amount",
                        "error_message": f"total_amount '{row['total_amount']}' is negative.",
                        "raw_data": row.to_dict(),
                    }
                )
        except (ValueError, TypeError):
            row_errors.append(
                {
                    "row_index": idx,
                    "error_type": "invalid_amount",
                    "error_message": f"total_amount '{row['total_amount']}' is not numeric.",
                    "raw_data": row.to_dict(),
                }
            )

    if record_type == "product":
        for col in ("stock_quantity", "reorder_point"):
            val = row.get(col)
            if val is None or (isinstance(val, float) and pd.isna(val)):
                continue
            try:
                number = float(str(val))
                if number < 0 or not number.is_integer():
                    raise ValueError
            except (ValueError, TypeError):
                row_errors.append({
                    "row_index": idx,
                    "error_type": "invalid_inventory_value",
                    "error_message": f"{col} must be a non-negative whole number.",
                    "raw_data": row.to_dict(),
                })
    return row_errors
