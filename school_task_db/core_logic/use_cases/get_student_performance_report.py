"""Build student performance report."""

from dataclasses import dataclass
from typing import Any

from core_logic.entities.report import StudentPerformanceReportData
from core_logic.interfaces.report_repo import IReportRepository


@dataclass(frozen=True)
class StudentPerformanceReportRequest:
    year: Any = None
    group_id: Any = None


class GetStudentPerformanceReportUseCase:
    def __init__(self, report_repo: IReportRepository):
        self.report_repo = report_repo

    def execute(
        self,
        request: StudentPerformanceReportRequest,
    ) -> StudentPerformanceReportData:
        return self.report_repo.get_student_performance_report(
            year=request.year,
            group_id=request.group_id,
        )
