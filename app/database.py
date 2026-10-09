"""
SQLAlchemy engine and session factory.
"""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker, with_loader_criteria
from sqlalchemy import event

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def _make_engine():
    settings = get_settings()
    if settings.database_url.startswith("sqlite"):
        return create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False},
            echo=settings.is_development,
        )
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        echo=settings.is_development,
    )


engine = _make_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@event.listens_for(Session, "do_orm_execute")
def _apply_workspace_scope(execute_state):
    """Apply workspace isolation to ORM reads in authenticated requests."""
    db = execute_state.session
    if not execute_state.is_select or "workspace_id" not in db.info or db.info.get("skip_workspace_scope"):
        return
    from app.models import (Customer, DataQualityError, DataSource, IngestionRun,
                            Order, OrderItem, Product, RawRecord)

    workspace_id = db.info["workspace_id"]
    source_names = tuple(db.info.get("workspace_source_names", ()))
    source_ids = tuple(db.info.get("workspace_source_ids", ()))
    execute_state.statement = execute_state.statement.options(
        with_loader_criteria(DataSource, lambda m: m.workspace_id == workspace_id, include_aliases=True),
        with_loader_criteria(Customer, lambda m: m.source_name.in_(source_names), include_aliases=True),
        with_loader_criteria(Order, lambda m: m.source_name.in_(source_names), include_aliases=True),
        with_loader_criteria(Product, lambda m: m.source_name.in_(source_names), include_aliases=True),
        with_loader_criteria(OrderItem, lambda m: m.order.has(Order.source_name.in_(source_names)), include_aliases=True),
        with_loader_criteria(IngestionRun, lambda m: m.data_source_id.in_(source_ids), include_aliases=True),
        with_loader_criteria(RawRecord, lambda m: m.data_source_id.in_(source_ids), include_aliases=True),
        with_loader_criteria(DataQualityError, lambda m: m.data_source_id.in_(source_ids), include_aliases=True),
    )


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager for use outside FastAPI dependency injection."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_db_connection() -> bool:
    """Returns True if the database connection is healthy."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def ensure_product_inventory_columns() -> None:
    """Add optional inventory fields to existing MVP databases."""
    inspector = inspect(engine)
    if "products" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("products")}
    with engine.begin() as connection:
        for column in ("stock_quantity", "reorder_point"):
            if column not in existing:
                connection.execute(text(f"ALTER TABLE products ADD COLUMN {column} INTEGER"))


def ensure_currency_columns() -> None:
    """Add normalized USD amount to order items in existing installations."""
    inspector = inspect(engine)
    if "order_items" not in inspector.get_table_names():
        return
    existing = {column["name"] for column in inspector.get_columns("order_items")}
    added = "line_total_usd" not in existing
    if added:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE order_items ADD COLUMN line_total_usd NUMERIC(12, 2)"))
    if added:
        from app.models.order import Order
        from app.models.order_item import OrderItem
        from app.pipeline.cleaner import convert_to_usd
        with SessionLocal() as db:
            for order in db.query(Order).all():
                order.total_amount_usd = convert_to_usd(order.total_amount, order.currency)
            for item in db.query(OrderItem).all():
                item.line_total_usd = convert_to_usd(item.line_total, item.currency)
            db.commit()


def ensure_workspace_columns() -> None:
    """Migrate existing local databases and attach existing demo data to a workspace."""
    from app.models.auth import Workspace
    import uuid

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if "workspaces" not in tables:
        return
    source_columns = {col["name"] for col in inspector.get_columns("data_sources")} if "data_sources" in tables else set()
    user_columns = {col["name"] for col in inspector.get_columns("app_users")} if "app_users" in tables else set()
    workspace_sql_type = "UUID" if engine.dialect.name == "postgresql" else "VARCHAR(36)"
    with engine.begin() as connection:
        if "workspace_id" not in source_columns:
            connection.execute(text(f"ALTER TABLE data_sources ADD COLUMN workspace_id {workspace_sql_type}"))
        if "display_name" not in source_columns:
            connection.execute(text("ALTER TABLE data_sources ADD COLUMN display_name VARCHAR(120)"))
        if "workspace_id" not in user_columns:
            connection.execute(text(f"ALTER TABLE app_users ADD COLUMN workspace_id {workspace_sql_type}"))
    with SessionLocal() as db:
        workspace = db.query(Workspace).first()
        if workspace is None:
            workspace = Workspace(id=uuid.uuid4(), name="Demo Company")
            db.add(workspace)
            db.commit()
            db.refresh(workspace)
        with engine.begin() as connection:
            workspace_value = "CAST(:wid AS UUID)" if engine.dialect.name == "postgresql" else ":wid"
            workspace_id_value = str(workspace.id) if engine.dialect.name == "postgresql" else workspace.id.hex
            if "data_sources" in tables:
                connection.execute(text(f"UPDATE data_sources SET workspace_id = {workspace_value} WHERE workspace_id IS NULL"), {"wid": workspace_id_value})
                connection.execute(text("UPDATE data_sources SET display_name = name WHERE display_name IS NULL OR display_name = ''"))
            if "app_users" in tables:
                connection.execute(text(f"UPDATE app_users SET workspace_id = {workspace_value} WHERE workspace_id IS NULL"), {"wid": workspace_id_value})
