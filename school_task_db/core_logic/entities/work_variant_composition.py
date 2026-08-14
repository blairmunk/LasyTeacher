"""Data contracts for composing and persisting work variants."""

from dataclasses import dataclass, field
from typing import Any, Mapping, Tuple

from core_logic.value_objects.task_print_settings import (
    DEFAULT_BLANK_SPACE_AREA_CM2,
    TASK_BANK_ROLE_ANY,
    TASK_BANK_ROLE_CONTROL,
    TASK_RENDER_MODE_TASK_ONLY,
)
from core_logic.value_objects.work_content_plan import (
    WORK_CONTENT_TEXT,
    WORK_CONTENT_THEORY,
)
from core_logic.value_objects.work_assessment import (
    WORK_ASSESSMENT_MODE_VARIANT,
)


@dataclass(frozen=True)
class AvailableVariantTask:
    task_id: str
    bank_role: str = TASK_BANK_ROLE_CONTROL


@dataclass(frozen=True)
class WorkVariantSpecRow:
    spec_row_id: str
    count: int
    weight: int
    content_order: int = 0
    available_tasks: Tuple[AvailableVariantTask, ...] = field(
        default_factory=tuple,
    )
    render_mode: str = TASK_RENDER_MODE_TASK_ONLY
    is_assessable: bool = True
    blank_cells_after: bool = False
    blank_space_area_cm2: int = DEFAULT_BLANK_SPACE_AREA_CM2
    page_break_after: bool = False

    def __post_init__(self):
        object.__setattr__(self, 'available_tasks', tuple(self.available_tasks))


@dataclass(frozen=True)
class WorkVariantSpecSourceRow:
    spec_row_id: str
    count: int
    weight: int
    content_order: int = 0
    available_tasks: Tuple[AvailableVariantTask, ...] = field(
        default_factory=tuple,
    )
    bank_role_filter: str = TASK_BANK_ROLE_ANY
    render_mode: str = TASK_RENDER_MODE_TASK_ONLY
    is_assessable: bool = True
    blank_cells_after: bool = False
    blank_space_area_cm2: int = DEFAULT_BLANK_SPACE_AREA_CM2
    page_break_after: bool = False

    def __post_init__(self):
        object.__setattr__(self, 'available_tasks', tuple(self.available_tasks))


@dataclass(frozen=True)
class WorkTheorySubtopicSource:
    subtopic_id: str
    name: str
    content: str = ''


@dataclass(frozen=True)
class WorkTheoryTopicSource:
    topic_id: str
    name: str
    subject: str = ''
    section: str = ''
    grade_level: int = 0
    content: str = ''
    subtopics: Tuple[WorkTheorySubtopicSource, ...] = field(
        default_factory=tuple,
    )

    def __post_init__(self):
        object.__setattr__(self, 'subtopics', tuple(self.subtopics))


@dataclass(frozen=True)
class WorkVariantContentBlock:
    source_content_id: str
    content_type: str
    order: int
    title: str = ''
    body: str = ''
    topics: Tuple[WorkTheoryTopicSource, ...] = field(default_factory=tuple)
    include_subtopics: bool = False

    def __post_init__(self):
        if self.content_type not in (
            WORK_CONTENT_THEORY,
            WORK_CONTENT_TEXT,
        ):
            raise ValueError(
                f'Unsupported work content type: {self.content_type}',
            )
        object.__setattr__(self, 'topics', tuple(self.topics))


@dataclass(frozen=True)
class WorkVariantCompositionInput:
    work_name: str
    duration: int
    max_score: int
    effective_max_score: int
    variant_counter: int
    spec_rows: Tuple[WorkVariantSpecRow, ...] = field(default_factory=tuple)
    content_blocks: Tuple[WorkVariantContentBlock, ...] = field(
        default_factory=tuple,
    )

    def __post_init__(self):
        object.__setattr__(self, 'spec_rows', tuple(self.spec_rows))
        object.__setattr__(
            self,
            'content_blocks',
            tuple(self.content_blocks),
        )


@dataclass(frozen=True)
class WorkVariantCompositionSource:
    work_name: str
    duration: int
    max_score: int
    variant_counter: int
    assessment_mode: str = WORK_ASSESSMENT_MODE_VARIANT
    spec_rows: Tuple[WorkVariantSpecSourceRow, ...] = field(
        default_factory=tuple,
    )
    content_blocks: Tuple[WorkVariantContentBlock, ...] = field(
        default_factory=tuple,
    )

    def __post_init__(self):
        object.__setattr__(self, 'spec_rows', tuple(self.spec_rows))
        object.__setattr__(self, 'content_blocks', tuple(self.content_blocks))


@dataclass(frozen=True)
class VariantTaskCreationPlan:
    task_id: str
    source_selection_id: str
    content_order: int
    order: int
    max_points: int
    weight: int
    bank_role: str
    render_mode: str
    is_assessable: bool
    blank_cells_after: bool
    blank_space_area_cm2: int
    page_break_after: bool = False


@dataclass(frozen=True)
class VariantContentBlockCreationPlan:
    source_content_id: str
    content_type: str
    order: int
    title: str = ''
    content: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, 'content', dict(self.content))


@dataclass(frozen=True)
class VariantCreationPlan:
    number: int
    work_name_snapshot: str
    max_score_snapshot: int
    duration_snapshot: int
    tasks: Tuple[VariantTaskCreationPlan, ...] = field(default_factory=tuple)
    content_blocks: Tuple[VariantContentBlockCreationPlan, ...] = field(
        default_factory=tuple,
    )

    def __post_init__(self):
        object.__setattr__(self, 'tasks', tuple(self.tasks))
        object.__setattr__(self, 'content_blocks', tuple(self.content_blocks))


@dataclass(frozen=True)
class WorkVariantCompositionPlan:
    variants: Tuple[VariantCreationPlan, ...]
    next_variant_counter: int

    def __post_init__(self):
        object.__setattr__(self, 'variants', tuple(self.variants))


@dataclass(frozen=True)
class WorkVariantCompositionSaveResult:
    status: str
