from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from scraper.models import ProductSnapshot


class Source(ABC):
    @abstractmethod
    def fetch(self) -> list[ProductSnapshot]:
        """Return a list of snapshots (one per product/model)."""
        raise NotImplementedError
