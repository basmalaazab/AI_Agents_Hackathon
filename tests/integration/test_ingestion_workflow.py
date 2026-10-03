"""
Integration tests for the ingestion workflow.
These tests use an in-memory SQLite database to avoid requiring a running PostgreSQL instance.

Run with: pytest tests/integration/ -v

Note: conftest.py patches JSONB → JSON before these imports for SQLite compatibility.
"""
import pytest
import uuid
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import (
    DataSource, IngestionRun, Customer, Order, Product, DataQualityError
)
from app.models.ingestion_run import RunStatus
from app.services.ingestion_service import IngestionService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_source(db_session):
    source = DataSource(
        name="test_csv_source",
        source_type="csv",
        description="Test source",
    )
    db_session.add(source)
    db_session.flush()
    return source


VALID_CUSTOMERS_CSV = b"""customer_id,email,first_name,last_name,city,country
C001,alice@example.com,Alice,Johnson,New York,USA
C002,bob@example.com,BOB,SMITH,Los Angeles,USA
C003,carol@example.com,Carol,Williams,London,UK
"""

CUSTOMERS_WITH_DUPLICATE_CSV = b"""customer_id,email,first_name,last_name
C001,alice@example.com,Alice,Johnson
C001,alice@example.com,Alice,Johnson
C004,dave@example.com,Dave,Brown
"""

VALID_ORDERS_CSV = b"""order_id,customer_id,order_date,total_amount,currency,status
ORD-001,C001,2024-01-10,149.99,USD,completed
ORD-002,C002,2024-01-15,89.99,USD,completed
ORD-003,C003,2024-01-20,299.99,USD,completed
"""

INVALID_ORDERS_CSV = b"""order_id,customer_id,order_date,total_amount
,C001,2024-01-10,149.99
ORD-002,C002,not-a-date,89.99
ORD-003,C003,2024-01-20,-50.00
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCustomerIngestion:
    def test_ingests_valid_customers(self, db_session, sample_source):
        svc = IngestionService(db_session)
        run = svc.run_csv_ingestion(sample_source, "customer", VALID_CUSTOMERS_CSV)

        assert run.status == RunStatus.SUCCESS
        assert run.records_fetched == 3
        assert run.records_valid == 3
        assert run.records_inserted == 3
        assert run.records_invalid == 0

        customers = db_session.query(Customer).all()
        assert len(customers) == 3

    def test_deduplicates_within_batch(self, db_session, sample_source):
        svc = IngestionService(db_session)
        run = svc.run_csv_ingestion(sample_source, "customer", CUSTOMERS_WITH_DUPLICATE_CSV)

        # C001 appears twice — one removed intra-batch
        assert run.records_fetched == 3  # after dedup: 2 unique
        customers = db_session.query(Customer).all()
        assert len(customers) == 2  # C001 and C004

    def test_no_duplicates_on_second_run(self, db_session, sample_source):
        svc = IngestionService(db_session)
        run1 = svc.run_csv_ingestion(sample_source, "customer", VALID_CUSTOMERS_CSV)
        assert run1.records_inserted == 3

        run2 = svc.run_csv_ingestion(sample_source, "customer", VALID_CUSTOMERS_CSV)
        assert run2.records_inserted == 0
        assert run2.records_duplicate == 3
        # No new customers in DB
        assert db_session.query(Customer).count() == 3

    def test_names_are_cleaned(self, db_session, sample_source):
        svc = IngestionService(db_session)
        svc.run_csv_ingestion(sample_source, "customer", VALID_CUSTOMERS_CSV)

        bob = db_session.query(Customer).filter_by(external_id="C002").first()
        assert bob is not None
        assert bob.first_name == "Bob"
        assert bob.last_name == "Smith"


class TestOrderIngestion:
    def test_ingests_valid_orders(self, db_session, sample_source):
        svc = IngestionService(db_session)
        run = svc.run_csv_ingestion(sample_source, "order", VALID_ORDERS_CSV)

        assert run.status == RunStatus.SUCCESS
        assert run.records_inserted == 3
        assert db_session.query(Order).count() == 3

    def test_invalid_orders_create_quality_errors(self, db_session, sample_source):
        svc = IngestionService(db_session)
        run = svc.run_csv_ingestion(sample_source, "order", INVALID_ORDERS_CSV)

        assert run.records_invalid == 3
        assert run.records_inserted == 0
        assert db_session.query(DataQualityError).count() == 3

    def test_order_dedup_on_rerun(self, db_session, sample_source):
        svc = IngestionService(db_session)
        run1 = svc.run_csv_ingestion(sample_source, "order", VALID_ORDERS_CSV)
        assert run1.records_inserted == 3

        run2 = svc.run_csv_ingestion(sample_source, "order", VALID_ORDERS_CSV)
        assert run2.records_inserted == 0
        assert run2.records_duplicate == 3


class TestRawRecordStorage:
    def test_raw_records_stored(self, db_session, sample_source):
        from app.models.raw_record import RawRecord
        svc = IngestionService(db_session)
        svc.run_csv_ingestion(sample_source, "customer", VALID_CUSTOMERS_CSV)

        raw = db_session.query(RawRecord).all()
        assert len(raw) == 3
        assert all(r.record_type == "customer" for r in raw)

    def test_raw_records_stored_for_invalid(self, db_session, sample_source):
        from app.models.raw_record import RawRecord
        svc = IngestionService(db_session)
        svc.run_csv_ingestion(sample_source, "order", INVALID_ORDERS_CSV)

        raw = db_session.query(RawRecord).all()
        assert len(raw) == 3  # All raw records stored even if invalid


class TestConnectorFailures:
    def test_fetch_failure_is_persisted_as_failed_run(self, db_session, sample_source):
        class FailingConnector:
            def fetch(self, record_type, **kwargs):
                raise RuntimeError("credential rejected")

        svc = IngestionService(db_session)
        run = svc.run_api_ingestion(
            data_source=sample_source,
            record_type="customer",
            connector=FailingConnector(),
            triggered_by="api",
        )

        assert run.status == RunStatus.FAILED
        assert run.error_message == "credential rejected"
        assert db_session.query(IngestionRun).filter_by(id=run.id).one().status == RunStatus.FAILED
