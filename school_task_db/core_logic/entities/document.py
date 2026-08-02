"""Generic document model for section-based rendering."""

from dataclasses import dataclass, field
from typing import Any, Mapping, Tuple


WORK_SOURCE_TYPE = 'work'
REMEDIAL_VARIANT_SOURCE_TYPE = 'remedial_variant'
REMEDIAL_WORK_SOURCE_TYPE = 'remedial_work'
EVENT_REPORT_SOURCE_TYPE = 'event_report'
STUDENT_DIGEST_SOURCE_TYPE = 'student_digest'


@dataclass(frozen=True)
class DocumentPresentation:
    html_template_override: str = ''
    latex_template_override: str = ''
    custom_css: str = ''
    custom_latex_preamble: str = ''

    def template_override_for_renderer(self, renderer_type: str) -> str:
        if renderer_type == 'html':
            return self.html_template_override
        if renderer_type == 'latex':
            return self.latex_template_override
        return ''

    @property
    def has_customization(self) -> bool:
        return any(
            (
                self.html_template_override,
                self.latex_template_override,
                self.custom_css,
                self.custom_latex_preamble,
            )
        )


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
    presentation: DocumentPresentation = field(
        default_factory=DocumentPresentation,
    )

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
            presentation=self.presentation,
        )


@dataclass(frozen=True)
class DocumentSectionSpec:
    section_type: str
    title: str = ''
    options: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, 'section_type', self.section_type.strip())
        object.__setattr__(self, 'title', self.title.strip())
        object.__setattr__(self, 'options', dict(self.options))
        if not self.section_type:
            raise ValueError('section_type is required')


@dataclass(frozen=True)
class DocumentRecipe:
    """Transient document-level assembly instructions for the engine."""

    document_type: str
    sections: Tuple[DocumentSectionSpec, ...] = field(default_factory=tuple)
    presentation: DocumentPresentation = field(
        default_factory=DocumentPresentation,
    )

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
            presentation=self.presentation,
        )


@dataclass(frozen=True)
class DocumentPresentationProfile:
    """Saved presentation settings for a rendered document."""

    name: str
    document_type: str
    presentation_profile_id: str = ''
    description: str = ''
    is_default: bool = False
    presentation: DocumentPresentation = field(
        default_factory=DocumentPresentation,
    )

    def __post_init__(self):
        if not self.document_type:
            raise ValueError('document_type is required')


@dataclass(frozen=True)
class CreatePresentationProfileParams:
    name: str
    document_type: str
    description: str = ''
    is_default: bool = False
    presentation: DocumentPresentation = field(
        default_factory=DocumentPresentation,
    )

    def __post_init__(self):
        object.__setattr__(self, 'name', self.name.strip())
        object.__setattr__(self, 'document_type', self.document_type.strip())
        object.__setattr__(self, 'description', self.description.strip())


@dataclass(frozen=True)
class CreatePresentationProfileResult:
    status: str
    presentation_profile_id: str = ''
    errors: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def success(self) -> bool:
        return self.status == 'created'


@dataclass(frozen=True)
class UpdatePresentationProfileParams:
    presentation_profile_id: str
    name: str
    document_type: str
    description: str = ''
    is_default: bool = False
    presentation: DocumentPresentation = field(
        default_factory=DocumentPresentation,
    )

    def __post_init__(self):
        object.__setattr__(
            self,
            'presentation_profile_id',
            self.presentation_profile_id.strip(),
        )
        object.__setattr__(self, 'name', self.name.strip())
        object.__setattr__(self, 'document_type', self.document_type.strip())
        object.__setattr__(self, 'description', self.description.strip())


@dataclass(frozen=True)
class UpdatePresentationProfileResult:
    status: str
    presentation_profile_id: str = ''
    errors: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def success(self) -> bool:
        return self.status == 'updated'
