"""Build variant detail screen data."""

from core_logic.entities.work import VariantDetailData
from core_logic.interfaces.work_repo import IWorkRepository


class GetVariantDetailUseCase:
    def __init__(self, work_repo: IWorkRepository):
        self.work_repo = work_repo

    def execute(self, variant_id: str) -> VariantDetailData:
        variant = self.work_repo.get_variant_detail(variant_id)
        if variant is None:
            return VariantDetailData()

        return VariantDetailData(
            variant=variant,
            variant_tasks=self.work_repo.get_variant_detail_tasks(variant_id),
            total_max_points=self.work_repo.get_variant_total_max_points(
                variant_id,
            ),
        )
