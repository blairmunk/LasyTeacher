"""Build import screen data."""

from dataclasses import dataclass

from core_logic.entities.core import ImportHistoryData, ImportPageData
from core_logic.interfaces.core_repo import ICoreRepository


@dataclass(frozen=True)
class ImportPageRequest:
    recent_limit: int = 5


class GetImportPageUseCase:
    def __init__(self, core_repo: ICoreRepository):
        self.core_repo = core_repo

    def execute(self, request: ImportPageRequest) -> ImportPageData:
        return ImportPageData(
            recent_imports=self.core_repo.get_recent_import_logs(
                limit=request.recent_limit,
            ),
        )


class GetImportHistoryUseCase:
    def __init__(self, core_repo: ICoreRepository):
        self.core_repo = core_repo

    def execute(self) -> ImportHistoryData:
        return ImportHistoryData(imports=self.core_repo.get_import_logs())
