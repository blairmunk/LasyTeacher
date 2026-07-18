"""Prepare remedial-from-event POST data for creation use case."""

from dataclasses import dataclass
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


def _list(data: Mapping[str, Sequence[str]], key: str):
    values = data.get(key)
    if not values:
        return []
    return [str(value) for value in values]
