"""Build work analysis report."""

from dataclasses import dataclass

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.report_summary import WorkAnalysisReportData
from core_logic.interfaces.report_summary_repo import IReportSummaryRepository
from core_logic.services.report_summary_service import ReportSummaryService


@dataclass(frozen=True)
class WorkAnalysisReportRequest:
    year: AcademicYearRef | None = None


class GetWorkAnalysisReportUseCase:
    def __init__(
        self,
        report_repo: IReportSummaryRepository,
        summary_service: ReportSummaryService | None = None,
    ):
        self.report_repo = report_repo
        self.summary_service = summary_service or ReportSummaryService()

    def execute(
        self,
        request: WorkAnalysisReportRequest,
    ) -> WorkAnalysisReportData:
        source = self.report_repo.get_work_analysis_source(year=request.year)
        return self.summary_service.build_work_analysis(source)
