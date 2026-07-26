"""Build variant list screen data."""

from core_logic.entities.work import VariantListData
from core_logic.interfaces.variant_read_repo import IVariantReadRepository


class GetVariantListUseCase:
    def __init__(self, variant_repo: IVariantReadRepository):
        self.variant_repo = variant_repo

    def execute(self) -> VariantListData:
        return VariantListData(
            variants=self.variant_repo.get_list_variants(),
        )
