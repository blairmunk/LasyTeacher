"""Event repository interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from core_logic.entities.event import (
    EventParticipationRow,
    EventEntity,
    EventParticipationRef,
    EventVariantAssignmentResult,
    EventVariantRef,
    MarkEntity,
    ParticipationMarkData,
)


@dataclass(frozen=True)
class CreateEventParams:
    name: str
    work_id: str
    date: Optional[Any] = None
    course_id: Optional[str] = None
    status: str = 'planned'
    location: str = ''
    description: str = ''
    event_id: str = ''


@dataclass(frozen=True)
class GradeParticipationParams:
    participation_id: str
    score: Optional[int] = None
    points: Optional[int] = None
    max_points: Optional[int] = None
    teacher_comment: str = ''
    mistakes_analysis: str = ''
    recommendations: str = ''
    checked_by: str = ''
    work_scan: Optional[Any] = None
    task_scores: Optional[Dict[str, dict]] = None
    is_retake: bool = False
    is_excellent: bool = False
    needs_attention: bool = False
    sync_event_status: bool = True


@dataclass(frozen=True)
class GradeParticipationResult:
    mark_id: str
    participation_id: str
    event_id: str
    student_name: str
    score: Optional[int]
    event_status: str


class IEventRepository(ABC):
    @abstractmethod
    def get_list_events(self) -> List[object]:
        """Return events for the list page."""

    @abstractmethod
    def get_detail_participations(self, event_id: str) -> List[EventParticipationRow]:
        """Return event detail participation rows."""

    @abstractmethod
    def get_available_variants(self, event_id: str) -> List[EventVariantRef]:
        """Return variants available for inline assignment."""

    @abstractmethod
    def get_event_status(self, event_id: str) -> Optional[str]:
        """Return the current event status."""

    @abstractmethod
    def add_participants(self, event_id: str, student_ids: List[str]) -> int:
        """Add assigned participations and return the number of new rows."""

    @abstractmethod
    def assign_variants(
        self,
        event_id: str,
        assignments: Dict[str, str],
    ) -> int:
        """Assign variants to event participations and return changed count."""

    @abstractmethod
    def assign_variant(
        self,
        event_id: str,
        participation_id: str,
        variant_id: str,
    ) -> EventVariantAssignmentResult:
        """Assign one variant and return data for user feedback."""

    @abstractmethod
    def set_event_status(self, event_id: str, status: str) -> None:
        """Persist a new event status."""

    @abstractmethod
    def get_by_id(self, event_id: str) -> Optional[EventEntity]:
        """Return an event by ID."""

    @abstractmethod
    def get_participation_ref(
        self,
        participation_id: str,
    ) -> Optional[EventParticipationRef]:
        """Return a lightweight participation reference by ID."""

    @abstractmethod
    def get_student_mark(
        self,
        event_id: str,
        student_id: str,
    ) -> Optional[MarkEntity]:
        """Return a student's mark for an event."""

    @abstractmethod
    def get_participation_marks(self, event_id: str) -> List[ParticipationMarkData]:
        """Return participation data with optional marks for preview."""

    @abstractmethod
    def create_event(self, params: CreateEventParams) -> str:
        """Create an event and return its ID."""

    @abstractmethod
    def update_event(self, params: CreateEventParams) -> bool:
        """Update an event and return whether it was found."""

    @abstractmethod
    def create_participation(
        self,
        event_id: str,
        student_id: str,
        variant_id: str,
    ) -> str:
        """Create an assigned event participation and return its ID."""

    @abstractmethod
    def grade_participation(
        self,
        params: GradeParticipationParams,
    ) -> GradeParticipationResult:
        """Persist a mark and update participation/event review state."""
