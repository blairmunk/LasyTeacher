"""Use case for preparing document print profile editor data."""

from dataclasses import dataclass
from typing import List, Tuple

from core_logic.entities.document import PrintSettingsSpec
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
class GetDocumentTemplateEditorDataRequest:
    document_type: str = ''
    renderable_only: bool = False
    include_legacy_sections: bool = False


@dataclass(frozen=True)
class DocumentTemplateEditorData:
    document_types: Tuple[DocumentTypeCatalogItem, ...]
    sections: Tuple[DocumentSectionCatalogItem, ...]
    print_profiles: List[PrintSettingsSpec]

    @property
    def templates(self) -> List[PrintSettingsSpec]:
        return self.print_profiles


class GetDocumentTemplateEditorDataUseCase:
    def __init__(
        self,
        document_template_repo: IDocumentTemplateRepository | None = None,
    ):
        self.document_template_repo = document_template_repo

    def execute(
        self,
        request: GetDocumentTemplateEditorDataRequest | None = None,
    ) -> DocumentTemplateEditorData:
        request = request or GetDocumentTemplateEditorDataRequest()
        return DocumentTemplateEditorData(
            document_types=get_document_type_catalog(
                renderable_only=request.renderable_only,
            ),
            sections=get_document_section_catalog(
                document_type=request.document_type,
                include_legacy=request.include_legacy_sections,
                renderable_only=request.renderable_only,
            ),
            print_profiles=self._print_profiles(request.document_type),
        )

    def _print_profiles(self, document_type: str) -> List[PrintSettingsSpec]:
        if self.document_template_repo is None:
            return []
        return self.document_template_repo.list_print_settings_specs(
            document_type=document_type,
        )
