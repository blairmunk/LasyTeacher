"""Create and update works."""

from dataclasses import dataclass, field
from typing import Sequence

from core_logic.entities.work_specification_commands import (
    CreateWorkParams,
    CreateWorkWithSpecificationParams,
    WorkContentBlockParams,
    WorkTaskSelectionParams,
)
from core_logic.interfaces.work_specification_repo import (
    IWorkSpecificationRepository,
)
from core_logic.value_objects.work_content_plan import (
    WORK_CONTENT_TEXT,
    WORK_CONTENT_THEORY,
)
from core_logic.value_objects.work_specification import WorkTaskSelectionSpec


@dataclass(frozen=True)
class SaveWorkResult:
    status: str
    work_id: str = ''
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class UpdateWorkWithSpecificationRequest:
    work: CreateWorkParams
    specs: tuple[WorkTaskSelectionParams, ...]
    content_blocks: tuple[WorkContentBlockParams, ...] = field(
        default_factory=tuple,
    )

    def __post_init__(self):
        object.__setattr__(self, 'specs', tuple(self.specs))
        object.__setattr__(self, 'content_blocks', tuple(self.content_blocks))


class CreateWorkWithSpecificationUseCase:
    def __init__(self, work_repo: IWorkSpecificationRepository):
        self.work_repo = work_repo

    def execute(
        self,
        params: CreateWorkWithSpecificationParams,
    ) -> SaveWorkResult:
        errors = validate_work_content_plan(
            params.specs,
            params.content_blocks,
        )
        if errors:
            return SaveWorkResult(status='invalid', errors=errors)

        work_id = self.work_repo.create_work_with_specification(params)
        return SaveWorkResult(status='created', work_id=work_id)


class UpdateWorkWithSpecificationUseCase:
    def __init__(self, work_repo: IWorkSpecificationRepository):
        self.work_repo = work_repo

    def execute(
        self,
        request: UpdateWorkWithSpecificationRequest,
    ) -> SaveWorkResult:
        errors = validate_work_content_plan(
            request.specs,
            request.content_blocks,
        )
        if errors:
            return SaveWorkResult(status='invalid', errors=errors)

        context = self.work_repo.get_work_update_context(
            request.work.work_id,
        )
        if context is None:
            return SaveWorkResult(status='not_found')
        mode_error = _assessment_mode_update_error(
            current_mode=context.assessment_mode,
            requested_mode=request.work.assessment_mode,
            mode_locked=context.assessment_mode_locked,
        )
        if mode_error:
            return SaveWorkResult(
                status='invalid',
                errors=(mode_error,),
            )

        updated = self.work_repo.update_work_with_specification(
            CreateWorkWithSpecificationParams(
                work=request.work,
                specs=request.specs,
                content_blocks=request.content_blocks,
            ),
        )
        if not updated:
            return SaveWorkResult(status='not_found')
        return SaveWorkResult(
            status='updated',
            work_id=request.work.work_id,
        )


def _assessment_mode_update_error(
    current_mode: str,
    requested_mode: str,
    mode_locked: bool,
) -> str:
    if current_mode == requested_mode or not mode_locked:
        return ''
    return (
        'Режим проверки уже зафиксирован вариантами или '
        'событиями. Для другого режима создайте новую работу.'
    )


def validate_work_specification_specs(
    specs: Sequence[WorkTaskSelectionParams],
) -> tuple[str, ...]:
    errors = []
    for index, spec in enumerate(specs, start=1):
        try:
            WorkTaskSelectionSpec(
                analog_group_id=spec.analog_group_id,
                count=spec.count,
                order=spec.order,
                bank_role_filter=spec.bank_role_filter,
                render_mode=spec.render_mode,
                is_assessable=spec.is_assessable,
                blank_cells_after=spec.blank_cells_after,
                blank_cells_rows=spec.blank_cells_rows,
                weight=spec.weight,
            )
        except ValueError as error:
            errors.append(f'Строка {index}: {error}')
    return tuple(errors)

def validate_work_content_blocks(
    content_blocks: Sequence[WorkContentBlockParams],
) -> tuple[str, ...]:
    errors = []
    for index, block in enumerate(content_blocks, start=1):
        if block.content_type not in (
            WORK_CONTENT_THEORY,
            WORK_CONTENT_TEXT,
        ):
            errors.append(
                f'Содержательный блок {index}: unsupported content type',
            )
            continue
        if block.order < 0:
            errors.append(
                f'Содержательный блок {index}: order must be non-negative',
            )
        if (
            block.content_type == WORK_CONTENT_THEORY
            and not block.topic_ids
        ):
            errors.append(
                f'Содержательный блок {index}: theory topics are required',
            )
        if (
            block.content_type == WORK_CONTENT_TEXT
            and not block.body.strip()
        ):
            errors.append(
                f'Содержательный блок {index}: text body is required',
            )
    return tuple(errors)


def validate_work_content_plan(
    specs: Sequence[WorkTaskSelectionParams],
    content_blocks: Sequence[WorkContentBlockParams],
) -> tuple[str, ...]:
    errors = list(validate_work_specification_specs(specs))
    errors.extend(validate_work_content_blocks(content_blocks))
    orders = [
        spec.order
        for spec in specs
    ] + [
        block.order
        for block in content_blocks
    ]
    duplicate_orders = sorted({
        order
        for order in orders
        if orders.count(order) > 1
    })
    if duplicate_orders:
        errors.append(
            'Порядок блоков должен быть уникальным: '
            + ', '.join(str(order) for order in duplicate_orders),
        )
    return tuple(errors)
