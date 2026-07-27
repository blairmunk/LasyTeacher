"""Create and update works."""

from dataclasses import dataclass
from typing import List

from core_logic.interfaces.work_repo import (
    CreateWorkParams,
    CreateWorkWithSpecificationParams,
    IWorkRepository,
    WorkTaskSelectionParams,
)
from core_logic.value_objects.work_specification import WorkTaskSelectionSpec


@dataclass(frozen=True)
class SaveWorkResult:
    status: str
    work_id: str = ''
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class SaveWorkSpecificationRequest:
    work_id: str
    specs: List[WorkTaskSelectionParams]


@dataclass(frozen=True)
class SaveWorkSpecificationResult:
    status: str
    saved_count: int = 0
    errors: tuple[str, ...] = ()


class CreateWorkWithSpecificationUseCase:
    def __init__(self, work_repo: IWorkRepository):
        self.work_repo = work_repo

    def execute(
        self,
        params: CreateWorkWithSpecificationParams,
    ) -> SaveWorkResult:
        errors = validate_work_specification_specs(params.specs)
        if errors:
            return SaveWorkResult(status='invalid', errors=errors)

        work_id = self.work_repo.create_work_with_specification(params)
        return SaveWorkResult(status='created', work_id=work_id)


class UpdateWorkUseCase:
    def __init__(self, work_repo: IWorkRepository):
        self.work_repo = work_repo

    def execute(self, params: CreateWorkParams) -> SaveWorkResult:
        updated = self.work_repo.update_work(params)
        if not updated:
            return SaveWorkResult(status='not_found')

        return SaveWorkResult(status='updated', work_id=params.work_id)


def validate_work_specification_specs(
    specs: List[WorkTaskSelectionParams],
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


class SaveWorkSpecificationUseCase:
    def __init__(self, work_repo: IWorkRepository):
        self.work_repo = work_repo

    def execute(
        self,
        request: SaveWorkSpecificationRequest,
    ) -> SaveWorkSpecificationResult:
        errors = validate_work_specification_specs(request.specs)
        if errors:
            return SaveWorkSpecificationResult(
                status='invalid',
                errors=errors,
            )

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
