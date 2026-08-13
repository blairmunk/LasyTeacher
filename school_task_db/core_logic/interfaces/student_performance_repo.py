"""Port for student performance report data."""

from abc import ABC, abstractmethod
from typing import Optional

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.report_summary import StudentPerformanceSource


class IStudentPerformanceRepository(ABC):
    @abstractmethod
    def get_student_performance_source(
        self,
        year: AcademicYearRef | None,
        group_id: Optional[str],
    ) -> StudentPerformanceSource:
        """Return normalized facts for the student performance report."""
