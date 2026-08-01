"""Build class journal data."""

from dataclasses import dataclass
from typing import Any

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.report import JournalData
from core_logic.interfaces.report_repo import IReportRepository
from core_logic.services.report_summary_service import ReportSummaryService


@dataclass(frozen=True)
class JournalRequest:
    course_id: Any
    group_id: Any
    year: AcademicYearRef | None = None
    show_debts_only: bool = False


class GetJournalUseCase:
    def __init__(
        self,
        report_repo: IReportRepository,
        summary_service: ReportSummaryService | None = None,
    ):
        self.report_repo = report_repo
        self.summary_service = summary_service or ReportSummaryService()

    def execute(self, request: JournalRequest) -> JournalData:
        source = self.report_repo.get_journal_source(
            course_id=request.course_id,
            group_id=request.group_id,
            year=request.year,
        )
        return self.summary_service.build_journal(
            source,
            show_debts_only=request.show_debts_only,
        )
