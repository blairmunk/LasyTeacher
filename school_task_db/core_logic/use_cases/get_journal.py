"""Build class journal data."""

from dataclasses import dataclass
from typing import Any

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.journal import JournalData
from core_logic.interfaces.journal_repo import IJournalRepository
from core_logic.services.journal_service import JournalService


@dataclass(frozen=True)
class JournalRequest:
    course_id: Any
    group_id: Any
    year: AcademicYearRef | None = None
    show_debts_only: bool = False


class GetJournalUseCase:
    def __init__(
        self,
        report_repo: IJournalRepository,
        journal_service: JournalService | None = None,
    ):
        self.report_repo = report_repo
        self.journal_service = journal_service or JournalService()

    def execute(self, request: JournalRequest) -> JournalData:
        source = self.report_repo.get_journal_source(
            course_id=request.course_id,
            group_id=request.group_id,
            year=request.year,
        )
        return self.journal_service.build(
            source,
            show_debts_only=request.show_debts_only,
        )
