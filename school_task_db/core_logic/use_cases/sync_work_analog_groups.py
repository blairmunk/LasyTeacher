"""Sync a work specification from generated variants."""

from dataclasses import dataclass

from core_logic.entities.work import SyncWorkAnalogGroupsResult
from core_logic.interfaces.work_variant_generation_repo import (
    IWorkVariantGenerationRepository,
)
from core_logic.interfaces.transaction_manager import ITransactionManager
from core_logic.services.work_spec_sync_service import WorkSpecSyncService


MAX_SYNC_ATTEMPTS = 3


@dataclass(frozen=True)
class SyncWorkAnalogGroupsRequest:
    work_id: str


class SyncWorkAnalogGroupsUseCase:
    def __init__(
        self,
        work_repo: IWorkVariantGenerationRepository,
        transaction_manager: ITransactionManager,
        sync_service=None,
    ):
        self.work_repo = work_repo
        self.transaction_manager = transaction_manager
        self.sync_service = sync_service or WorkSpecSyncService()

    def execute(
        self,
        request: SyncWorkAnalogGroupsRequest,
    ) -> SyncWorkAnalogGroupsResult:
        for _attempt in range(MAX_SYNC_ATTEMPTS):
            with self.transaction_manager.atomic():
                source = self.work_repo.get_work_spec_sync_source(
                    request.work_id,
                )
                if source is None:
                    return SyncWorkAnalogGroupsResult(
                        created_count=0,
                        status='not_found',
                    )

                plan = self.sync_service.build_plan(source.variant_group_ids)
                save_result = self.work_repo.save_work_spec_sync_plan(
                    work_id=request.work_id,
                    expected_variant_counter=source.variant_counter,
                    plan=plan,
                )
            if save_result.status == 'saved':
                return SyncWorkAnalogGroupsResult(
                    created_count=save_result.created_count,
                )
            if save_result.status == 'not_found':
                return SyncWorkAnalogGroupsResult(
                    created_count=0,
                    status='not_found',
                )
            if save_result.status != 'conflict':
                raise ValueError(
                    'Unsupported work specification sync status: '
                    f'{save_result.status}',
                )

        return SyncWorkAnalogGroupsResult(
            created_count=0,
            status='conflict',
        )
