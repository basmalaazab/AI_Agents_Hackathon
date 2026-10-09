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

## Public historical retail sample (UCI)

For a more realistic ingestion and analysis walkthrough, this repository includes a small sample selected evenly across the UCI Online Retail transaction period. It is historical public data from a UK online retailer, covering 2010-12-01 through 2011-12-09. The sample contains 500 invoices and 15,119 sale lines, 393 customer IDs, and 2,703 product codes. It includes no customer email/phone or inventory counts.

Credit: Chen, D. (2015). *Online Retail* [Dataset]. UCI Machine Learning Repository. [https://doi.org/10.24432/C5BW33](https://doi.org/10.24432/C5BW33). Licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The included CSVs are a processed subset; cancellations and negative-quantity return/adjustment rows were excluded.

### Load the UCI sample

1. Use a disposable company workspace or a clean local database. The sample is real historical public data; it is not a current SME pilot.
2. Sign in as a workspace manager and open **Data Sources**.
3. Click **Import UCI sample**. Clearview imports the customer, product, and order files under the workspace-scoped `uci_online_retail` source and records three ingestion runs in **Activity**. The button reports inserted, duplicate, and invalid row totals. Clicking it again is safe: existing rows are deduplicated.
4. Select **All Time** or a custom range from December 2010 through December 2011 and filter to `uci_online_retail` to explore the historical results.

You can also import the CSVs manually: import `uci_customers.csv` as **Customers**, `uci_products.csv` as **Products**, then `uci_orders.csv` as **Orders**, using `uci_online_retail` as the same source name each time.

The converter script can rebuild the files from the official UCI download: `python scripts/prepare_uci_online_retail.py`. To use a previously downloaded UCI ZIP, pass `--source-zip path\to\online-retail.zip`. The default output is the included `data/public_uci_sample/` folder.

This dataset supports historical sales, product and repeat-customer analysis. It contains no stock counts, so inventory risk should correctly report insufficient data. Revenue is stored in GBP and converted using Clearview's available USD reference rate; this is not the retailer's historical accounting FX. The converted amount is an analytical estimate, not a statement of the retailer's reported USD revenue.
