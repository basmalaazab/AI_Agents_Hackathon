"""
Unit tests for Person 3 AI Agent Service & SQL Safety Validator.
"""
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Customer, Order, OrderItem, Product, DataSource
from app.services.ai_agent_service import AIAgentService, SQLSafetyValidator


# ---------------------------------------------------------------------------
# SQL Safety Validator Tests
# ---------------------------------------------------------------------------

class TestSQLSafetyValidator:
    """Verifies that SQL safety guardrails strictly prevent SQL injection & write operations."""

    def test_allow_safe_select(self):
        is_safe, error = SQLSafetyValidator.validate("SELECT * FROM orders WHERE status = 'completed'")
        assert is_safe is True
        assert error is None

    def test_allow_safe_with_cte(self):
        query = (
            "WITH recent_sales AS (SELECT * FROM orders WHERE total_amount_usd > 100) "
            "SELECT COUNT(*) FROM recent_sales"
        )
        is_safe, error = SQLSafetyValidator.validate(query)
        assert is_safe is True
        assert error is None

    def test_allow_join_on_whitelisted_tables(self):
        query = (
            "SELECT c.email, o.total_amount_usd FROM customers c "
            "JOIN orders o ON o.customer_id = c.id"
        )
        is_safe, error = SQLSafetyValidator.validate(query)
        assert is_safe is True
        assert error is None

    def test_block_drop_table(self):
        is_safe, error = SQLSafetyValidator.validate("DROP TABLE orders;")
        assert is_safe is False
        assert "must begin with SELECT, WITH, or EXPLAIN" in error or "Prohibited" in error

    def test_block_delete(self):
        is_safe, error = SQLSafetyValidator.validate("DELETE FROM customers WHERE id IS NOT NULL")
        assert is_safe is False

    def test_block_insert(self):
        is_safe, error = SQLSafetyValidator.validate("INSERT INTO products (name) VALUES ('Hacked Product')")
        assert is_safe is False

    def test_block_update(self):
        is_safe, error = SQLSafetyValidator.validate("UPDATE orders SET total_amount = 0")
        assert is_safe is False

    def test_block_multi_statement_piggybacking(self):
        is_safe, error = SQLSafetyValidator.validate("SELECT * FROM orders; DROP TABLE customers")
        assert is_safe is False
        assert "Multi-statement queries" in error

    def test_block_unauthorized_table(self):
        is_safe, error = SQLSafetyValidator.validate("SELECT * FROM sensitive_admin_passwords")
        assert is_safe is False
        assert "not in the allowed business tables whitelist" in error

    def test_block_system_catalogs(self):
        is_safe, error = SQLSafetyValidator.validate("SELECT * FROM pg_catalog.pg_tables")
        assert is_safe is False

    def test_sanitize_and_limit_adds_limit(self):
        limited = SQLSafetyValidator.sanitize_and_limit("SELECT * FROM orders", max_rows=25)
        assert "LIMIT 25" in limited

    def test_sanitize_and_limit_preserves_existing_limit(self):
        limited = SQLSafetyValidator.sanitize_and_limit("SELECT * FROM orders LIMIT 10", max_rows=50)
        assert "LIMIT 10" in limited


# ---------------------------------------------------------------------------
# AI Agent Service Tests
# ---------------------------------------------------------------------------

@pytest.fixture
def agent_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed data for testing
    src = DataSource(name="test_store", source_type="csv")
    session.add(src)
    session.commit()

    cust1 = Customer(source_name="test_store", external_id="C1", email="alice@test.com", first_name="Alice", last_name="Smith")
    cust2 = Customer(source_name="test_store", external_id="C2", email="bob@test.com", first_name="Bob", last_name="Jones")
    session.add_all([cust1, cust2])
    session.commit()

    prod = Product(source_name="test_store", external_id="P1", name="Wireless Mouse", sku="WM-01", category="Electronics", unit_price=29.99)
    session.add(prod)
    session.commit()

    o1 = Order(
        source_name="test_store",
        external_id="ORD-1",
        customer_id=cust1.id,
        order_date=datetime.now(timezone.utc),
        status="completed",
        total_amount=150.00,
        currency="USD",
        total_amount_usd=150.00,
    )
    session.add(o1)
    session.commit()

    item1 = OrderItem(
        order_id=o1.id,
        product_id=prod.id,
        product_name="Wireless Mouse",
        sku="WM-01",
        quantity=5,
        unit_price=30.00,
        line_total=150.00,
        currency="USD",
    )
    session.add(item1)
    session.commit()

    yield session

    session.close()
    engine.dispose()


class TestAIAgentService:
    """Verifies Person 3 AI Agent core functionality."""

    def test_schema_metadata(self, agent_session):
        svc = AIAgentService(agent_session)
        meta = svc.get_schema_metadata()
        assert "tables" in meta
        assert "customers" in meta["tables"]
        assert "orders" in meta["tables"]
        assert "order_items" in meta["tables"]
        assert "products" in meta["tables"]
        assert meta["guardrails"]["read_only"] is True

    def test_execute_safe_sql(self, agent_session):
        svc = AIAgentService(agent_session)
        res = svc.execute_safe_sql("SELECT status, total_amount_usd FROM orders")
        assert res["success"] is True
        assert res["row_count"] == 1
        assert res["rows"][0]["status"] == "completed"
        assert res["rows"][0]["total_amount_usd"] == 150.0

    def test_execute_unsafe_sql_rejected(self, agent_session):
        svc = AIAgentService(agent_session)
        res = svc.execute_safe_sql("DROP TABLE orders")
        assert res["success"] is False
        assert "error" in res

    def test_process_query_revenue(self, agent_session):
        svc = AIAgentService(agent_session)
        resp = svc.process_query("What was our total revenue this month?")
        assert resp["intent"] == "revenue_analysis"
        assert "Revenue" in resp["answer"]
        assert resp["metrics_snapshot"]["revenue"] == 150.0
        assert len(resp["suggested_followups"]) > 0

    def test_process_query_products(self, agent_session):
        svc = AIAgentService(agent_session)
        resp = svc.process_query("Which products are top sellers?")
        assert resp["intent"] == "product_analysis"
        assert "Wireless Mouse" in resp["answer"]
        assert len(resp["suggested_followups"]) > 0

    def test_process_query_customer_retention(self, agent_session):
        svc = AIAgentService(agent_session)
        resp = svc.process_query("How are our repeat customers and churn risk?")
        assert resp["intent"] == "customer_analysis"
        assert "Repeat Customer Rate" in resp["answer"]

    def test_generate_recommendations(self, agent_session):
        svc = AIAgentService(agent_session)
        recs = svc.generate_recommendations()
        assert recs["total_recommendations"] > 0
        assert "executive_summary" in recs
        assert len(recs["recommendations"]) > 0
        assert "action_steps" in recs["recommendations"][0]
        assert "priority" in recs["recommendations"][0]

    def test_diagnose_anomalies(self, agent_session):
        svc = AIAgentService(agent_session)
        diagnoses = svc.diagnose_anomalies()
        assert isinstance(diagnoses, list)
        assert len(diagnoses) > 0
        assert "title" in diagnoses[0]
        assert "mitigation_actions" in diagnoses[0]

    def test_get_suggested_queries(self, agent_session):
        svc = AIAgentService(agent_session)
        suggestions = svc.get_suggested_queries()
        assert len(suggestions) > 0
        assert "prompt" in suggestions[0]
        assert "category" in suggestions[0]
