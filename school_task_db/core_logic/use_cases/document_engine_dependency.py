"""Document engine dependency helpers for rendering use cases."""

from core_logic.interfaces.document_engine import IDocumentEngine


def resolve_document_engine(
    document_engine: IDocumentEngine | None = None,
) -> IDocumentEngine:
    resolved_engine = document_engine
    if resolved_engine is None:
        raise ValueError('Document engine dependency is required.')
    return resolved_engine
