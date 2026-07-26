"""Build orphan variant list screen data."""

from core_logic.entities.work import OrphanVariantListData
from core_logic.interfaces.orphan_variant_repo import IOrphanVariantRepository


class GetOrphanVariantListUseCase:
    def __init__(self, orphan_variant_repo: IOrphanVariantRepository):
        self.orphan_variant_repo = orphan_variant_repo

    def execute(self) -> OrphanVariantListData:
        return OrphanVariantListData(
            variants=self.orphan_variant_repo.get_orphan_variants(),
            total_orphans=self.orphan_variant_repo.count_orphan_variants(),
        )
