"""Student repository interface."""

from abc import ABC, abstractmethod
from typing import List

from core_logic.entities.student import TaskResult


class IStudentRepository(ABC):
    @abstractmethod
    def get_task_results_for_event(
        self,
        student_id: str,
        event_id: str,
    ) -> List[TaskResult]:
        """Return the student's task-level results for an event."""

