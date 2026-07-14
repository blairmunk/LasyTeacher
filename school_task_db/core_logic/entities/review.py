"""Review screen domain DTOs."""

from dataclasses import dataclass, field
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


@dataclass(frozen=True)
class ReviewVariantRef:
    pk: str
    number: int


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
