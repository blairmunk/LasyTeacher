"""Prepare event action POST data for mutation use cases."""

from dataclasses import dataclass
from typing import Mapping, Sequence

from core_logic.use_cases.assign_single_event_variant import (
    AssignSingleEventVariantRequest,
)
from core_logic.use_cases.change_event_status import ChangeEventStatusRequest


@dataclass(frozen=True)
class PrepareEventActionSubmissionRequest:
    event_id: str
    data: Mapping[str, Sequence[str]]


class PrepareAssignSingleVariantSubmissionUseCase:
    def execute(
        self,
        request: PrepareEventActionSubmissionRequest,
    ) -> AssignSingleEventVariantRequest:
        return AssignSingleEventVariantRequest(
            event_id=request.event_id,
            participation_id=_first(request.data, 'participation_id'),
            variant_id=_first(request.data, 'variant_id'),
        )


class PrepareChangeEventStatusSubmissionUseCase:
    def execute(
        self,
        request: PrepareEventActionSubmissionRequest,
    ) -> ChangeEventStatusRequest:
        return ChangeEventStatusRequest(
            event_id=request.event_id,
            new_status=_first(request.data, 'new_status'),
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
