"""Repository interface for student remedial planning sources."""

from abc import ABC, abstractmethod
from typing import Optional

from core_logic.entities.student import (
    RemedialWizardPreviewSource,
    StudentRemedialSource,
    TaskResultsSource,
)


class IStudentRemedialRepository(ABC):
    @abstractmethod
    def get_task_results_source_for_event(
        self,
        student_id: str,
        event_id: str,
    ) -> Optional[TaskResultsSource]:
        """Return task-level grading facts for an event."""

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
