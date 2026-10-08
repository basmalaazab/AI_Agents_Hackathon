"""
Unit tests for AnalyticsService calculations.
"""
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Customer, Order, OrderItem, Product, DataSource
from app.services.analytics_service import AnalyticsService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed test data
    source = DataSource(name="test_store", source_type="csv", description="Test Store")
    session.add(source)
    session.commit()

    cust1 = Customer(
        source_name="test_store",
        external_id="C-1",
        email="cust1@test.com",
        first_name="Alice",
        last_name="Smith",
    )
    cust2 = Customer(
        source_name="test_store",
        external_id="C-2",
        email="cust2@test.com",
        first_name="Bob",
        last_name="Jones",
    )
    session.add_all([cust1, cust2])
    session.commit()

    prod1 = Product(
        source_name="test_store",
        external_id="P-1",
        name="Widget A",
        category="Electronics",
        unit_price=100.0,
    )
    prod2 = Product(
        source_name="test_store",
        external_id="P-2",
        name="Widget B",
        category="Apparel",
        unit_price=50.0,
    )
    session.add_all([prod1, prod2])
    session.commit()

    # Create Orders
    now = datetime.now(timezone.utc)
    o1 = Order(
        source_name="test_store",
        external_id="O-1",
        customer_id=cust1.id,
        order_date=now,
        status="completed",
        total_amount=150.0,
        currency="USD",
        total_amount_usd=150.0,
    )
    o2 = Order(
        source_name="test_store",
        external_id="O-2",
        customer_id=cust1.id,
        order_date=now,
        status="completed",
        total_amount=200.0,
        currency="USD",
        total_amount_usd=200.0,
    )
    o3 = Order(
        source_name="test_store",
        external_id="O-3",
        customer_id=cust2.id,
        order_date=now,
        status="cancelled",
        total_amount=100.0,
        currency="USD",
        total_amount_usd=100.0,
    )
    session.add_all([o1, o2, o3])
    session.commit()

    # Create Order Items
    item1 = OrderItem(order_id=o1.id, product_id=prod1.id, product_name="Widget A", quantity=1, unit_price=100.0, line_total=100.0)
    item2 = OrderItem(order_id=o1.id, product_id=prod2.id, product_name="Widget B", quantity=1, unit_price=50.0, line_total=50.0)
    item3 = OrderItem(order_id=o2.id, product_id=prod1.id, product_name="Widget A", quantity=2, unit_price=100.0, line_total=200.0)
    session.add_all([item1, item2, item3])
    session.commit()

    yield session
    session.close()
    engine.dispose()


def test_get_overview_kpis(db_session):
    svc = AnalyticsService(db_session)
    overview = svc.get_overview_kpis(date_range="30d")

    kpis = overview["kpis"]
    assert kpis["revenue"]["current"] == 350.0
    assert kpis["orders"]["current"] == 2
    assert kpis["avg_order_value"]["current"] == 175.0
    assert kpis["active_customers"]["current"] == 1
    assert kpis["cancellation_rate"]["current"] == 33.33  # 1 cancelled out of 3 total attempts


def test_get_revenue_trends(db_session):
    svc = AnalyticsService(db_session)
    trends = svc.get_revenue_trends(date_range="30d")

    assert len(trends) >= 1
    today_trend = trends[0]
    assert today_trend["orders"] == 2
    assert today_trend["revenue"] == 350.0


def test_get_sales_breakdown(db_session):
    svc = AnalyticsService(db_session)
    breakdown = svc.get_sales_breakdown(date_range="30d")

    # Categories
    categories = {c["category"]: c["revenue"] for c in breakdown["by_category"]}
    assert "Electronics" in categories
    assert categories["Electronics"] == 300.0
    assert categories["Apparel"] == 50.0
    category_shares = {c["category"]: c["percentage_of_total"] for c in breakdown["by_category"]}
    assert category_shares["Electronics"] == 85.71
    assert category_shares["Apparel"] == 14.29

    # Top products
    top_prods = breakdown["top_products"]
    assert len(top_prods) >= 2
    assert top_prods[0]["name"] == "Widget A"
    assert top_prods[0]["revenue"] == 300.0


def test_get_customer_analytics(db_session):
    svc = AnalyticsService(db_session)
    cust_analytics = svc.get_customer_analytics(date_range="30d")

    summary = cust_analytics["summary"]
    assert summary["total_registered_customers"] == 2
    assert summary["repeat_customer_rate"] == 100.0  # 1 customer with completed orders, who has >1 order


    top_custs = cust_analytics["top_customers"]
    assert len(top_custs) >= 1
    assert top_custs[0]["lifetime_value"] == 350.0


def test_get_business_alerts(db_session):
    svc = AnalyticsService(db_session)
    alerts = svc.get_business_alerts(date_range="30d")

    # Should detect high cancellation rate alert (33.33% > 5.0%)
    alert_ids = [a["id"] for a in alerts]
    assert "alert_high_cancellation" in alert_ids


def test_get_ai_context(db_session):
    svc = AnalyticsService(db_session)
    context = svc.get_ai_context(date_range="30d")

    assert context["context_type"] == "business_analytics_snapshot"
    assert "headline_kpis" in context
    assert "business_alerts" in context
    assert "sales_performance" in context
    assert context["headline_kpis"]["revenue"]["current"] == 350.0


def test_inventory_risk_uses_stock_level_and_recent_sales(db_session):
    product = db_session.query(Product).filter_by(external_id="P-1").one()
    product.stock_quantity = 3
    product.reorder_point = 5
    db_session.commit()

    inventory = AnalyticsService(db_session).get_inventory_risk("test_store")
    result = next(item for item in inventory["products"] if item["sku"] is None and item["name"] == "Widget A")
    assert result["stock_quantity"] == 3
    assert result["units_sold_last_30d"] == 3
    assert result["estimated_days_of_cover"] == 30.0
    assert result["at_risk"] is True


def test_non_usd_orders_are_not_added_to_usd_revenue(db_session):
    db_session.add(Order(
        source_name="test_store",
        external_id="O-GBP",
        order_date=datetime.now(timezone.utc),
        status="completed",
        total_amount=1000,
        currency="GBP",
        total_amount_usd=None,
    ))
    db_session.commit()

    overview = AnalyticsService(db_session).get_overview_kpis("30d")
    assert overview["kpis"]["revenue"]["current"] == 350.0
    assert overview["unconverted_orders_excluded"] == 1
