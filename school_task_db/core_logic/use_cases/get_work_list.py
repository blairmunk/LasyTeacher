"""Build work list screen data."""

from core_logic.entities.work import WorkListData, WorkListFilters
from core_logic.interfaces.work_read_repo import IWorkReadRepository


class GetWorkListUseCase:
    def __init__(self, work_read_repo: IWorkReadRepository):
        self.work_read_repo = work_read_repo

    def execute(
        self,
        filters: WorkListFilters | None = None,
    ) -> WorkListData:
        filters = filters or WorkListFilters()
        return WorkListData(
            works=self.work_read_repo.get_list_works(filters),
            filters=filters,
        )
