"""Transaction boundary port for application use cases."""

from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from typing import Any


class ITransactionManager(ABC):
    @abstractmethod
    def atomic(self) -> AbstractContextManager[Any]:
        """Return a context manager that commits or rolls back all writes."""
