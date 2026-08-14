"""Command persistence port for task images."""

from abc import ABC, abstractmethod
from typing import Sequence

from core_logic.entities.task import (
    TaskImageSaveParams,
    TaskImagesSaveResult,
)


class ITaskImageCommandRepository(ABC):
    @abstractmethod
    def save_task_images(
        self,
        task_id: str,
        images: Sequence[TaskImageSaveParams],
    ) -> TaskImagesSaveResult:
        """Persist task images and return change counts."""
