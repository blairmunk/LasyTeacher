"""Create and update works."""

from dataclasses import dataclass

from core_logic.interfaces.work_repo import CreateWorkParams, IWorkRepository


@dataclass(frozen=True)
class SaveWorkResult:
    status: str
    work_id: str = ''


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
