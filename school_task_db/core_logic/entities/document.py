"""Generic document model for section-based rendering."""

from dataclasses import dataclass, field
from typing import Any, Mapping, Tuple


WORK_SOURCE_TYPE = 'work'
REMEDIAL_VARIANT_SOURCE_TYPE = 'remedial_variant'


@dataclass(frozen=True)
class DocumentSourceRef:
    source_type: str
    source_id: str = ''
    title: str = ''

    def __post_init__(self):
        if not self.source_type:
            raise ValueError('source_type is required')


@dataclass(frozen=True)
class DocumentSection:
    section_type: str
    title: str = ''
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.section_type:
            raise ValueError('section_type is required')


@dataclass(frozen=True)
class Document:
    title: str
    document_type: str = ''
    sections: Tuple[DocumentSection, ...] = field(default_factory=tuple)
    source: DocumentSourceRef | None = None

    def __post_init__(self):
        object.__setattr__(self, 'sections', tuple(self.sections))

    @property
    def section_types(self) -> Tuple[str, ...]:
        return tuple(section.section_type for section in self.sections)

    def has_section(self, section_type: str) -> bool:
        return section_type in self.section_types

    def sections_by_type(self, section_type: str) -> Tuple[DocumentSection, ...]:
        return tuple(
            section
            for section in self.sections
            if section.section_type == section_type
        )

    def first_section(self, section_type: str) -> DocumentSection | None:
        sections = self.sections_by_type(section_type)
        if not sections:
            return None
        return sections[0]

    def with_section(self, section: DocumentSection) -> "Document":
        return Document(
            title=self.title,
            document_type=self.document_type,
            sections=(*self.sections, section),
            source=self.source,
        )


@dataclass(frozen=True)
class DocumentSectionSpec:
    section_type: str
    options: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.section_type:
            raise ValueError('section_type is required')


@dataclass(frozen=True)
class DocumentRecipe:
    document_type: str
    sections: Tuple[DocumentSectionSpec, ...] = field(default_factory=tuple)

    def __post_init__(self):
        if not self.document_type:
            raise ValueError('document_type is required')
        object.__setattr__(self, 'sections', tuple(self.sections))

    @property
    def section_types(self) -> Tuple[str, ...]:
        return tuple(section.section_type for section in self.sections)

    def has_section(self, section_type: str) -> bool:
        return section_type in self.section_types

    def sections_by_type(
        self,
        section_type: str,
    ) -> Tuple[DocumentSectionSpec, ...]:
        return tuple(
            section
            for section in self.sections
            if section.section_type == section_type
        )

    def first_section(self, section_type: str) -> DocumentSectionSpec | None:
        sections = self.sections_by_type(section_type)
        if not sections:
            return None
        return sections[0]

    def with_section(self, section: DocumentSectionSpec) -> "DocumentRecipe":
        return DocumentRecipe(
            document_type=self.document_type,
            sections=(*self.sections, section),
        )


@dataclass(frozen=True)
class DocumentTemplateSpec:
    name: str
    template_type: str
    sections: Tuple[DocumentSectionSpec, ...] = field(default_factory=tuple)
    default_content_config: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.template_type:
            raise ValueError('template_type is required')
        object.__setattr__(self, 'sections', tuple(self.sections))
        object.__setattr__(
            self,
            'default_content_config',
            dict(self.default_content_config),
        )

    @property
    def section_types(self) -> Tuple[str, ...]:
        return tuple(section.section_type for section in self.sections)

    def to_recipe(self, document_type: str = '') -> DocumentRecipe:
        return DocumentRecipe(
            document_type=document_type or self.template_type,
            sections=self.sections,
        )
