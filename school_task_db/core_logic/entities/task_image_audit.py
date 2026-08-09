"""Read models for task image position diagnostics."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TaskImageAuditSource:
    pk: str
    task_text: str
    topic_name: str
    filename: str
    caption: str = ''
    position: str = ''

    @property
    def short_id(self) -> str:
        return self.pk[-8:]


@dataclass(frozen=True)
class TaskImagePositionCount:
    position: str
    label: str
    count: int
    percentage: float


@dataclass(frozen=True)
class TaskImagePositionSuggestion:
    image_id: str
    position: str
    position_label: str


@dataclass(frozen=True)
class TaskImageAuditData:
    total_images: int = 0
    distribution: tuple[TaskImagePositionCount, ...] = field(default_factory=tuple)
    missing_images: tuple[TaskImageAuditSource, ...] = field(default_factory=tuple)
    suggestions: tuple[TaskImagePositionSuggestion, ...] = field(default_factory=tuple)

    @property
    def missing_count(self) -> int:
        return len(self.missing_images)
