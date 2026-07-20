"""Document engine dependency helpers for rendering use cases."""

from core_logic.interfaces.document_engine import IDocumentEngine


def resolve_document_engine(
    document_engine: IDocumentEngine | None = None,
    document_rendering_service: IDocumentEngine | None = None,
    document_generation_service: IDocumentEngine | None = None,
) -> IDocumentEngine:
    return (
        document_engine
        or document_rendering_service
        or document_generation_service
    )
