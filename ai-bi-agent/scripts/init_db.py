"""
Database initialisation script.
Creates all tables defined in SQLAlchemy models.
Safe to run multiple times (uses CREATE TABLE IF NOT EXISTS semantics).
"""
import sys
import os

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from app.database import Base, engine
from app.models import (  # noqa: F401 — import triggers model registration
    DataSource, IngestionRun, RawRecord,
    Customer, Product, Order, OrderItem, DataQualityError,
)
from app.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db():
    settings = get_settings()
    logger.info("Initialising database at: %s", settings.database_url.split("@")[-1])
    Base.metadata.create_all(bind=engine)
    logger.info("All tables created successfully.")


def seed_default_sources():
    """Register default data sources if they do not already exist."""
    from sqlalchemy.orm import sessionmaker
    from app.models.data_source import DataSource

    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        sources = [
            {
                "name": "mock_ecommerce_api",
                "source_type": "mock_api",
                "description": "Mock e-commerce REST API (synthetic data only)",
            },
            {
                "name": "csv_upload",
                "source_type": "csv",
                "description": "Manual CSV file uploads",
            },
        ]
        for s in sources:
            existing = db.query(DataSource).filter_by(name=s["name"]).first()
            if not existing:
                db.add(DataSource(**s))
                logger.info("Seeded data source: %s", s["name"])
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Failed to seed data sources: %s", e)
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    seed_default_sources()
    logger.info("Database initialisation complete.")
