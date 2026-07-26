"""Bulk delete variants from a work."""

from dataclasses import dataclass
from typing import List

from core_logic.entities.work import BulkDeleteVariantsResult
from core_logic.interfaces.variant_lifecycle_repo import (
    IVariantLifecycleRepository,
)


@dataclass(frozen=True)
class BulkDeleteVariantsRequest:
    work_id: str
    variant_ids: List[str]


class BulkDeleteVariantsUseCase:
    def __init__(self, variant_repo: IVariantLifecycleRepository):
        self.variant_repo = variant_repo

    def execute(
        self,
        request: BulkDeleteVariantsRequest,
    ) -> BulkDeleteVariantsResult:
        if not request.variant_ids:
            return BulkDeleteVariantsResult(status='empty_selection')

        deleted_count = self.variant_repo.bulk_delete_work_variants(
            work_id=request.work_id,
            variant_ids=request.variant_ids,
        )
        return BulkDeleteVariantsResult(
            status='deleted',
            deleted_count=deleted_count,
            remaining_count=self.variant_repo.count_work_variants(
                request.work_id,
            ),
        )
