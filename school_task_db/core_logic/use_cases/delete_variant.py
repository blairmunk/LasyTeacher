"""Delete or detach a variant."""

from dataclasses import dataclass

from core_logic.entities.work import DeleteVariantResult
from core_logic.interfaces.variant_lifecycle_command_repo import (
    IVariantLifecycleCommandRepository,
)
from core_logic.interfaces.variant_lifecycle_query_repo import (
    IVariantLifecycleQueryRepository,
)


@dataclass(frozen=True)
class DeleteVariantRequest:
    variant_id: str
    action: str = 'delete'


class DeleteVariantUseCase:
    def __init__(
        self,
        variant_query_repo: IVariantLifecycleQueryRepository,
        variant_command_repo: IVariantLifecycleCommandRepository,
    ):
        self.variant_query_repo = variant_query_repo
        self.variant_command_repo = variant_command_repo

    def execute(self, request: DeleteVariantRequest) -> DeleteVariantResult:
        info = self.variant_query_repo.get_variant_delete_info(
            request.variant_id,
        )
        if info is None:
            return DeleteVariantResult(status='not_found')

        if request.action == 'detach':
            return DeleteVariantResult(
                status='detached',
                variant_short_id=(
                    self.variant_command_repo.detach_variant_from_work(
                        request.variant_id,
                    )
                ),
            )

        if info.has_participations:
            return DeleteVariantResult(
                status='blocked_has_participations',
                participation_count=info.participation_count,
            )

        outcome = self.variant_command_repo.delete_variant_if_unreferenced(
            request.variant_id,
        )
        if outcome.status == 'not_found':
            return DeleteVariantResult(status='not_found')
        if outcome.status == 'blocked_has_participations':
            return DeleteVariantResult(
                status='blocked_has_participations',
                participation_count=outcome.participation_count,
            )
        return DeleteVariantResult(
            status='deleted',
            redirect_work_id=outcome.work_id,
        )
