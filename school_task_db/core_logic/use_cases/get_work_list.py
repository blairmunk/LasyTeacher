"""Build work list screen data."""

from core_logic.entities.work import WorkListData, WorkListFilters
from core_logic.interfaces.work_repo import IWorkRepository


class GetWorkListUseCase:
    def __init__(self, work_repo: IWorkRepository):
        self.work_repo = work_repo

    def execute(
        self,
        filters: WorkListFilters | None = None,
    ) -> WorkListData:
        filters = filters or WorkListFilters()
        return WorkListData(
            works=self.work_repo.get_list_works(filters),
            filters=filters,
        )
