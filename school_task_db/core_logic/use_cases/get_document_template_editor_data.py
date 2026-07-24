"""Legacy adapter for document print settings editor data."""

from dataclasses import dataclass
from typing import List, Tuple

from core_logic.entities.document import PrintSettingsSpec
from core_logic.interfaces.print_settings_repo import (
    IPrintSettingsRepository,
)
from core_logic.use_cases.get_print_settings_editor_data import (
    GetPrintSettingsEditorDataRequest,
    GetPrintSettingsEditorDataUseCase,
    PrintSettingsEditorData,
)
from core_logic.value_objects.document_section_catalog import (
    DocumentSectionCatalogItem,
)
from core_logic.value_objects.document_type_catalog import (
    DocumentTypeCatalogItem,
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


class GetDocumentTemplateEditorDataUseCase(GetPrintSettingsEditorDataUseCase):
    """Adapt the former template-oriented editor data contract."""

    def __init__(
        self,
        document_template_repo: IPrintSettingsRepository | None = None,
        print_settings_repo: IPrintSettingsRepository | None = None,
    ):
        repository = print_settings_repo or document_template_repo
        super().__init__(print_settings_repo=repository)
        self.document_template_repo = repository

    def execute(
        self,
        request: GetDocumentTemplateEditorDataRequest | None = None,
    ) -> DocumentTemplateEditorData:
        request = request or GetDocumentTemplateEditorDataRequest()
        data = super().execute(
            GetPrintSettingsEditorDataRequest(
                document_type=request.document_type,
                renderable_only=request.renderable_only,
                include_legacy_sections=request.include_legacy_sections,
            ),
        )
        return DocumentTemplateEditorData(
            document_types=data.document_types,
            sections=data.sections,
            print_profiles=data.print_profiles,
        )
