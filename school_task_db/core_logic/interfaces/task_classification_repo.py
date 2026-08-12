"""Query port for validating explicit task classifications."""

from abc import ABC, abstractmethod
from typing import Tuple


class ITaskClassificationRepository(ABC):
    @abstractmethod
    def get_classification_errors(
        self,
        topic_id: str,
        content_entry_ids: Tuple[str, ...],
        requirement_ids: Tuple[str, ...],
    ) -> Tuple[str, ...]:
        """Return errors for missing or incompatible classifications."""
