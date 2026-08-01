"""Student repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.student import (
    RemedialWizardPreviewSource,
    SaveStudentGroupParams,
    SaveStudentGroupResult,
    SaveStudentParams,
    SaveStudentResult,
    StudentDetail,
    StudentListItem,
    StudentGroupDetail,
    StudentGroupListItem,
    StudentRemedialSource,
    StudentGroupRef,
    StudentParticipationProfile,
    StudentTaskLogProfile,
    TaskLogSyncPlan,
    TaskLogSyncSource,
    TaskResultsSource,
    WorkGroupRef,
)


class IStudentRepository(ABC):
    @abstractmethod
    def get_list_students(
        self,
        year: AcademicYearRef | None = None,
    ) -> List[StudentListItem]:
        """Return students for the student list page."""

    @abstractmethod
    def get_list_student_groups(
        self,
        year: AcademicYearRef | None = None,
    ) -> List[StudentGroupListItem]:
        """Return student groups/classes for the group list page."""

    @abstractmethod
    def get_student(self, student_id: str) -> Optional[StudentDetail]:
        """Return one student detail read model, or None."""

    @abstractmethod
    def get_student_group(self, group_id: str) -> Optional[StudentGroupDetail]:
        """Return one student group detail read model, or None."""

    @abstractmethod
    def create_student(self, params: SaveStudentParams) -> SaveStudentResult:
        """Create a student."""

    @abstractmethod
    def update_student(self, params: SaveStudentParams) -> SaveStudentResult:
        """Update a student, or return not_found status."""

    @abstractmethod
    def create_student_group(
        self,
        params: SaveStudentGroupParams,
    ) -> SaveStudentGroupResult:
        """Create a student group/class."""

    @abstractmethod
    def update_student_group(
        self,
        params: SaveStudentGroupParams,
    ) -> SaveStudentGroupResult:
        """Update a student group/class, or return not_found status."""

    @abstractmethod
    def get_task_results_source_for_event(
        self,
        student_id: str,
        event_id: str,
    ) -> Optional[TaskResultsSource]:
        """Return raw task-level grading facts for an event."""

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
    def get_student_remedial_source(
        self,
        student_id: str,
    ) -> StudentRemedialSource:
        """Return task history and candidates for student remedial work."""

    @abstractmethod
    def get_group_name(self, group_id: str) -> Optional[str]:
        """Return a student group name."""

    @abstractmethod
    def get_remedial_wizard_preview_source(
        self,
        group_id: str,
    ) -> Optional[RemedialWizardPreviewSource]:
        """Return facts needed to build the class remedial preview."""

    @abstractmethod
    def get_work_group_refs(self, work_ids: List[str]) -> List[WorkGroupRef]:
        """Return analog groups used by works."""

    @abstractmethod
    def get_task_log_sync_source(
        self,
        mark_id: str,
    ) -> Optional[TaskLogSyncSource]:
        """Return facts needed to synchronize logs from a mark."""

    @abstractmethod
    def apply_task_log_sync(self, plan: TaskLogSyncPlan) -> int:
        """Apply a prepared task-log projection plan."""
