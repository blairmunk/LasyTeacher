"""Build student performance report."""

from dataclasses import dataclass
from typing import Any

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.report_summary import StudentPerformanceReportData
from core_logic.interfaces.report_summary_repo import IReportSummaryRepository
from core_logic.services.student_performance_service import (
    StudentPerformanceService,
)


@dataclass(frozen=True)
class StudentPerformanceReportRequest:
    year: AcademicYearRef | None = None
    group_id: Any = None


class GetStudentPerformanceReportUseCase:
    def __init__(
        self,
        report_repo: IReportSummaryRepository,
        performance_service: StudentPerformanceService | None = None,
    ):
        self.report_repo = report_repo
        self.performance_service = (
            performance_service or StudentPerformanceService()
        )

    def execute(
        self,
        request: StudentPerformanceReportRequest,
    ) -> StudentPerformanceReportData:
        source = self.report_repo.get_student_performance_source(
            year=request.year,
            group_id=request.group_id,
        )
        return self.performance_service.build(source)
