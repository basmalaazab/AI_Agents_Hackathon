"""Connectors package — connector registry."""
from app.connectors.base import BaseConnector
from app.connectors.csv_connector import CSVConnector
from app.connectors.hubspot_connector import HubSpotConnector
from app.connectors.mock_api_connector import MockAPIConnector
from app.connectors.spreadsheet_connector import SpreadsheetConnector
from app.connectors.stripe_connector import StripeConnector

# Registry: source_type → connector class
CONNECTOR_REGISTRY: dict[str, type[BaseConnector]] = {
    "csv": CSVConnector,
    "mock_api": MockAPIConnector,
    "spreadsheet": SpreadsheetConnector,
    "hubspot": HubSpotConnector,
    "stripe": StripeConnector,
}


def get_connector(source_type: str, source_name: str, config: dict | None = None) -> BaseConnector:
    """Instantiate a connector by source_type string."""
    cls = CONNECTOR_REGISTRY.get(source_type)
    if cls is None:
        raise ValueError(
            f"Unknown source_type={source_type!r}. "
            f"Available: {list(CONNECTOR_REGISTRY)}"
        )
    return cls(source_name=source_name, config=config)


__all__ = [
    "BaseConnector",
    "CSVConnector",
    "HubSpotConnector",
    "MockAPIConnector",
    "SpreadsheetConnector",
    "StripeConnector",
    "CONNECTOR_REGISTRY",
    "get_connector",
]
