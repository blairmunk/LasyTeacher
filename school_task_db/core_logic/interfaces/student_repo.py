"""Student repository interface."""

from abc import ABC, abstractmethod
from typing import List

from core_logic.entities.student import (
    StudentGroupRef,
    StudentParticipationProfile,
    StudentTaskLogProfile,
    TaskResult,
    WorkGroupRef,
)


class IStudentRepository(ABC):
    @abstractmethod
    def get_task_results_for_event(
        self,
        student_id: str,
        event_id: str,
    ) -> List[TaskResult]:
        """Return the student's task-level results for an event."""

    @abstractmethod
    def get_student_groups(self, student_id: str) -> List[StudentGroupRef]:
        """Return groups/classes containing the student."""

    @abstractmethod
    def get_profile_participations(
        self,
        student_id: str,
    ) -> List[StudentParticipationProfile]:
        """Return participation rows for a student profile."""

    @abstractmethod
    def get_task_logs(self, student_id: str) -> List[StudentTaskLogProfile]:
        """Return task-level learning history for a student."""

    @abstractmethod
    def get_work_group_refs(self, work_ids: List[str]) -> List[WorkGroupRef]:
        """Return analog groups used by works."""
