"""Build student performance report."""

from dataclasses import dataclass
from typing import Any

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.report import StudentPerformanceReportData
from core_logic.interfaces.report_repo import IReportRepository
from core_logic.services.report_summary_service import ReportSummaryService


@dataclass(frozen=True)
class StudentPerformanceReportRequest:
    year: AcademicYearRef | None = None
    group_id: Any = None


class GetStudentPerformanceReportUseCase:
    def __init__(
        self,
        report_repo: IReportRepository,
        summary_service: ReportSummaryService | None = None,
    ):
        self.report_repo = report_repo
        self.summary_service = summary_service or ReportSummaryService()

    def execute(
        self,
        request: StudentPerformanceReportRequest,
    ) -> StudentPerformanceReportData:
        source = self.report_repo.get_student_performance_source(
            year=request.year,
            group_id=request.group_id,
        )
        return self.summary_service.build_student_performance(source)
