"""Repository interface for source task sets used by remedial selection."""

from abc import ABC, abstractmethod
from typing import Set


class IRemedialSourceRepository(ABC):
    @abstractmethod
    def get_event_variant_task_ids(
        self,
        event_id: str,
        student_id: str,
    ) -> Set[str]:
        """Return task IDs from a student's variant in the source event."""
