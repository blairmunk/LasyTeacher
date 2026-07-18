"""Create and update analog groups."""

from dataclasses import dataclass

from core_logic.interfaces.task_repo import ITaskRepository


@dataclass(frozen=True)
class SaveAnalogGroupRequest:
    name: str
    description: str = ''
    group_id: str = ''


@dataclass(frozen=True)
class SaveAnalogGroupResult:
    status: str
    group_id: str = ''


class CreateAnalogGroupUseCase:
    def __init__(self, task_repo: ITaskRepository):
        self.task_repo = task_repo

    def execute(self, request: SaveAnalogGroupRequest) -> SaveAnalogGroupResult:
        group_id = self.task_repo.create_analog_group(
            name=request.name,
            description=request.description,
        )
        return SaveAnalogGroupResult(status='created', group_id=group_id)


class UpdateAnalogGroupUseCase:
    def __init__(self, task_repo: ITaskRepository):
        self.task_repo = task_repo

    def execute(self, request: SaveAnalogGroupRequest) -> SaveAnalogGroupResult:
        updated = self.task_repo.update_analog_group(
            group_id=request.group_id,
            name=request.name,
            description=request.description,
        )
        if not updated:
            return SaveAnalogGroupResult(status='not_found')

        return SaveAnalogGroupResult(
            status='updated',
            group_id=request.group_id,
        )
