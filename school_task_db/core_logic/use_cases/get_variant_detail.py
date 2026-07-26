"""Build variant detail screen data."""

from core_logic.entities.work import VariantDetailData
from core_logic.interfaces.variant_read_repo import IVariantReadRepository


class GetVariantDetailUseCase:
    def __init__(self, variant_repo: IVariantReadRepository):
        self.variant_repo = variant_repo

    def execute(self, variant_id: str) -> VariantDetailData:
        variant = self.variant_repo.get_variant_detail(variant_id)
        if variant is None:
            return VariantDetailData()

        return VariantDetailData(
            variant=variant,
            variant_tasks=self.variant_repo.get_variant_detail_tasks(variant_id),
            total_max_points=self.variant_repo.get_variant_total_max_points(
                variant_id,
            ),
        )
