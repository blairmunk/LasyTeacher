"""Sync a work specification from generated variants."""

from dataclasses import dataclass

from core_logic.entities.work import SyncWorkAnalogGroupsResult
from core_logic.interfaces.work_repo import IWorkRepository


@dataclass(frozen=True)
class SyncWorkAnalogGroupsRequest:
    work_id: str


class SyncWorkAnalogGroupsUseCase:
    def __init__(self, work_repo: IWorkRepository):
        self.work_repo = work_repo

    def execute(
        self,
        request: SyncWorkAnalogGroupsRequest,
    ) -> SyncWorkAnalogGroupsResult:
        if self.work_repo.get_work_name(request.work_id) is None:
            return SyncWorkAnalogGroupsResult(
                created_count=0,
                status='not_found',
            )

        return SyncWorkAnalogGroupsResult(
            created_count=self.work_repo.sync_analog_groups_from_variants(
                request.work_id,
            )
        )
