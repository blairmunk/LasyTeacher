"""Build orphan variant list screen data."""

from core_logic.entities.work import OrphanVariantListData
from core_logic.interfaces.work_repo import IWorkRepository


class GetOrphanVariantListUseCase:
    def __init__(self, work_repo: IWorkRepository):
        self.work_repo = work_repo

    def execute(self) -> OrphanVariantListData:
        return OrphanVariantListData(
            variants=self.work_repo.get_orphan_variants(),
            total_orphans=self.work_repo.count_orphan_variants(),
        )
