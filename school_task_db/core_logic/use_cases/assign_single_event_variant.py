"""Assign one variant to one event participation."""

from dataclasses import dataclass
from typing import Optional

from core_logic.entities.event import EventVariantAssignmentResult
from core_logic.interfaces.event_repo import IEventRepository


@dataclass(frozen=True)
class AssignSingleEventVariantRequest:
    event_id: str
    participation_id: Optional[str]
    variant_id: Optional[str]


@dataclass(frozen=True)
class AssignSingleEventVariantResult:
    success: bool
    assignment: Optional[EventVariantAssignmentResult] = None
    error: str = ''


class AssignSingleEventVariantUseCase:
    def __init__(self, event_repo: IEventRepository):
        self.event_repo = event_repo

    def execute(
        self,
        request: AssignSingleEventVariantRequest,
    ) -> AssignSingleEventVariantResult:
        if not request.participation_id or not request.variant_id:
            return AssignSingleEventVariantResult(
                success=False,
                error='missing_selection',
            )

        return AssignSingleEventVariantResult(
            success=True,
            assignment=self.event_repo.assign_variant(
                event_id=request.event_id,
                participation_id=request.participation_id,
                variant_id=request.variant_id,
            ),
        )
