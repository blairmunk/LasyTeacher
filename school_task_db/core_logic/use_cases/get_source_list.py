"""Build source list screen data."""

from core_logic.entities.task import SourceListData
from core_logic.interfaces.source_repo import ISourceRepository


class GetSourceListUseCase:
    def __init__(self, source_repo: ISourceRepository):
        self.source_repo = source_repo

    def execute(self) -> SourceListData:
        return SourceListData(
            sources=self.source_repo.get_source_list_sources(),
        )
