"""Write port for persisting a checked event participation."""

from abc import ABC, abstractmethod

from core_logic.entities.event import ParticipationGradingContext
from core_logic.entities.grading import (
    GradeParticipationParams,
    GradeParticipationResult,
)


class IParticipationGradingRepository(ABC):
    @abstractmethod
    def get_participation_grading_context(
        self,
        participation_id: str,
    ) -> ParticipationGradingContext:
        """Lock and return the state needed for grading decisions."""

    @abstractmethod
    def save_participation_grade(
        self,
        params: GradeParticipationParams,
    ) -> GradeParticipationResult:
        """Persist a mark, participation state and optional event status."""
