"""Review screen domain DTOs."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ReviewStudentRef:
    pk: str
    last_name: str
    first_name: str
    middle_name: str = ''

    def get_full_name(self) -> str:
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return ' '.join(parts)


@dataclass(frozen=True)
class ReviewEventRef:
    pk: str
    name: str
    planned_date: Optional[datetime] = None
    status: str = ''
    work: Optional['ReviewWorkRef'] = None
    course: Optional['ReviewCourseRef'] = None


@dataclass(frozen=True)
class ReviewWorkRef:
    pk: str
    name: str
    work_type: str = ''
    work_type_display: str = ''

    def get_work_type_display(self) -> str:
        return self.work_type_display or self.work_type


@dataclass(frozen=True)
class ReviewCourseRef:
    pk: str
    name: str


@dataclass(frozen=True)
class ReviewVariantTaskCount:
    count: int


@dataclass(frozen=True)
class ReviewVariantRef:
    pk: str
    number: int
    tasks_count: int = 0

    @property
    def tasks(self) -> ReviewVariantTaskCount:
        return ReviewVariantTaskCount(count=self.tasks_count)


@dataclass(frozen=True)
class ReviewParticipationRef:
    pk: str
    student: ReviewStudentRef
    event: ReviewEventRef
    variant: Optional[ReviewVariantRef] = None


@dataclass(frozen=True)
class ReviewTopicRef:
    pk: str
    name: str


@dataclass(frozen=True)
class ReviewTaskRef:
    id: str
    text: str
    answer: str = ''
    short_solution: str = ''
    difficulty: Optional[int] = None
    topic: Optional[ReviewTopicRef] = None

    @property
    def pk(self) -> str:
        return self.id


@dataclass(frozen=True)
class ReviewVariantTaskRef:
    task: ReviewTaskRef
    weight: int = 5


@dataclass(frozen=True)
class ReviewWorkScanRef:
    name: str
    url: str


@dataclass(frozen=True)
class ReviewMarkRef:
    pk: str
    score: Optional[int] = None
    points: Optional[int] = None
    max_points: Optional[int] = None
    teacher_comment: str = ''
    work_scan: Optional[ReviewWorkScanRef] = None
    task_scores: Dict[str, dict] = field(default_factory=dict)


@dataclass(frozen=True)
class ReviewTaskScoreRow:
    task: ReviewTaskRef
    number: int
    points: int
    max_points: int
    comment: str = ''


@dataclass(frozen=True)
class ReviewCommentRef:
    text: str


@dataclass(frozen=True)
class ReviewEventProgress:
    event: ReviewEventRef
    total_participants: int
    graded_participants: int
    absent_participants: int
    active_participants: int
    progress_percentage: float
    remaining: int


@dataclass(frozen=True)
class ReviewDashboardData:
    needs_review: List[ReviewEventProgress]
    in_progress: List[ReviewEventProgress]
    fully_graded: List[ReviewEventProgress]
    total_events: int


@dataclass(frozen=True)
class EventReviewParticipationRow:
    participation: ReviewParticipationRef
    mark: Optional[ReviewMarkRef]
    has_mark: bool
    is_absent: bool
    student: ReviewStudentRef
    variant: Optional[ReviewVariantRef]


@dataclass(frozen=True)
class EventReviewData:
    has_participants: bool
    variants_assigned: bool
    all_variants_assigned: bool
    blocked: bool
    block_reason: str
    available_variants: List[ReviewVariantRef]
    participations_data: List[EventReviewParticipationRow]
    total_participants: int
    active_participants: int
    graded_participants: int
    absent_participants: int
    progress_percentage: float
    avg_score: float
    score_distribution: Dict[int, int]


@dataclass(frozen=True)
class ParticipationReviewData:
    participation: ReviewParticipationRef
    mark: ReviewMarkRef
    tasks_with_scores: List[ReviewTaskScoreRow]
    typical_comments: List[ReviewCommentRef]
    previous_participation: Optional[ReviewParticipationRef]
    next_participation: Optional[ReviewParticipationRef]
    current_position: int
    total_positions: int
    navigation_progress: float
