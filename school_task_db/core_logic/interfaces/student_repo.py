"""Student repository interface."""

from abc import ABC, abstractmethod
from typing import Any, List, Optional

from core_logic.entities.student import (
    RemedialWizardPreviewData,
    StudentDetail,
    StudentListItem,
    StudentGroupDetail,
    StudentGroupListItem,
    StudentRemedialWorkData,
    StudentGroupRef,
    StudentParticipationProfile,
    StudentTaskLogProfile,
    TaskResult,
    WorkGroupRef,
)


class IStudentRepository(ABC):
    @abstractmethod
    def get_list_students(self) -> List[StudentListItem]:
        """Return students for the student list page."""

    @abstractmethod
    def get_list_student_groups(self) -> List[StudentGroupListItem]:
        """Return student groups/classes for the group list page."""

    @abstractmethod
    def get_student(self, student_id: str) -> Optional[StudentDetail]:
        """Return one student detail read model, or None."""

    @abstractmethod
    def get_student_group(self, group_id: str) -> Optional[StudentGroupDetail]:
        """Return one student group detail read model, or None."""

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
    def get_all_student_groups(self) -> List[StudentGroupRef]:
        """Return all student groups/classes for selection controls."""

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
    def get_student_remedial_work_data(
        self,
        student_id: str,
    ) -> StudentRemedialWorkData:
        """Return data for a student's remedial work page."""

    @abstractmethod
    def get_student_short_name(self, student_id: str) -> str:
        """Return student's short display name."""

    @abstractmethod
    def get_group_name(self, group_id: str) -> Optional[str]:
        """Return a student group name."""

    @abstractmethod
    def select_student_remedial_task_ids(
        self,
        student_id: str,
        max_tasks: int,
        selected_group_ids: List[str],
    ) -> List[str]:
        """Return task IDs for a single-student remedial variant."""

    @abstractmethod
    def get_remedial_wizard_preview_data(
        self,
        group_id: str,
        threshold: int,
        limit_type: str,
        limit_value: int,
        work_name: str,
    ) -> RemedialWizardPreviewData:
        """Return preview data for class remedial wizard step 2."""

    @abstractmethod
    def get_work_group_refs(self, work_ids: List[str]) -> List[WorkGroupRef]:
        """Return analog groups used by works."""
