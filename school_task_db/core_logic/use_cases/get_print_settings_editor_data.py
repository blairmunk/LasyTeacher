"""Prepare data for the sectioned document print settings editor."""

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
class GetPrintSettingsEditorDataRequest:
    document_type: str = ''
    renderable_only: bool = False


@dataclass(frozen=True)
class PrintSettingsEditorData:
    document_types: Tuple[DocumentTypeCatalogItem, ...]
    sections: Tuple[DocumentSectionCatalogItem, ...]
    print_profiles: List[PrintSettingsSpec]


class GetPrintSettingsEditorDataUseCase:
    """Prepare data for the sectioned document print settings editor."""

    def __init__(
        self,
        print_settings_repo: IPrintSettingsRepository | None = None,
    ):
        self.print_settings_repo = print_settings_repo

    def execute(
        self,
        request: GetPrintSettingsEditorDataRequest | None = None,
    ) -> PrintSettingsEditorData:
        request = request or GetPrintSettingsEditorDataRequest()
        return PrintSettingsEditorData(
            document_types=get_document_type_catalog(
                renderable_only=request.renderable_only,
            ),
            sections=get_document_section_catalog(
                document_type=request.document_type,
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
