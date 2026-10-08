# Demo data

Every dataset in this folder is synthetic and fictional. It is provided for development and hackathon demos; it does not contain real customer or business records.

## CSV examples

| File | Contents | Example quality issues |
| --- | --- | --- |
| `sample_sales.csv` | Order and sales rows | Duplicate IDs, missing fields, negative amounts, inconsistent dates, and formatted currency values |
| `sample_customers.csv` | Customer profile rows | Duplicate IDs, missing or invalid emails, inconsistent name casing, and empty rows |
| `sample_products.csv` | Product catalog and stock levels | Synthetic 4K monitor stock is below its reorder point |

The ingestion pipeline reports invalid rows and duplicate records rather than silently treating them as valid new data. Exact counts can change as these examples are edited; use the import result in the app as the source of truth.

## Try the examples

1. Start the backend and frontend using the repository [Quick Start](../README.md#run-locally).
2. In the app, open **Data Sources**.
3. Select the record type, choose one of the CSV files, and upload it.
4. Review the fetched, inserted, duplicate, and invalid row counts. To demo `sample_products.csv`, seed recent synthetic sales into a separate demo database (`DATABASE_URL=sqlite:///./demo_runtime.db`) and run the backend against that database; then choose **Products** and use source name `shopify_store` to match the demo sales data.

The pipeline does not convert currencies. Non-USD orders are excluded from USD revenue totals. Do not use these files to infer real business performance.
