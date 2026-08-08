"""Port for work analysis report data."""

from abc import ABC, abstractmethod

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.report_summary import WorkAnalysisSource


class IWorkAnalysisRepository(ABC):
    @abstractmethod
    def get_work_analysis_source(
        self,
        year: AcademicYearRef | None,
    ) -> WorkAnalysisSource:
        """Return normalized facts for work analysis."""
