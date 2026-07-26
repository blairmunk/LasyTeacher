"""Delete or detach a variant."""

from dataclasses import dataclass

from core_logic.entities.work import DeleteVariantResult
from core_logic.interfaces.variant_lifecycle_repo import (
    IVariantLifecycleRepository,
)


@dataclass(frozen=True)
class DeleteVariantRequest:
    variant_id: str
    action: str = 'delete'


class DeleteVariantUseCase:
    def __init__(self, variant_repo: IVariantLifecycleRepository):
        self.variant_repo = variant_repo

    def execute(self, request: DeleteVariantRequest) -> DeleteVariantResult:
        info = self.variant_repo.get_variant_delete_info(request.variant_id)
        if info is None:
            return DeleteVariantResult(status='not_found')

        if request.action == 'detach':
            return DeleteVariantResult(
                status='detached',
                variant_short_id=self.variant_repo.detach_variant_from_work(
                    request.variant_id,
                ),
            )

        if info.has_participations:
            return DeleteVariantResult(
                status='blocked_has_participations',
                participation_count=info.participation_count,
            )

        return DeleteVariantResult(
            status='deleted',
            redirect_work_id=self.variant_repo.delete_variant(request.variant_id),
        )
