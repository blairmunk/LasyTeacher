"""Build journal selection data."""

from dataclasses import dataclass
from typing import Any

from core_logic.entities.report import JournalSelectData
from core_logic.interfaces.report_repo import IReportRepository


@dataclass(frozen=True)
class JournalSelectRequest:
    year: Any = None


class GetJournalSelectUseCase:
    def __init__(self, report_repo: IReportRepository):
        self.report_repo = report_repo

    def execute(self, request: JournalSelectRequest) -> JournalSelectData:
        return self.report_repo.get_journal_select(year=request.year)
