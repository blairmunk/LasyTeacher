"""Build variant list screen data."""

from core_logic.entities.work import VariantListData
from core_logic.interfaces.work_repo import IWorkRepository


class GetVariantListUseCase:
    def __init__(self, work_repo: IWorkRepository):
        self.work_repo = work_repo

    def execute(self) -> VariantListData:
        return VariantListData(
            variants=self.work_repo.get_list_variants(),
        )
