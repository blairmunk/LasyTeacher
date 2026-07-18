"""Create a work specification from selected analog groups."""

from dataclasses import dataclass
from typing import List

from core_logic.interfaces.task_repo import ITaskRepository
from core_logic.interfaces.work_repo import (
    CreateWorkAnalogGroupParams,
    CreateWorkParams,
    IWorkRepository,
)


@dataclass(frozen=True)
class GroupSpecRequest:
    id: str
    order: int = 0
    count: int = 1
    weight: int = 1


@dataclass(frozen=True)
class CreateWorkFromGroupsRequest:
    groups: List[GroupSpecRequest]
    work_name: str
    work_type: str = 'test'
    max_score: int = 0
    auto_generate: bool = False
    variant_count: int = 2


@dataclass(frozen=True)
class CreateWorkFromGroupsResult:
    status: str
    work_id: str = ''
    message: str = ''
    warning: str = ''
    variants_generated: int = 0

    @property
    def success(self) -> bool:
        return self.status == 'created'


class CreateWorkFromGroupsUseCase:
    def __init__(
        self,
        task_repo: ITaskRepository,
        work_repo: IWorkRepository,
    ):
        self.task_repo = task_repo
        self.work_repo = work_repo

    def execute(
        self,
        request: CreateWorkFromGroupsRequest,
    ) -> CreateWorkFromGroupsResult:
        if not request.groups:
            return CreateWorkFromGroupsResult(
                status='empty_groups',
                message='Не выбрано ни одной группы',
            )

        work_name = request.work_name.strip()
        if not work_name:
            return CreateWorkFromGroupsResult(
                status='empty_name',
                message='Название работы не указано',
            )

        group_ids = {group.id for group in request.groups}
        if self.task_repo.count_existing_group_ids(group_ids) != len(group_ids):
            return CreateWorkFromGroupsResult(
                status='missing_groups',
                message='Некоторые группы не найдены',
            )

        work_id = self.work_repo.create_work(
            CreateWorkParams(
                name=work_name,
                work_type=request.work_type,
                max_score=max(0, int(request.max_score)),
            )
        )

        for position, group in enumerate(request.groups, 1):
            weight = group.weight
            if weight <= 0:
                weight = self.task_repo.get_first_task_difficulty_for_group(group.id)

            self.work_repo.create_work_analog_group(
                CreateWorkAnalogGroupParams(
                    work_id=work_id,
                    analog_group_id=group.id,
                    order=group.order or position,
                    count=group.count,
                    weight=max(1, int(weight)),
                )
            )

        message = (
            f'Создана работа «{work_name}» '
            f'со спецификацией из {len(request.groups)} групп'
        )
        warning = ''
        variants_generated = 0
        if request.auto_generate:
            try:
                variants_generated = min(int(request.variant_count), 10)
                self.work_repo.compose_variants(work_id, variants_generated)
                message += f' и {variants_generated} вариантами'
            except Exception as error:
                warning = (
                    'Работа создана, но генерация вариантов не удалась: '
                    f'{error}'
                )

        return CreateWorkFromGroupsResult(
            status='created',
            work_id=work_id,
            message=message,
            warning=warning,
            variants_generated=variants_generated,
        )
