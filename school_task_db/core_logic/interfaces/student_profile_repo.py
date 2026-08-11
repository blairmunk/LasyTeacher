"""Repository interface for student profile learning history."""

from abc import ABC, abstractmethod
from typing import List

from core_logic.entities.student import (
    StudentParticipationProfile,
    StudentTaskResultProfile,
    WorkGroupRef,
)


class IStudentProfileRepository(ABC):
    @abstractmethod
    def get_profile_participations(
        self,
        student_id: str,
    ) -> List[StudentParticipationProfile]:
        """Return participation history for a student profile."""

    @abstractmethod
    def get_task_logs(
        self,
        student_id: str,
    ) -> List[StudentTaskResultProfile]:
        """Return task-level learning history for a student."""

    @abstractmethod
    def get_work_group_refs(self, work_ids: List[str]) -> List[WorkGroupRef]:
        """Return analog groups used by works."""
