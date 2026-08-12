"""Read-only persistence port for task image position diagnostics."""

from abc import ABC, abstractmethod
from typing import Sequence

from core_logic.entities.task_image_audit import TaskImageAuditSource


class ITaskImageAuditQueryRepository(ABC):
    @abstractmethod
    def list_task_images(self) -> Sequence[TaskImageAuditSource]:
        """Return task image facts needed by the audit."""
