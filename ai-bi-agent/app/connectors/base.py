"""
Connector base class.

All connectors must implement:
    fetch(record_type: str, **kwargs) -> list[dict]
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseConnector(ABC):
    """Abstract base class for all data source connectors."""

    source_type: str = "base"

    def __init__(self, source_name: str, config: dict[str, Any] | None = None):
        self.source_name = source_name
        self.config = config or {}

    @abstractmethod
    def fetch(self, record_type: str, **kwargs) -> list[dict]:
        """
        Fetch records from the data source.

        Args:
            record_type: One of 'order', 'customer', 'product'.
            **kwargs: Connector-specific options (e.g. file path, since timestamp).

        Returns:
            A list of raw record dicts.
        """

    def health_check(self) -> bool:
        """Override to provide connectivity checks. Returns True if healthy."""
        return True

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.source_name!r}>"
