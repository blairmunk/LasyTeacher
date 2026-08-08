"""Assign variants to event participations."""

from dataclasses import dataclass
from typing import Mapping

from core_logic.interfaces.event_repo import IEventRepository


@dataclass(frozen=True)
class AssignEventVariantsRequest:
    event_id: str
    assignments: Mapping[str, str]


@dataclass(frozen=True)
class AssignEventVariantsResult:
    assigned_count: int
    status: str = 'assigned'


class AssignEventVariantsUseCase:
    def __init__(self, event_repo: IEventRepository):
        self.event_repo = event_repo

    def execute(
        self,
        request: AssignEventVariantsRequest,
    ) -> AssignEventVariantsResult:
        event = self.event_repo.get_by_id(request.event_id)
        if event is None:
            return AssignEventVariantsResult(
                assigned_count=0,
                status='not_found',
            )
        if not event.requires_variants:
            return AssignEventVariantsResult(
                assigned_count=0,
                status='variants_not_required',
            )
        assignments = {
            str(participation_id): str(variant_id)
            for participation_id, variant_id in request.assignments.items()
            if participation_id and variant_id
        }
        return AssignEventVariantsResult(
            assigned_count=self.event_repo.assign_variants(
                event_id=request.event_id,
                assignments=assignments,
            )
        )
