"""Document template selection helpers."""

from core_logic.entities.document import DocumentTemplateSpec
from core_logic.interfaces.document_template_repo import (
    IDocumentTemplateRepository,
)


def resolve_document_template_spec(
    template_type: str,
    request_template_spec: DocumentTemplateSpec | None = None,
    document_template_repo: IDocumentTemplateRepository | None = None,
) -> DocumentTemplateSpec | None:
    if request_template_spec is not None:
        return request_template_spec
    if document_template_repo is None:
        return None
    return document_template_repo.get_default_template_spec(template_type)
