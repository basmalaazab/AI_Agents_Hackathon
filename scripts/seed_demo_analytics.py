"""
Demo Analytics Seed Script — Populates rich multi-month realistic transactions
for dashboard visualization and AI agent evaluation.
"""
import os
import sys
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite:///bi_db.sqlite"

# SQLite JSONB patch for standalone run
from sqlalchemy import JSON
import sqlalchemy.dialects.postgresql as pg_dialect
class _SQLiteCompatibleJSON(JSON):
    pass
pg_dialect.JSONB = _SQLiteCompatibleJSON  # type: ignore

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))



from app.database import Base, engine, SessionLocal
from app.models import DataSource, Customer, Product, Order, OrderItem


def seed_rich_analytics_data():
    print("==================================================")
    print("   AI BI AGENT - ANALYTICS DEMO DATA SEEDER      ")
    print("==================================================")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 1. Register Data Sources
    sources = [
        ("shopify_store", "Shopify Store", "csv"),
        ("amazon_seller", "Amazon Marketplace", "api"),
        ("pos_terminal", "Retail POS System", "csv"),
    ]
    ds_map = {}
    for name, desc, stype in sources:
        existing = db.query(DataSource).filter_by(name=name).first()
        if not existing:
            s = DataSource(name=name, source_type=stype, description=desc)
            db.add(s)
            db.commit()
            db.refresh(s)
            ds_map[name] = s
        else:
            ds_map[name] = existing

    # 2. Seed Products
    catalog = [
        ("Wireless Noise-Canceling Headphones", "TECH-001", "Electronics", 199.99),
        ("Ergonomic Mechanical Keyboard", "TECH-002", "Electronics", 129.99),
        ("4K Ultra HD Monitor 27-inch", "TECH-003", "Electronics", 349.99),
        ("Organic Cotton Hoodie", "APP-001", "Apparel", 65.00),
        ("Slim Fit Denim Jeans", "APP-002", "Apparel", 85.00),
        ("Running Performance Sneakers", "APP-003", "Apparel", 120.00),
        ("Smart LED Desk Lamp", "HOME-001", "Home & Office", 45.00),
        ("Stainless Steel Water Bottle 1L", "HOME-002", "Home & Office", 28.00),
        ("Hydrating Facial Moisturizer", "BEAUTY-001", "Beauty & Care", 34.00),
        ("Natural Botanical Serum", "BEAUTY-002", "Beauty & Care", 52.00),
    ]

    prod_objects = []
    for name, sku, category, price in catalog:
        existing_p = db.query(Product).filter_by(sku=sku).first()
        if not existing_p:
            p = Product(
                source_name="shopify_store",
                external_id=f"PROD-{sku}",
                name=name,
                sku=sku,
                category=category,
                description=f"High quality {name}",
                unit_price=price,
                currency="USD",
            )
            db.add(p)
            prod_objects.append(p)
        else:
            prod_objects.append(existing_p)
    db.commit()

    # 3. Seed Customers
    customer_names = [
        ("Sophia", "Martinez", "sophia.m@example.com", "Austin", "USA"),
        ("Liam", "Johnson", "liam.j@example.com", "Seattle", "USA"),
        ("Emma", "Brown", "emma.b@example.com", "Chicago", "USA"),
        ("Noah", "Davis", "noah.d@example.com", "New York", "USA"),
        ("Olivia", "Wilson", "olivia.w@example.com", "Denver", "USA"),
        ("James", "Taylor", "james.t@example.com", "San Francisco", "USA"),
        ("Ava", "Anderson", "ava.a@example.com", "Miami", "USA"),
        ("Ethan", "Thomas", "ethan.t@example.com", "Boston", "USA"),
        ("Isabella", "Jackson", "isabella.j@example.com", "Atlanta", "USA"),
        ("Lucas", "White", "lucas.w@example.com", "Dallas", "USA"),
    ]

    cust_objects = []
    for fn, ln, email, city, country in customer_names:
        existing_c = db.query(Customer).filter_by(email=email).first()
        if not existing_c:
            c = Customer(
                source_name=random.choice(["shopify_store", "amazon_seller", "pos_terminal"]),
                external_id=f"CUST-{random.randint(1000, 9999)}",
                email=email,
                first_name=fn,
                last_name=ln,
                city=city,
                country=country,
            )
            db.add(c)
            cust_objects.append(c)
        else:
            cust_objects.append(existing_c)
    db.commit()

    # 4. Generate Orders & Order Items across last 90 days
    now = datetime.now(timezone.utc)
    statuses = ["completed", "completed", "completed", "completed", "completed", "completed", "cancelled", "refunded"]

    order_count_added = 0
    random.seed(42)  # Deterministic seed for reproducible demo analytics

    for day_offset in range(90, 0, -1):
        order_date = now - timedelta(days=day_offset, hours=random.randint(1, 10))
        # Daily sales volume varies to create realistic trends
        num_orders_today = random.randint(1, 4) if (day_offset % 7 != 0) else random.randint(3, 7)

        for _ in range(num_orders_today):
            cust = random.choice(cust_objects)
            source_name = random.choice(["shopify_store", "amazon_seller", "pos_terminal"])
            status = random.choice(statuses)

            # Choose 1-3 items
            num_items = random.randint(1, 3)
            chosen_prods = random.sample(prod_objects, num_items)

            total_amount = 0.0
            order_items_data = []

            for p in chosen_prods:
                qty = random.randint(1, 2)
                line_total = round(qty * float(p.unit_price), 2)
                total_amount += line_total
                order_items_data.append((p, qty, float(p.unit_price), line_total))

            total_amount = round(total_amount, 2)
            ext_order_id = f"ORD-{day_offset}-{random.randint(10000, 99999)}"


            order = Order(
                source_name=source_name,
                external_id=ext_order_id,
                customer_id=cust.id,
                order_date=order_date,
                status=status,
                total_amount=total_amount,
                currency="USD",
                total_amount_usd=total_amount,
            )
            db.add(order)
            db.commit()
            db.refresh(order)

            for p, qty, price, ltotal in order_items_data:
                item = OrderItem(
                    order_id=order.id,
                    product_id=p.id,
                    product_name=p.name,
                    sku=p.sku,
                    quantity=qty,
                    unit_price=price,
                    line_total=ltotal,
                    currency="USD",
                )
                db.add(item)
            db.commit()
            order_count_added += 1

    print(f"[OK] Seeded {len(prod_objects)} products, {len(cust_objects)} customers, and {order_count_added} orders over 90 days!")

    db.close()


if __name__ == "__main__":
    seed_rich_analytics_data()
