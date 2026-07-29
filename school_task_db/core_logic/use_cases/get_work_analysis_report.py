"""Build work analysis report."""

from dataclasses import dataclass

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.report import WorkAnalysisReportData
from core_logic.interfaces.report_repo import IReportRepository


@dataclass(frozen=True)
class WorkAnalysisReportRequest:
    year: AcademicYearRef | None = None


class GetWorkAnalysisReportUseCase:
    def __init__(self, report_repo: IReportRepository):
        self.report_repo = report_repo

    def execute(
        self,
        request: WorkAnalysisReportRequest,
    ) -> WorkAnalysisReportData:
        return self.report_repo.get_work_analysis_report(year=request.year)
