"""
Integration tests for Person 3 AI Agent API Endpoints.
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
        source = DataSource(name="agent_demo_source", source_type="csv")
        session.add(source)
        session.commit()

        c1 = Customer(
            source_name="agent_demo_source",
            external_id="C-1",
            email="sarah.connor@example.com",
            first_name="Sarah",
            last_name="Connor",
        )
        session.add(c1)
        session.commit()

        p1 = Product(
            source_name="agent_demo_source",
            external_id="P-101",
            name="Mechanical Keyboard",
            sku="MK-101",
            category="Office Equipment",
            unit_price=120.0,
            currency="USD",
        )
        session.add(p1)
        session.commit()

        order = Order(
            source_name="agent_demo_source",
            external_id="ORD-999",
            customer_id=c1.id,
            order_date=datetime.now(timezone.utc),
            status="completed",
            total_amount=240.0,
            currency="USD",
            total_amount_usd=240.0,
        )
        session.add(order)
        session.commit()

        item = OrderItem(
            order_id=order.id,
            product_id=p1.id,
            product_name="Mechanical Keyboard",
            sku="MK-101",
            quantity=2,
            unit_price=120.0,
            line_total=240.0,
            currency="USD",
        )
        session.add(item)
        session.commit()

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


class TestAIAgentAPI:
    """Tests for /api/v1/agent endpoints."""

    def test_agent_query_revenue(self, test_client):
        resp = test_client.post(
            "/api/v1/agent/query",
            json={"query": "What is our total revenue?", "date_range": "30d"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] == "revenue_analysis"
        assert "Revenue" in data["answer"]
        assert data["metrics_snapshot"]["revenue"] == 240.0
        assert len(data["suggested_followups"]) > 0

    def test_agent_query_products(self, test_client):
        resp = test_client.post(
            "/api/v1/agent/query",
            json={"query": "What are our top products?", "date_range": "30d"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] == "product_analysis"
        assert "Mechanical Keyboard" in data["answer"]

    def test_agent_recommendations(self, test_client):
        resp = test_client.post(
            "/api/v1/agent/recommendations",
            json={"date_range": "30d"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "recommendations" in data
        assert "executive_summary" in data
        assert data["total_recommendations"] > 0
        assert "action_steps" in data["recommendations"][0]

    def test_agent_diagnose(self, test_client):
        resp = test_client.post(
            "/api/v1/agent/diagnose",
            json={"date_range": "30d"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "mitigation_actions" in data[0]

    def test_agent_safe_sql_disabled(self, test_client):
        resp = test_client.post(
            "/api/v1/agent/sql",
            json={"query": "SELECT status, total_amount_usd FROM orders LIMIT 5"},
        )
        assert resp.status_code == 403
        data = resp.json()
        assert "Direct SQL access is disabled" in data["detail"]

    def test_agent_unsafe_sql_blocked(self, test_client):
        resp = test_client.post(
            "/api/v1/agent/sql",
            json={"query": "DROP TABLE orders"},
        )
        assert resp.status_code in (400, 403)


    def test_agent_suggestions(self, test_client):
        resp = test_client.get("/api/v1/agent/suggestions?date_range=30d")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "prompt" in data[0]

    def test_agent_capabilities(self, test_client):
        resp = test_client.get("/api/v1/agent/capabilities")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "AI Business Intelligence Agent (Person 3)"
        assert "database_schema" in data
        assert "security_guardrails" in data
