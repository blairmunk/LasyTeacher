"""Prepare data for the sectioned document print settings form."""

from dataclasses import dataclass
from typing import Tuple

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
class GetPrintSettingsFormDataRequest:
    print_settings_id: str = ''
    renderable_only: bool = True
    include_legacy_sections: bool = False


@dataclass(frozen=True)
class PrintSettingsFormData:
    document_types: Tuple[DocumentTypeCatalogItem, ...]
    sections: Tuple[DocumentSectionCatalogItem, ...]
    print_profile: PrintSettingsSpec | None = None


class GetPrintSettingsFormDataUseCase:
    """Prepare data for the sectioned document print settings form."""

    def __init__(
        self,
        print_settings_repo: IPrintSettingsRepository | None = None,
    ):
        self.print_settings_repo = print_settings_repo

    def execute(
        self,
        request: GetPrintSettingsFormDataRequest | None = None,
    ) -> PrintSettingsFormData:
        request = request or GetPrintSettingsFormDataRequest()
        return PrintSettingsFormData(
            document_types=get_document_type_catalog(
                renderable_only=request.renderable_only,
            ),
            sections=get_document_section_catalog(
                include_legacy=request.include_legacy_sections,
                renderable_only=request.renderable_only,
            ),
            print_profile=self._print_profile(request.print_settings_id),
        )

    def _print_profile(self, print_settings_id: str) -> PrintSettingsSpec | None:
        if not print_settings_id or self.print_settings_repo is None:
            return None
        return self.print_settings_repo.get_print_settings_spec(
            print_settings_id=print_settings_id,
        )
