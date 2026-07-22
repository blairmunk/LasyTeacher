"""Prepare data for the sectioned document template form."""

from dataclasses import dataclass
from typing import Tuple

from core_logic.entities.document import DocumentTemplateSpec
from core_logic.interfaces.document_template_repo import (
    IDocumentTemplateRepository,
)
from core_logic.value_objects.document_section_catalog import (
    DocumentSectionCatalogItem,
    get_document_section_catalog,
)
from core_logic.value_objects.document_type_catalog import (
    DocumentTypeCatalogItem,
    get_document_type_catalog,
)


@dataclass(frozen=True)
class GetDocumentTemplateFormDataRequest:
    template_id: str = ''
    renderable_only: bool = True
    include_legacy_sections: bool = False


@dataclass(frozen=True)
class DocumentTemplateFormData:
    document_types: Tuple[DocumentTypeCatalogItem, ...]
    sections: Tuple[DocumentSectionCatalogItem, ...]
    template: DocumentTemplateSpec | None = None


class GetDocumentTemplateFormDataUseCase:
    def __init__(
        self,
        document_template_repo: IDocumentTemplateRepository | None = None,
    ):
        self.document_template_repo = document_template_repo

    def execute(
        self,
        request: GetDocumentTemplateFormDataRequest | None = None,
    ) -> DocumentTemplateFormData:
        request = request or GetDocumentTemplateFormDataRequest()
        return DocumentTemplateFormData(
            document_types=get_document_type_catalog(
                renderable_only=request.renderable_only,
            ),
            sections=get_document_section_catalog(
                include_legacy=request.include_legacy_sections,
                renderable_only=request.renderable_only,
            ),
            template=self._template(request.template_id),
        )

    def _template(self, template_id: str) -> DocumentTemplateSpec | None:
        if not template_id or self.document_template_repo is None:
            return None
        return self.document_template_repo.get_template_spec(
            template_id=template_id,
        )
