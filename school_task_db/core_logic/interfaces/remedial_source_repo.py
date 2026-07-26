"""Repository interface for source task sets used by remedial selection."""

from abc import ABC, abstractmethod
from typing import Set


class IRemedialSourceRepository(ABC):
    @abstractmethod
    def get_variant_task_ids(self, work_id: str) -> Set[str]:
        """Return task IDs used in all variants of a source work."""

    @abstractmethod
    def get_student_variant_task_ids(
        self,
        work_id: str,
        student_id: str,
        event_id: str,
    ) -> Set[str]:
        """Return task IDs from a student's source variant for an event."""
