"""Request DTOs for document rendering."""

from dataclasses import dataclass

from core_logic.entities.document import (
    Document,
    DocumentSection,
)
from core_logic.value_objects.document_render_options import RenderTarget


@dataclass(frozen=True)
class DocumentRenderRequest:
    document: Document
    render_target: RenderTarget


@dataclass(frozen=True)
class DocumentSectionRenderRequest:
    document: Document
    section: DocumentSection
    render_target: RenderTarget


@dataclass(frozen=True)
class DocumentContentWrapRequest:
    document: Document
    render_target: RenderTarget
    body_content: str
