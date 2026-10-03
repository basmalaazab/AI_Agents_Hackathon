"""Unit tests for the data cleaner."""
import pytest
from decimal import Decimal
import pandas as pd

from app.pipeline.cleaner import (
    clean_amount,
    clean_date,
    clean_string,
    clean_currency_code,
    clean_orders,
    clean_customers,
    deduplicate_by_column,
)


class TestCleanAmount:
    def test_plain_number(self):
        assert clean_amount("149.99") == Decimal("149.99")

    def test_dollar_sign(self):
        assert clean_amount("$34.99") == Decimal("34.99")

    def test_euro_sign(self):
        assert clean_amount("€89.99") == Decimal("89.99")

    def test_comma_thousands(self):
        assert clean_amount("1,299.99") == Decimal("1299.99")

    def test_none_returns_none(self):
        assert clean_amount(None) is None

    def test_nan_returns_none(self):
        assert clean_amount(float("nan")) is None

    def test_invalid_string_returns_none(self):
        assert clean_amount("not-a-number") is None

    def test_integer_input(self):
        assert clean_amount(100) == Decimal("100")


class TestCleanDate:
    def test_iso_date(self):
        result = clean_date("2024-01-15")
        assert result is not None
        assert result.year == 2024

    def test_iso_datetime(self):
        result = clean_date("2024-01-15T10:30:00Z")
        assert result is not None

    def test_us_format(self):
        result = clean_date("01/20/2024")
        assert result is not None

    def test_invalid_string_returns_none(self):
        assert clean_date("not-a-date") is None

    def test_none_returns_none(self):
        assert clean_date(None) is None


class TestCleanString:
    def test_strips_whitespace(self):
        assert clean_string("  hello  ") == "hello"

    def test_title_case(self):
        assert clean_string("ALICE JOHNSON", title_case=True) == "Alice Johnson"

    def test_empty_string_returns_none(self):
        assert clean_string("") is None

    def test_none_returns_none(self):
        assert clean_string(None) is None


class TestCleanCurrencyCode:
    def test_valid_usd(self):
        assert clean_currency_code("usd") == "USD"

    def test_valid_gbp(self):
        assert clean_currency_code("GBP") == "GBP"

    def test_invalid_returns_usd(self):
        assert clean_currency_code("dollars") == "USD"

    def test_none_returns_usd(self):
        assert clean_currency_code(None) == "USD"


class TestDeduplicateByColumn:
    def test_removes_duplicates(self):
        df = pd.DataFrame({"order_id": ["A", "B", "A", "C"]})
        result, count = deduplicate_by_column(df, "order_id")
        assert count == 1
        assert len(result) == 3

    def test_no_duplicates(self):
        df = pd.DataFrame({"order_id": ["A", "B", "C"]})
        result, count = deduplicate_by_column(df, "order_id")
        assert count == 0
        assert len(result) == 3


class TestCleanOrders:
    def test_cleans_currency_symbol(self):
        df = pd.DataFrame({
            "order_id": ["ORD-1"],
            "order_date": ["2024-01-05"],
            "total_amount": ["$149.99"],
            "currency": ["USD"],
            "status": ["completed"],
        })
        result = clean_orders(df)
        assert result["total_amount"].iloc[0] == Decimal("149.99")

    def test_sets_default_status(self):
        df = pd.DataFrame({
            "order_id": ["ORD-1"],
            "order_date": ["2024-01-05"],
            "total_amount": ["89.99"],
        })
        result = clean_orders(df)
        assert result["status"].iloc[0] == "completed"

    def test_normalises_status_case(self):
        df = pd.DataFrame({
            "order_id": ["ORD-1"],
            "order_date": ["2024-01-05"],
            "total_amount": ["89.99"],
            "status": ["COMPLETED"],
        })
        result = clean_orders(df)
        assert result["status"].iloc[0] == "completed"


class TestCleanCustomers:
    def test_email_lowercased(self):
        df = pd.DataFrame({
            "customer_id": ["C001"],
            "email": ["ALICE@EXAMPLE.COM"],
        })
        result = clean_customers(df)
        assert result["email"].iloc[0] == "alice@example.com"

    def test_invalid_email_set_to_none(self):
        df = pd.DataFrame({
            "customer_id": ["C001"],
            "email": ["not-an-email"],
        })
        result = clean_customers(df)
        assert result["email"].iloc[0] is None

    def test_names_title_cased(self):
        df = pd.DataFrame({
            "customer_id": ["C001"],
            "first_name": ["BOB"],
            "last_name": ["SMITH"],
        })
        result = clean_customers(df)
        assert result["first_name"].iloc[0] == "Bob"
        assert result["last_name"].iloc[0] == "Smith"
