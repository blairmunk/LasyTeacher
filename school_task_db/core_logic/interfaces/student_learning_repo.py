"""Student learning history repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from core_logic.entities.student import (
    RemedialWizardPreviewSource,
    StudentParticipationProfile,
    StudentRemedialSource,
    StudentTaskResultProfile,
    TaskResultsSource,
    WorkGroupRef,
)


class IStudentLearningRepository(ABC):
    @abstractmethod
    def get_task_results_source_for_event(
        self,
        student_id: str,
        event_id: str,
    ) -> Optional[TaskResultsSource]:
        """Return task-level grading facts for an event."""

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
    def get_student_remedial_source(
        self,
        student_id: str,
    ) -> StudentRemedialSource:
        """Return task history and remedial candidates."""

    @abstractmethod
    def get_remedial_wizard_preview_source(
        self,
        group_id: str,
    ) -> Optional[RemedialWizardPreviewSource]:
        """Return facts needed for class remedial planning."""

    @abstractmethod
    def get_work_group_refs(self, work_ids: List[str]) -> List[WorkGroupRef]:
        """Return analog groups used by works."""
