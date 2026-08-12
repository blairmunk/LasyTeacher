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
    difficulty_display: str = ''
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
    codifier_content_entries: Tuple[TaskCodifierSnapshot, ...] = field(
        default_factory=tuple,
    )
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
            'codifier_content_entries',
            tuple(self.codifier_content_entries),
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
        data['codifier_content_entries'] = tuple(
            TaskCodifierSnapshot(**item)
            for item in data.get('codifier_content_entries', ())
        )
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


def task_content_snapshot_from_mapping(value) -> TaskContentSnapshot:
    return TaskContentSnapshot.from_mapping(value)


def task_content_snapshot_payload(value) -> Mapping[str, Any]:
    """Project a stored task snapshot to renderer-neutral document data."""
    snapshot = (
        value
        if isinstance(value, TaskContentSnapshot)
        else task_content_snapshot_from_mapping(value)
    )
    return {
        'id': snapshot.task_id,
        'text': snapshot.text,
        'answer': snapshot.answer,
        'short_solution': snapshot.short_solution,
        'full_solution': snapshot.full_solution,
        'hint': snapshot.hint,
        'instruction': snapshot.instruction,
        'task_type': snapshot.task_type,
        'task_type_display': snapshot.task_type_display,
        'difficulty': snapshot.difficulty,
        'difficulty_display': snapshot.difficulty_display,
        'topic': snapshot.topic_name,
        'topic_section': snapshot.topic_section,
        'subtopic': snapshot.subtopic_name,
        'source': snapshot.source_name,
        'source_detail': snapshot.source_detail,
        'content_element': snapshot.content_element,
        'requirement_element': snapshot.requirement_element,
        'codifier_content_entries': tuple(
            {
                'codifier_id': item.codifier_id,
                'codifier_name': item.codifier_name,
                'codifier_short_name': item.codifier_short_name,
                'code': item.code,
                'name': item.name,
            }
            for item in snapshot.codifier_content_entries
        ),
        'codifier_requirements': tuple(
            {
                'codifier_id': item.codifier_id,
                'codifier_name': item.codifier_name,
                'codifier_short_name': item.codifier_short_name,
                'code': item.code,
                'name': item.name,
            }
            for item in snapshot.codifier_requirements
        ),
        'content_element_descriptions': (
            snapshot.content_element_descriptions
        ),
        'images': tuple(
            {
                'image_id': item.image_id,
                'file_name': item.file_name,
                'position': item.position,
                'caption': item.caption,
                'order': item.order,
            }
            for item in snapshot.images
        ),
    }
