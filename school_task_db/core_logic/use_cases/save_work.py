"""Create and update works."""

from dataclasses import dataclass
from typing import List

from core_logic.interfaces.work_repo import (
    CreateWorkAnalogGroupParams,
    CreateWorkParams,
    IWorkRepository,
)


@dataclass(frozen=True)
class SaveWorkResult:
    status: str
    work_id: str = ''


@dataclass(frozen=True)
class SaveWorkSpecificationRequest:
    work_id: str
    specs: List[CreateWorkAnalogGroupParams]


@dataclass(frozen=True)
class SaveWorkSpecificationResult:
    status: str
    saved_count: int = 0


class CreateWorkUseCase:
    def __init__(self, work_repo: IWorkRepository):
        self.work_repo = work_repo

    def execute(self, params: CreateWorkParams) -> SaveWorkResult:
        work_id = self.work_repo.create_work(params)
        return SaveWorkResult(status='created', work_id=work_id)


class UpdateWorkUseCase:
    def __init__(self, work_repo: IWorkRepository):
        self.work_repo = work_repo

    def execute(self, params: CreateWorkParams) -> SaveWorkResult:
        updated = self.work_repo.update_work(params)
        if not updated:
            return SaveWorkResult(status='not_found')

        return SaveWorkResult(status='updated', work_id=params.work_id)


class SaveWorkSpecificationUseCase:
    def __init__(self, work_repo: IWorkRepository):
        self.work_repo = work_repo

    def execute(
        self,
        request: SaveWorkSpecificationRequest,
    ) -> SaveWorkSpecificationResult:
        updated = self.work_repo.replace_work_analog_groups(
            work_id=request.work_id,
            specs=request.specs,
        )
        if not updated:
            return SaveWorkSpecificationResult(status='not_found')

        return SaveWorkSpecificationResult(
            status='saved',
            saved_count=len(request.specs),
        )
