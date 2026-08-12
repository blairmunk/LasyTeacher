"""Bulk delete variants from a work."""

from dataclasses import dataclass
from typing import List

from core_logic.entities.work import BulkDeleteVariantsResult
from core_logic.interfaces.variant_lifecycle_command_repo import (
    IVariantLifecycleCommandRepository,
)
from core_logic.interfaces.variant_lifecycle_query_repo import (
    IVariantLifecycleQueryRepository,
)


@dataclass(frozen=True)
class BulkDeleteVariantsRequest:
    work_id: str
    variant_ids: List[str]


class BulkDeleteVariantsUseCase:
    def __init__(
        self,
        variant_query_repo: IVariantLifecycleQueryRepository,
        variant_command_repo: IVariantLifecycleCommandRepository,
    ):
        self.variant_query_repo = variant_query_repo
        self.variant_command_repo = variant_command_repo

    def execute(
        self,
        request: BulkDeleteVariantsRequest,
    ) -> BulkDeleteVariantsResult:
        if not request.variant_ids:
            return BulkDeleteVariantsResult(status='empty_selection')

        deleted_count = self.variant_command_repo.bulk_delete_work_variants(
            work_id=request.work_id,
            variant_ids=request.variant_ids,
        )
        return BulkDeleteVariantsResult(
            status='deleted',
            deleted_count=deleted_count,
            remaining_count=self.variant_query_repo.count_work_variants(
                request.work_id,
            ),
        )
