"""Unit tests for the data validator."""
import pytest
import pandas as pd

from app.pipeline.validator import (
    normalize_columns,
    validate_orders,
    validate_customers,
    validate_products,
)


class TestNormalizeColumns:
    def test_lowercases_columns(self):
        df = pd.DataFrame({"Order_ID": [1], "Total_Amount": [100]})
        result = normalize_columns(df, "order")
        assert "order_id" in result.columns
        assert "total_amount" in result.columns

    def test_applies_order_aliases(self):
        df = pd.DataFrame({"sale_id": ["S1"], "amount": [100], "sale_date": ["2024-01-01"]})
        result = normalize_columns(df, "order")
        assert "order_id" in result.columns
        assert "total_amount" in result.columns
        assert "order_date" in result.columns

    def test_applies_customer_aliases(self):
        df = pd.DataFrame({"cust_id": ["C1"], "mail": ["a@b.com"]})
        result = normalize_columns(df, "customer")
        assert "customer_id" in result.columns
        assert "email" in result.columns


class TestValidateOrders:
    def _base_df(self, overrides=None):
        data = {
            "order_id": ["ORD-1"],
            "order_date": ["2024-01-01"],
            "total_amount": ["99.99"],
        }
        if overrides:
            data.update(overrides)
        return pd.DataFrame(data)

    def test_valid_row_passes(self):
        result = validate_orders(self._base_df())
        assert result.valid_count == 1
        assert result.error_count == 0

    def test_missing_order_id_rejected(self):
        df = self._base_df({"order_id": [None]})
        result = validate_orders(df)
        assert result.valid_count == 0
        assert result.error_count == 1
        assert result.errors[0]["error_type"] == "missing_required_field"

    def test_missing_order_date_rejected(self):
        df = self._base_df({"order_date": [None]})
        result = validate_orders(df)
        assert result.valid_count == 0
        assert result.error_count == 1

    def test_invalid_date_rejected(self):
        df = self._base_df({"order_date": ["not-a-date"]})
        result = validate_orders(df)
        assert result.valid_count == 0
        assert result.errors[0]["error_type"] == "invalid_date"

    def test_negative_amount_rejected(self):
        df = self._base_df({"total_amount": ["-50.00"]})
        result = validate_orders(df)
        assert result.valid_count == 0
        assert result.errors[0]["error_type"] == "invalid_amount"

    def test_non_numeric_amount_rejected(self):
        df = self._base_df({"total_amount": ["abc"]})
        result = validate_orders(df)
        assert result.valid_count == 0
        assert result.errors[0]["error_type"] == "invalid_amount"

    def test_multiple_rows_partial_valid(self):
        df = pd.DataFrame({
            "order_id": ["ORD-1", "ORD-2", "ORD-3"],
            "order_date": ["2024-01-01", None, "2024-01-03"],
            "total_amount": ["100", "200", "300"],
        })
        result = validate_orders(df)
        assert result.valid_count == 2
        assert result.error_count == 1

    def test_errors_contain_raw_data(self):
        df = self._base_df({"order_id": [None]})
        result = validate_orders(df)
        assert "raw_data" in result.errors[0]

    def test_missing_required_column_rejects_all(self):
        df = pd.DataFrame({"order_date": ["2024-01-01"], "total_amount": ["100"]})
        result = validate_orders(df)
        assert result.valid_count == 0
        assert result.errors[0]["error_type"] == "missing_required_column"


class TestValidateCustomers:
    def test_valid_customer(self):
        df = pd.DataFrame({"customer_id": ["C001"], "email": ["a@b.com"]})
        result = validate_customers(df)
        assert result.valid_count == 1

    def test_missing_customer_id_rejected(self):
        df = pd.DataFrame({"customer_id": [None]})
        result = validate_customers(df)
        assert result.valid_count == 0
        assert result.error_count == 1


class TestValidateProducts:
    def test_valid_product(self):
        df = pd.DataFrame({
            "product_id": ["P001"],
            "product_name": ["Widget"],
        })
        result = validate_products(df)
        assert result.valid_count == 1

    def test_missing_product_name_rejected(self):
        df = pd.DataFrame({
            "product_id": ["P001"],
            "product_name": [None],
        })
        result = validate_products(df)
        assert result.valid_count == 0

    def test_inventory_must_be_non_negative_whole_number(self):
        df = pd.DataFrame({
            "product_id": ["P001", "P002"],
            "product_name": ["Widget A", "Widget B"],
            "stock_quantity": [-2, 1.5],
        })
        result = validate_products(df)
        assert result.valid_count == 0
        assert len(result.errors) == 2
        assert all(error["error_type"] == "invalid_inventory_value" for error in result.errors)
