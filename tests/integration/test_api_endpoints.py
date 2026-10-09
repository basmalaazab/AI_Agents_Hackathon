"""
Integration tests for FastAPI endpoints.
Tests health check, CSV upload, source listing, pipeline trigger, and data query endpoints.
"""
import pytest
import uuid
from io import BytesIO
from types import SimpleNamespace
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import DataSource


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

    # Seed default source for testing
    with TestingSessionLocal() as session:
        mock_source = DataSource(
            name="mock_ecommerce_api",
            source_type="mock_api",
            description="Mock source",
        )
        session.add(mock_source)
        session.commit()

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


def test_health_check(test_client):
    response = test_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] in ["healthy", "degraded"]


def test_list_sources(test_client):
    response = test_client.get("/api/v1/sources")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(s["name"] == "mock_ecommerce_api" for s in data)


def test_register_unsupported_source_type_is_rejected(test_client):
    response = test_client.post(
        "/api/v1/sources",
        json={"name": "unsupported_shopify", "source_type": "shopify"},
    )

    assert response.status_code == 422


def test_upload_customer_csv(test_client):
    csv_content = (
        b"customer_id,email,first_name,last_name,city,country\n"
        b"CUST-001,john.doe@example.com,John,Doe,Austin,USA\n"
        b"CUST-002,jane.doe@example.com,Jane,Doe,Dallas,USA\n"
    )
    files = {"file": ("customers.csv", BytesIO(csv_content), "text/csv")}
    data = {"record_type": "customer", "source_name": "api_test_source"}

    response = test_client.post("/api/v1/upload/csv", files=files, data=data)
    assert response.status_code == 200
    res = response.json()
    assert res["records_fetched"] == 2
    assert res["records_inserted"] == 2
    assert res["records_invalid"] == 0


def test_upload_customer_csv_deduplication(test_client):
    # Ingest the exact same data again
    csv_content = (
        b"customer_id,email,first_name,last_name,city,country\n"
        b"CUST-001,john.doe@example.com,John,Doe,Austin,USA\n"
        b"CUST-002,jane.doe@example.com,Jane,Doe,Dallas,USA\n"
    )
    files = {"file": ("customers.csv", BytesIO(csv_content), "text/csv")}
    data = {"record_type": "customer", "source_name": "api_test_source"}

    response = test_client.post("/api/v1/upload/csv", files=files, data=data)
    assert response.status_code == 200
    res = response.json()
    assert res["records_inserted"] == 0
    assert res["records_duplicate"] == 2


def test_import_public_uci_sample_is_workspace_scoped_and_audited(test_client, monkeypatch):
    from app.api import uploads

    imported_types = []

    def fake_ingest(self, data_source, record_type, file_content, triggered_by):
        assert data_source.workspace_id is not None
        assert data_source.name.startswith("ws_")
        assert file_content
        assert triggered_by == "public_sample"
        imported_types.append(record_type)
        return SimpleNamespace(
            id=uuid.uuid4(),
            status="success",
            records_fetched=1,
            records_valid=1,
            records_invalid=0,
            records_inserted=1,
            records_duplicate=0,
            error_message=None,
        )

    monkeypatch.setattr(uploads.IngestionService, "run_csv_ingestion", fake_ingest)
    response = test_client.post("/api/v1/upload/public-sample/uci-online-retail")

    assert response.status_code == 200, response.text
    result = response.json()
    assert result["source_name"] == "uci_online_retail"
    assert result["period"] == "2010-12-01 to 2011-12-09"
    assert result["attribution"].endswith("CC BY 4.0")
    assert [run["record_type"] for run in result["runs"]] == ["customer", "product", "order"]
    assert imported_types == ["customer", "product", "order"]
    assert all(run["status"] == "success" for run in result["runs"])


def test_upload_sales_csv_and_query_analytics(test_client):
    csv_content = (
        b"order_id,customer_id,order_date,total_amount,currency,status\n"
        b"ORD-101,CUST-001,2024-03-01,150.00,USD,completed\n"
        b"ORD-102,CUST-002,2024-03-02,250.00,USD,completed\n"
    )
    files = {"file": ("sales.csv", BytesIO(csv_content), "text/csv")}
    data = {"record_type": "order", "source_name": "api_test_source"}

    response = test_client.post("/api/v1/upload/csv", files=files, data=data)
    assert response.status_code == 200
    res = response.json()
    assert res["records_inserted"] == 2

    # Query clean orders
    orders_resp = test_client.get("/api/v1/data/orders")
    assert orders_resp.status_code == 200
    orders = orders_resp.json()
    assert len(orders) >= 2

    # Query analytics
    rev_resp = test_client.get("/api/v1/data/analytics/revenue-summary")
    assert rev_resp.status_code == 200
    rev = rev_resp.json()
    assert rev["total_orders"] >= 2
    assert rev["total_revenue_usd"] >= 400.0


def test_pipeline_summary(test_client):
    response = test_client.get("/api/v1/pipelines/summary")
    assert response.status_code == 200
    summary = response.json()
    assert summary["total_runs"] >= 2
    assert summary["total_customers"] >= 2
    assert summary["total_orders"] >= 2
