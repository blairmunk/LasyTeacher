"""Query port for validating explicit task classifications."""

from abc import ABC, abstractmethod
from typing import Tuple

from core_logic.entities.task import TaskClassificationOptions


class ITaskClassificationRepository(ABC):
    @abstractmethod
    def get_classification_options(
        self,
        topic_id: str,
    ) -> TaskClassificationOptions:
        """Return active classifications compatible with the topic subject."""

    @abstractmethod
    def get_classification_errors(
        self,
        topic_id: str,
        content_entry_ids: Tuple[str, ...],
        requirement_ids: Tuple[str, ...],
    ) -> Tuple[str, ...]:
        """Return errors for missing or incompatible classifications."""
