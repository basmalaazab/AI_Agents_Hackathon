"""Connectors package — connector registry."""
from app.connectors.base import BaseConnector
from app.connectors.csv_connector import CSVConnector
from app.connectors.mock_api_connector import MockAPIConnector
from app.connectors.spreadsheet_connector import SpreadsheetConnector

# Registry: source_type → connector class
CONNECTOR_REGISTRY: dict[str, type[BaseConnector]] = {
    "csv": CSVConnector,
    "mock_api": MockAPIConnector,
    "spreadsheet": SpreadsheetConnector,
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
    "MockAPIConnector",
    "SpreadsheetConnector",
    "CONNECTOR_REGISTRY",
    "get_connector",
]
