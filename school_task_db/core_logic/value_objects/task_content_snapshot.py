"""Immutable task content stored as part of a generated variant."""

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Tuple


TASK_CONTENT_SNAPSHOT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class TaskCodifierSnapshot:
    codifier_id: str
    codifier_name: str
    codifier_short_name: str
    code: str
    name: str = ''


@dataclass(frozen=True)
class TaskImageSnapshot:
    image_id: str
    file_name: str
    position: str = ''
    caption: str = ''
    order: int = 1


@dataclass(frozen=True)
class TaskContentSnapshot:
    """Historical task content captured when a variant is generated."""

    task_id: str
    text: str
    answer: str
    short_solution: str = ''
    full_solution: str = ''
    hint: str = ''
    instruction: str = ''
    task_type: str = ''
    task_type_display: str = ''
    difficulty: int = 0
    topic_id: str = ''
    topic_name: str = ''
    topic_section: str = ''
    subject: str = ''
    subtopic_id: str = ''
    subtopic_name: str = ''
    source_id: str = ''
    source_name: str = ''
    source_detail: str = ''
    content_element: str = ''
    requirement_element: str = ''
    codifier_requirements: Tuple[TaskCodifierSnapshot, ...] = field(
        default_factory=tuple,
    )
    content_element_descriptions: Tuple[str, ...] = field(
        default_factory=tuple,
    )
    images: Tuple[TaskImageSnapshot, ...] = field(default_factory=tuple)
    schema_version: int = TASK_CONTENT_SNAPSHOT_SCHEMA_VERSION

    def __post_init__(self):
        if not self.task_id:
            raise ValueError('task_id is required')
        if self.schema_version != TASK_CONTENT_SNAPSHOT_SCHEMA_VERSION:
            raise ValueError(
                f'Unsupported task snapshot schema: {self.schema_version}',
            )
        object.__setattr__(
            self,
            'codifier_requirements',
            tuple(self.codifier_requirements),
        )
        object.__setattr__(self, 'images', tuple(self.images))
        object.__setattr__(
            self,
            'content_element_descriptions',
            tuple(self.content_element_descriptions),
        )

    def to_mapping(self) -> Mapping[str, Any]:
        return asdict(self)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]):
        if not value:
            raise ValueError('Variant task has no task content snapshot')
        data = dict(value)
        data['codifier_requirements'] = tuple(
            TaskCodifierSnapshot(**item)
            for item in data.get('codifier_requirements', ())
        )
        data['images'] = tuple(
            TaskImageSnapshot(**item)
            for item in data.get('images', ())
        )
        data['content_element_descriptions'] = tuple(
            data.get('content_element_descriptions', ()),
        )
        return cls(**data)
