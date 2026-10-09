# Demo data

All records in this directory are synthetic and fictional. They are for local development and hackathon demonstrations; they do not describe real customers, merchants or business performance.

## Included CSV examples

| File | Contents | Demonstrates |
| --- | --- | --- |
| `sample_sales.csv` | Order and line-item fields | Validation, date and currency normalization, duplicate detection and invalid-row reporting |
| `sample_customers.csv` | Customer profile fields | Customer ingestion, required-field checks and duplicate handling |
| `sample_products.csv` | Product catalog and optional stock fields | Inventory import, reorder points and low-stock alerts |

The examples may include malformed, duplicate or incomplete rows on purpose. Exact counts can change as the files or validation rules change; use the app's import result and Activity page as the source of truth.

## Import the sample files

1. Start the API and frontend using the repository [local setup](../README.md#run-locally-on-windows).
2. Create or sign in to a company workspace.
3. Open **Data Sources**, choose **Orders**, **Customers** or **Products**, select a file, and upload it.
4. Use a consistent source name when products must be linked to order lines (for example, use `shopify_store` for both).
5. Review the ingestion result: fetched, inserted, duplicate and invalid records. Open **Activity** to inspect the timestamped pipeline run.

Revenue is normalized to USD where a supported reference rate is available. Unknown currencies are excluded from USD revenue and reported. These rates are for product analytics, not accounting.

## Inventory-risk walkthrough

Product rows may include `stock_quantity` and `reorder_point`. To demonstrate a stock warning, import the sample product file under the same source as sales data and ensure recent linked sales are present. The product example includes a synthetic 4K monitor balance below its reorder point. Inventory cover is estimated from recorded recent sales and does not include supplier lead time or safety stock.

An AI reorder draft can suggest a target quantity when it has current stock plus enough recent sales or an imported reorder point. It is a review-only calculation; no purchase order is submitted.

Keep demo records in a disposable database. Do not combine sample rows with a real business workspace when reporting actual performance.
