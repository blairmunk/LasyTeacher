"""Prepare individual student remedial POST data."""

from dataclasses import dataclass
from typing import Mapping, Sequence

from core_logic.use_cases.create_student_remedial_variant import (
    CreateStudentRemedialVariantRequest,
)


@dataclass(frozen=True)
class PrepareStudentRemedialSubmissionRequest:
    student_id: str
    data: Mapping[str, Sequence[str]]


class PrepareStudentRemedialSubmissionUseCase:
    def execute(
        self,
        request: PrepareStudentRemedialSubmissionRequest,
    ) -> CreateStudentRemedialVariantRequest:
        return CreateStudentRemedialVariantRequest(
            student_id=request.student_id,
            max_tasks=_int(_first(request.data, 'max_tasks', '10'), default=10),
            selected_group_ids=_list(request.data, 'groups'),
        )


def _first(
    data: Mapping[str, Sequence[str]],
    key: str,
    default: str = '',
) -> str:
    values = data.get(key)
    if not values:
        return default
    return str(values[0])


def _list(data: Mapping[str, Sequence[str]], key: str):
    values = data.get(key)
    if not values:
        return []
    return [str(value) for value in values]


def _int(value: str, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
