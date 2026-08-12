"""Command persistence port for task image position diagnostics."""

from abc import ABC, abstractmethod
from typing import Sequence

from core_logic.entities.task_image_audit import TaskImagePositionSuggestion


class ITaskImageAuditCommandRepository(ABC):
    @abstractmethod
    def apply_position_suggestions(
        self,
        suggestions: Sequence[TaskImagePositionSuggestion],
    ) -> int:
        """Apply positions to still-unpositioned images and return update count."""
