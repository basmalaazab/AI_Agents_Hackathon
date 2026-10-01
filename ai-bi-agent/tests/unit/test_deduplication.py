"""Unit tests for deduplication behaviour in cleaner and loader."""
import pytest
import pandas as pd

from app.pipeline.cleaner import deduplicate_by_column


class TestDeduplication:
    def test_keeps_first_occurrence(self):
        df = pd.DataFrame({
            "order_id": ["A", "B", "A"],
            "total_amount": ["100", "200", "999"],
        })
        result, count = deduplicate_by_column(df, "order_id")
        assert count == 1
        # First occurrence kept
        row_a = result[result["order_id"] == "A"].iloc[0]
        assert row_a["total_amount"] == "100"

    def test_all_unique_no_removal(self):
        df = pd.DataFrame({"order_id": ["A", "B", "C"]})
        result, count = deduplicate_by_column(df, "order_id")
        assert count == 0
        assert len(result) == 3

    def test_all_duplicates_keeps_one(self):
        df = pd.DataFrame({"customer_id": ["X", "X", "X"]})
        result, count = deduplicate_by_column(df, "customer_id")
        assert count == 2
        assert len(result) == 1

    def test_preserves_all_columns(self):
        df = pd.DataFrame({
            "order_id": ["A", "A"],
            "amount": [100, 200],
            "status": ["ok", "ok"],
        })
        result, _ = deduplicate_by_column(df, "order_id")
        assert set(result.columns) == {"order_id", "amount", "status"}

    def test_empty_dataframe(self):
        df = pd.DataFrame({"order_id": []})
        result, count = deduplicate_by_column(df, "order_id")
        assert count == 0
        assert len(result) == 0
