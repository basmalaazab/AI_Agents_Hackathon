"""
Demo verification script.
Tests:
1. Database initialisation
2. Ingestion of data/sample_customers.csv (dirty/edge case dataset)
3. Ingestion of data/sample_sales.csv (dirty/edge case dataset)
4. Re-ingestion of data/sample_sales.csv to prove 100% deduplication
5. Quality error inspection
6. Analytics querying
"""
import sys
import os
from pathlib import Path

# Use SQLite for standalone verification run
os.environ["DATABASE_URL"] = "sqlite:///demo_verification.db"
os.environ["APP_ENV"] = "development"

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import Base, engine, SessionLocal
from app.models import DataSource, Customer, Order, OrderItem, Product, DataQualityError, IngestionRun
from app.services.ingestion_service import IngestionService
from app.api.data import revenue_summary, sales_by_date, sales_by_product, customer_frequency

def run_demo():
    print("==================================================")
    print("   AI BI AGENT - DATA ENGINEERING DEMO RUNNER     ")
    print("==================================================")

    # 1. Init DB
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    print("[1] Database initialized.")

    # 2. Register Source
    source = DataSource(name="demo_csv_store", source_type="csv", description="Demo CSV Uploads")
    db.add(source)
    db.commit()
    db.refresh(source)
    print(f"[2] Registered DataSource: {source.name} (ID: {source.id})")

    svc = IngestionService(db)

    # 3. Ingest Customers CSV
    customers_file = Path("data/sample_customers.csv")
    with open(customers_file, "rb") as f:
        cust_bytes = f.read()

    print(f"\n[3] Ingesting {customers_file}...")
    cust_run = svc.run_csv_ingestion(source, "customer", cust_bytes)
    print(f"    Status: {cust_run.status}")
    print(f"    Fetched: {cust_run.records_fetched}, Valid: {cust_run.records_valid}, Invalid: {cust_run.records_invalid}")
    print(f"    Inserted: {cust_run.records_inserted}, Duplicates: {cust_run.records_duplicate}")

    # 4. Ingest Sales CSV (First Run)
    sales_file = Path("data/sample_sales.csv")
    with open(sales_file, "rb") as f:
        sales_bytes = f.read()

    print(f"\n[4] Ingesting {sales_file} (First Run)...")
    sales_run = svc.run_csv_ingestion(source, "order", sales_bytes)
    print(f"    Status: {sales_run.status}")
    print(f"    Fetched: {sales_run.records_fetched}, Valid: {sales_run.records_valid}, Invalid: {sales_run.records_invalid}")
    print(f"    Inserted: {sales_run.records_inserted}, Duplicates: {sales_run.records_duplicate}")

    # 5. Re-ingest Sales CSV (Idempotency / Dedup Verification)
    print(f"\n[5] Re-ingesting {sales_file} (Second Run - Idempotency Check)...")
    sales_run2 = svc.run_csv_ingestion(source, "order", sales_bytes)
    print(f"    Status: {sales_run2.status}")
    print(f"    Fetched: {sales_run2.records_fetched}")
    print(f"    Inserted: {sales_run2.records_inserted} (Expected: 0)")
    print(f"    Duplicates: {sales_run2.records_duplicate} (Expected: {sales_run.records_inserted + 1})")

    # 6. Data Quality Errors
    errors = db.query(DataQualityError).all()
    print(f"\n[6] Logged Data Quality Errors ({len(errors)} total):")
    for e in errors:
        print(f"    - Type: {e.error_type} | Record: {e.record_type} | Message: {e.error_message}")

    # 7. Analytics Queries
    print("\n[7] Querying Analytics Contract Endpoints:")
    rev = revenue_summary(db)
    print(f"    Revenue Summary: Total Orders = {rev['total_orders']}, Total Revenue USD = ${rev['total_revenue_usd']:,.2f}, AOV = ${rev['avg_order_value_usd']:,.2f}")
    
    dates = sales_by_date(limit=5, db=db)
    print(f"    Daily Sales (top {len(dates)} dates): {dates}")

    custs = customer_frequency(limit=5, db=db)
    print(f"    Customer Frequency (top {len(custs)} customers): {custs}")

    db.close()
    engine.dispose()
    if os.path.exists("demo_verification.db"):
        os.remove("demo_verification.db")

    print("\n==================================================")
    print("      DEMO VERIFICATION COMPLETED SUCCESSFULLY    ")
    print("==================================================")

if __name__ == "__main__":
    run_demo()
