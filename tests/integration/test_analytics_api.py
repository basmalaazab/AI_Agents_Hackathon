"""
Integration tests for Analytics API endpoints.
"""
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import Customer, Order, OrderItem, Product, DataSource


@pytest.fixture(scope="module")
def test_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def test_client(test_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Seed data
    with TestingSessionLocal() as session:
        source = DataSource(name="api_demo_source", source_type="csv", description="API Test Source")
        session.add(source)
        session.commit()

        cust = Customer(
            source_name="api_demo_source",
            external_id="CUST-100",
            email="test.client@example.com",
            first_name="Test",
            last_name="User",
        )
        session.add(cust)
        session.commit()

        order1 = Order(
            source_name="api_demo_source",
            external_id="ORD-100",
            customer_id=cust.id,
            order_date=datetime.now(timezone.utc),
            status="completed",
            total_amount=500.0,
            currency="USD",
            total_amount_usd=500.0,
        )
        session.add(order1)
        session.commit()

        item = OrderItem(order_id=order1.id, product_name="Premium Laptop", quantity=1, unit_price=500.0, line_total=500.0)
        session.add(item)
        session.commit()

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


def test_analytics_overview_endpoint(test_client):
    res = test_client.get("/api/v1/analytics/overview?date_range=30d")
    assert res.status_code == 200
    data = res.json()
    assert "kpis" in data
    assert data["kpis"]["revenue"]["current"] >= 500.0
    assert data["kpis"]["orders"]["current"] >= 1


def test_analytics_revenue_trends_endpoint(test_client):
    res = test_client.get("/api/v1/analytics/revenue-trends?date_range=30d")
    assert res.status_code == 200
    trends = res.json()
    assert isinstance(trends, list)
    assert len(trends) >= 1
    assert trends[0]["revenue"] >= 500.0


def test_analytics_sales_breakdown_endpoint(test_client):
    res = test_client.get("/api/v1/analytics/sales-breakdown?date_range=30d")
    assert res.status_code == 200
    data = res.json()
    assert "by_category" in data
    assert "top_products" in data
    assert len(data["top_products"]) >= 1
    assert data["top_products"][0]["name"] == "Premium Laptop"


def test_analytics_customers_endpoint(test_client):
    res = test_client.get("/api/v1/analytics/customers?date_range=30d")
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "top_customers" in data
    assert data["summary"]["total_registered_customers"] >= 1


def test_analytics_alerts_endpoint(test_client):
    res = test_client.get("/api/v1/analytics/alerts?date_range=30d")
    assert res.status_code == 200
    alerts = res.json()
    assert isinstance(alerts, list)


def test_analytics_ai_context_endpoint(test_client):
    res = test_client.get("/api/v1/analytics/ai-context?date_range=30d")
    assert res.status_code == 200
    ctx = res.json()
    assert ctx["context_type"] == "business_analytics_snapshot"
    assert "headline_kpis" in ctx
    assert "sales_performance" in ctx


def test_analytics_csv_export_endpoint(test_client):
    res = test_client.get("/api/v1/analytics/export/csv?date_range=30d")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    assert "Date,Revenue (USD),Completed Orders" in res.text
