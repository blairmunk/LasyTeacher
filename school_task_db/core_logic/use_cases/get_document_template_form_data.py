"""Legacy adapter for document print settings form data."""

from dataclasses import dataclass
from typing import Tuple

from core_logic.entities.document import PrintSettingsSpec
from core_logic.interfaces.print_settings_repo import (
    IPrintSettingsRepository,
)
from core_logic.use_cases.get_print_settings_form_data import (
    GetPrintSettingsFormDataRequest,
    GetPrintSettingsFormDataUseCase,
    PrintSettingsFormData,
)
from core_logic.value_objects.document_section_catalog import (
    DocumentSectionCatalogItem,
)
from core_logic.value_objects.document_type_catalog import (
    DocumentTypeCatalogItem,
)


@dataclass(frozen=True)
class GetDocumentTemplateFormDataRequest:
    template_id: str = ''
    print_settings_id: str = ''
    renderable_only: bool = True
    include_legacy_sections: bool = False

    @property
    def selected_print_settings_id(self) -> str:
        return self.print_settings_id or self.template_id


@dataclass(frozen=True)
class DocumentTemplateFormData:
    document_types: Tuple[DocumentTypeCatalogItem, ...]
    sections: Tuple[DocumentSectionCatalogItem, ...]
    print_profile: PrintSettingsSpec | None = None

    @property
    def template(self) -> PrintSettingsSpec | None:
        return self.print_profile


class GetDocumentTemplateFormDataUseCase(GetPrintSettingsFormDataUseCase):
    """Adapt the former template-oriented form data contract."""

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
        request: GetDocumentTemplateFormDataRequest | None = None,
    ) -> DocumentTemplateFormData:
        request = request or GetDocumentTemplateFormDataRequest()
        data = super().execute(
            GetPrintSettingsFormDataRequest(
                print_settings_id=request.selected_print_settings_id,
                renderable_only=request.renderable_only,
                include_legacy_sections=request.include_legacy_sections,
            ),
        )
        return DocumentTemplateFormData(
            document_types=data.document_types,
            sections=data.sections,
            print_profile=data.print_profile,
        )
