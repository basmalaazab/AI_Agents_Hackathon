"""Prepare a small, attributed UCI Online Retail sample for Clearview CSV import.

The generated sample is spread over the dataset's full date range. Cancellation
invoices and negative-quantity lines are excluded so the sample contains only
positive completed purchases. No inventory counts or customer contact details
are present in the source.
"""
from __future__ import annotations

import argparse
import io
import zipfile
from pathlib import Path
from urllib.request import urlopen

import numpy as np
import pandas as pd

DATASET_URL = "https://archive.ics.uci.edu/static/public/352/online%2Bretail.zip"
DATASET_MEMBER = "Online Retail.xlsx"
DEFAULT_OUTPUT = Path("data/public_uci_sample")


def read_source(zip_path: Path | None) -> pd.DataFrame:
    if zip_path:
        archive_bytes = zip_path.read_bytes()
    else:
        with urlopen(DATASET_URL, timeout=45) as response:
            archive_bytes = response.read()
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        workbook = archive.read(DATASET_MEMBER)
    return pd.read_excel(
        io.BytesIO(workbook),
        usecols=["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice", "CustomerID", "Country"],
        dtype={"InvoiceNo": "string", "StockCode": "string", "Description": "string", "CustomerID": "string", "Country": "string"},
    )


def prepare(source: pd.DataFrame, max_orders: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows = source.copy()
    rows["InvoiceNo"] = rows["InvoiceNo"].str.strip()
    rows["StockCode"] = rows["StockCode"].str.strip()
    rows["Quantity"] = pd.to_numeric(rows["Quantity"], errors="coerce")
    rows["UnitPrice"] = pd.to_numeric(rows["UnitPrice"], errors="coerce")
    rows["InvoiceDate"] = pd.to_datetime(rows["InvoiceDate"], errors="coerce")
    rows["CustomerID"] = rows["CustomerID"].str.strip()
    rows["Description"] = rows["Description"].str.strip()

    # C-prefixed invoices are cancellation records; negative quantities are
    # returns/adjustments and are kept out of this completed-sales sample.
    rows = rows[
        rows["InvoiceNo"].notna()
        & ~rows["InvoiceNo"].str.upper().str.startswith("C")
        & rows["StockCode"].notna()
        & rows["Description"].notna()
        & rows["InvoiceDate"].notna()
        & rows["Quantity"].gt(0)
        & rows["UnitPrice"].ge(0)
    ].copy()
    if rows.empty:
        raise ValueError("The source file has no positive sales rows after filtering.")

    invoice_dates = rows.groupby("InvoiceNo")["InvoiceDate"].min().sort_values()
    count = min(max_orders, len(invoice_dates))
    positions = np.linspace(0, len(invoice_dates) - 1, num=count, dtype=int)
    selected = set(invoice_dates.index[positions])
    rows = rows[rows["InvoiceNo"].isin(selected)].copy()
    rows["line_total"] = (rows["Quantity"] * rows["UnitPrice"]).round(2)
    invoice_totals = rows.groupby("InvoiceNo")["line_total"].sum().round(2)

    orders = pd.DataFrame({
        "order_id": rows["InvoiceNo"],
        "customer_id": rows["CustomerID"],
        "order_date": rows["InvoiceDate"].dt.strftime("%Y-%m-%d %H:%M:%S"),
        "total_amount": rows["InvoiceNo"].map(invoice_totals).map(lambda value: f"{value:.2f}"),
        "currency": "GBP",
        "product_name": rows["Description"],
        "sku": rows["StockCode"],
        "quantity": rows["Quantity"].astype(int),
        "unit_price": rows["UnitPrice"].map(lambda value: f"{value:.2f}"),
        "line_total": rows["line_total"].map(lambda value: f"{value:.2f}"),
        "status": "completed",
    })
    customers = (
        rows.loc[rows["CustomerID"].notna(), ["CustomerID", "Country"]]
        .drop_duplicates(subset=["CustomerID"])
        .rename(columns={"CustomerID": "customer_id", "Country": "country"})
        .sort_values("customer_id")
    )
    products = (
        rows.groupby("StockCode", as_index=False)
        .agg(product_name=("Description", lambda column: column.mode().iloc[0]), unit_price=("UnitPrice", "median"))
        .rename(columns={"StockCode": "sku"})
    )
    products.insert(0, "product_id", "UCI-" + products["sku"].astype(str))
    products["currency"] = "GBP"
    products["unit_price"] = products["unit_price"].map(lambda value: f"{value:.2f}")
    return orders, customers, products


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", type=Path, help="Use an already downloaded UCI ZIP instead of downloading it.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--max-orders", type=int, default=500, help="Evenly sample up to this many invoices across the source date range.")
    args = parser.parse_args()
    if args.max_orders < 1:
        parser.error("--max-orders must be at least 1")

    orders, customers, products = prepare(read_source(args.source_zip), args.max_orders)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    orders.to_csv(args.output_dir / "uci_orders.csv", index=False)
    customers.to_csv(args.output_dir / "uci_customers.csv", index=False)
    products.to_csv(args.output_dir / "uci_products.csv", index=False)
    print(f"Prepared {orders['order_id'].nunique():,} invoices across {len(orders):,} line items.")
    print(f"Prepared {len(customers):,} customer profiles and {len(products):,} products.")
    print(f"Import files from {args.output_dir.resolve()} using source name uci_online_retail.")
    print("Use All Time or a custom date range; these historical records span 2010-12-01 to 2011-12-09.")


if __name__ == "__main__":
    main()
