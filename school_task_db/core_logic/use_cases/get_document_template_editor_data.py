"""Use case for preparing document print profile editor data."""

from dataclasses import dataclass
from typing import List, Tuple

from core_logic.entities.document import PrintSettingsSpec
from core_logic.interfaces.print_settings_repo import (
    IPrintSettingsRepository,
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
        print_settings_repo: IPrintSettingsRepository | None = None,
        document_template_repo: IPrintSettingsRepository | None = None,
    ):
        self.print_settings_repo = print_settings_repo or document_template_repo
        self.document_template_repo = self.print_settings_repo

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
        if self.print_settings_repo is None:
            return []
        return self.print_settings_repo.list_print_settings_specs(
            document_type=document_type,
        )


GetPrintSettingsEditorDataRequest = GetDocumentTemplateEditorDataRequest
PrintSettingsEditorData = DocumentTemplateEditorData
GetPrintSettingsEditorDataUseCase = GetDocumentTemplateEditorDataUseCase
