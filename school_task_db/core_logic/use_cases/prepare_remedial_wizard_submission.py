"""Prepare remedial wizard POST data for use cases."""

from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence

from core_logic.use_cases.create_remedial_wizard_work import (
    CreateRemedialWizardWorkRequest,
)
from core_logic.use_cases.get_remedial_wizard_preview import (
    RemedialWizardPreviewRequest,
)


@dataclass(frozen=True)
class PrepareRemedialWizardSubmissionRequest:
    data: Mapping[str, Sequence[str]]


class PrepareRemedialWizardPreviewSubmissionUseCase:
    def execute(
        self,
        request: PrepareRemedialWizardSubmissionRequest,
    ) -> RemedialWizardPreviewRequest:
        data = request.data
        return RemedialWizardPreviewRequest(
            group_id=_first(data, 'group_id'),
            threshold=_int(_first(data, 'threshold', '70'), default=70),
            limit_type=_first(data, 'limit_type', 'tasks'),
            limit_value=_int(_first(data, 'limit_value', '10'), default=10),
            work_name=_first(data, 'work_name', 'Работа над ошибками'),
        )


class PrepareRemedialWizardCreateSubmissionUseCase:
    def execute(
        self,
        request: PrepareRemedialWizardSubmissionRequest,
    ) -> CreateRemedialWizardWorkRequest:
        data = request.data
        selected_student_ids = _list(data, 'selected_students')

        return CreateRemedialWizardWorkRequest(
            group_id=_first(data, 'group_id'),
            selected_student_ids=selected_student_ids,
            student_task_ids=_student_task_ids(data, selected_student_ids),
            work_name=_first(data, 'work_name', 'Работа над ошибками'),
            create_event=_first(data, 'create_event') == '1',
            event_date=_first(data, 'event_date'),
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


def _list(data: Mapping[str, Sequence[str]], key: str) -> List[str]:
    values = data.get(key)
    if not values:
        return []
    return [str(value) for value in values]


def _int(value: str, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _student_task_ids(
    data: Mapping[str, Sequence[str]],
    selected_student_ids: List[str],
) -> Dict[str, List[str]]:
    student_tasks = {}
    for student_id in selected_student_ids:
        task_ids_raw = _first(data, f'task_ids_{student_id}')
        task_ids = [
            task_id.strip()
            for task_id in task_ids_raw.split(',')
            if task_id.strip()
        ]
        if task_ids:
            student_tasks[student_id] = task_ids
    return student_tasks
