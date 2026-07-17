"""Build class journal data."""

from dataclasses import dataclass
from typing import Any

from core_logic.entities.report import JournalData
from core_logic.interfaces.report_repo import IReportRepository


@dataclass(frozen=True)
class JournalRequest:
    course_id: Any
    group_id: Any
    year: Any = None
    show_debts_only: bool = False


class GetJournalUseCase:
    def __init__(self, report_repo: IReportRepository):
        self.report_repo = report_repo

    def execute(self, request: JournalRequest) -> JournalData:
        return self.report_repo.get_journal(
            course_id=request.course_id,
            group_id=request.group_id,
            year=request.year,
            show_debts_only=request.show_debts_only,
        )
