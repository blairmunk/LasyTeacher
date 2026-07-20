"""Use case for listing available document template sections."""

from dataclasses import dataclass
from typing import Tuple

from core_logic.value_objects.document_section_catalog import (
    DocumentSectionCatalogItem,
    get_document_section_catalog,
)


@dataclass(frozen=True)
class GetDocumentSectionCatalogRequest:
    document_type: str = ''
    include_legacy: bool = False
    renderable_only: bool = False


@dataclass(frozen=True)
class DocumentSectionCatalogData:
    sections: Tuple[DocumentSectionCatalogItem, ...]


class GetDocumentSectionCatalogUseCase:
    def execute(
        self,
        request: GetDocumentSectionCatalogRequest | None = None,
    ) -> DocumentSectionCatalogData:
        request = request or GetDocumentSectionCatalogRequest()
        return DocumentSectionCatalogData(
            sections=get_document_section_catalog(
                document_type=request.document_type,
                include_legacy=request.include_legacy,
                renderable_only=request.renderable_only,
            ),
        )
