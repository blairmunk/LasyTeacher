"""Build work analysis report."""

from dataclasses import dataclass

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.report_summary import WorkAnalysisReportData
from core_logic.interfaces.work_analysis_repo import IWorkAnalysisRepository
from core_logic.services.work_analysis_service import WorkAnalysisService


@dataclass(frozen=True)
class WorkAnalysisReportRequest:
    year: AcademicYearRef | None = None


class GetWorkAnalysisReportUseCase:
    def __init__(
        self,
        report_repo: IWorkAnalysisRepository,
        analysis_service: WorkAnalysisService | None = None,
    ):
        self.report_repo = report_repo
        self.analysis_service = analysis_service or WorkAnalysisService()

    def execute(
        self,
        request: WorkAnalysisReportRequest,
    ) -> WorkAnalysisReportData:
        source = self.report_repo.get_work_analysis_source(year=request.year)
        return self.analysis_service.build(source)
