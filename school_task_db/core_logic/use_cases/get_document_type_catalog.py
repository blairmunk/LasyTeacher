"""Use case for listing available document template types."""

from dataclasses import dataclass
from typing import Tuple

from core_logic.value_objects.document_type_catalog import (
    DocumentTypeCatalogItem,
    get_document_type_catalog,
)


@dataclass(frozen=True)
class GetDocumentTypeCatalogRequest:
    renderable_only: bool = False


@dataclass(frozen=True)
class DocumentTypeCatalogData:
    document_types: Tuple[DocumentTypeCatalogItem, ...]


class GetDocumentTypeCatalogUseCase:
    def execute(
        self,
        request: GetDocumentTypeCatalogRequest | None = None,
    ) -> DocumentTypeCatalogData:
        request = request or GetDocumentTypeCatalogRequest()
        return DocumentTypeCatalogData(
            document_types=get_document_type_catalog(
                renderable_only=request.renderable_only,
            ),
        )
