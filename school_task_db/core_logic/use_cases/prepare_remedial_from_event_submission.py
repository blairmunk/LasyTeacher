"""Prepare remedial-from-event POST data for creation use case."""

from dataclasses import dataclass
from datetime import date
from typing import Mapping, Sequence

from core_logic.use_cases.create_remedial_from_event import (
    RemedialFromEventRequest,
)


@dataclass(frozen=True)
class PrepareRemedialFromEventSubmissionRequest:
    event_id: str
    data: Mapping[str, Sequence[str]]


class PrepareRemedialFromEventSubmissionUseCase:
    def execute(
        self,
        request: PrepareRemedialFromEventSubmissionRequest,
    ) -> RemedialFromEventRequest:
        data = request.data
        return RemedialFromEventRequest(
            event_id=request.event_id,
            selected_student_ids=_list(data, 'selected_students'),
            work_name=_first(data, 'work_name'),
            create_event=_first(data, 'create_event') == '1',
            event_date=_optional_date(_first(data, 'event_date')),
            tasks_per_group=_bounded_int(
                _first(data, 'tasks_per_group', '1'),
                default=1,
                minimum=1,
                maximum=10,
            ),
            max_total_tasks=_bounded_int(
                _first(data, 'max_total_tasks', '10'),
                default=10,
                minimum=1,
                maximum=50,
            ),
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
        return ()
    return tuple(str(value) for value in values)


def _bounded_int(
    value: str,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return min(max(parsed, minimum), maximum)


def _optional_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None
