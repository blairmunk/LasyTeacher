"""Create a work specification from selected analog groups."""

from dataclasses import dataclass
from typing import Any, Mapping, List

from core_logic.interfaces.task_repo import ITaskRepository
from core_logic.interfaces.work_repo import (
    CreateWorkAnalogGroupParams,
    CreateWorkParams,
    IWorkRepository,
)
from core_logic.value_objects.task_print_settings import (
    DEFAULT_BLANK_CELLS_ROWS,
    TASK_BANK_ROLE_ANY,
    TASK_RENDER_MODE_TASK_ONLY,
)
from core_logic.value_objects.variant_print_plan import (
    WorkTaskRoleSpec,
)


@dataclass(frozen=True)
class GroupSpecRequest:
    id: str
    order: int = 0
    count: int = 1
    weight: int = 1
    bank_role_filter: str = TASK_BANK_ROLE_ANY
    render_mode: str = TASK_RENDER_MODE_TASK_ONLY
    is_assessable: bool = True
    blank_cells_after: bool = False
    blank_cells_rows: int = DEFAULT_BLANK_CELLS_ROWS


@dataclass(frozen=True)
class CreateWorkFromGroupsRequest:
    groups: List[GroupSpecRequest]
    work_name: str
    work_type: str = 'test'
    max_score: int = 0
    auto_generate: bool = False
    variant_count: int = 2


@dataclass(frozen=True)
class PrepareCreateWorkFromGroupsSubmissionRequest:
    body: Any


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


class PrepareCreateWorkFromGroupsSubmissionUseCase:
    def execute(
        self,
        request: PrepareCreateWorkFromGroupsSubmissionRequest,
    ) -> CreateWorkFromGroupsRequest:
        body = request.body
        if not isinstance(body, Mapping):
            body = {}
        groups_data = body.get('groups', [])
        if not isinstance(groups_data, list):
            groups_data = []

        return CreateWorkFromGroupsRequest(
            groups=[
                GroupSpecRequest(
                    id=str(group_data.get('id', '')),
                    order=_int_or_default(group_data.get('order'), index),
                    count=_int_or_default(group_data.get('count'), 1),
                    weight=_int_or_default(group_data.get('weight'), 1),
                    bank_role_filter=group_data.get(
                        'bank_role_filter',
                        TASK_BANK_ROLE_ANY,
                    ),
                    render_mode=group_data.get(
                        'render_mode',
                        TASK_RENDER_MODE_TASK_ONLY,
                    ),
                    is_assessable=_bool_or_default(
                        group_data.get('is_assessable'),
                        True,
                    ),
                    blank_cells_after=_bool_or_default(
                        group_data.get('blank_cells_after'),
                        False,
                    ),
                    blank_cells_rows=_int_or_default(
                        group_data.get('blank_cells_rows'),
                        DEFAULT_BLANK_CELLS_ROWS,
                    ),
                )
                for index, group_data in enumerate(groups_data, 1)
                if isinstance(group_data, Mapping)
            ],
            work_name=str(body.get('work_name', '')),
            work_type=str(body.get('work_type', 'test')),
            max_score=_int_or_default(body.get('max_score'), 0),
            auto_generate=_bool_or_default(body.get('auto_generate'), False),
            variant_count=_int_or_default(body.get('variant_count'), 2),
        )


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

        for group in request.groups:
            try:
                WorkTaskRoleSpec(
                    analog_group_id=group.id,
                    count=group.count,
                    order=group.order,
                    bank_role_filter=group.bank_role_filter,
                    render_mode=group.render_mode,
                    is_assessable=group.is_assessable,
                    blank_cells_after=group.blank_cells_after,
                    blank_cells_rows=group.blank_cells_rows,
                    weight=group.weight,
                )
            except ValueError as error:
                return CreateWorkFromGroupsResult(
                    status='invalid_group_spec',
                    message=str(error),
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
                    bank_role_filter=group.bank_role_filter,
                    render_mode=group.render_mode,
                    is_assessable=group.is_assessable,
                    blank_cells_after=group.blank_cells_after,
                    blank_cells_rows=group.blank_cells_rows,
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


def _int_or_default(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _bool_or_default(value, default):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {'1', 'true', 'yes', 'on'}:
            return True
        if normalized in {'0', 'false', 'no', 'off', ''}:
            return False
    if value is None:
        return default
    return bool(value)
