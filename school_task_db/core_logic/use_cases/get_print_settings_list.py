"""Build document print settings list data."""

from dataclasses import dataclass
from typing import List

from core_logic.entities.document import PrintSettingsSpec
from core_logic.interfaces.print_settings_repo import (
    IPrintSettingsRepository,
)


@dataclass(frozen=True)
class GetPrintSettingsListRequest:
    document_type: str = ''


@dataclass(frozen=True)
class PrintSettingsListData:
    print_profiles: List[PrintSettingsSpec]


class GetPrintSettingsListUseCase:
    """Build document print settings list data."""

    def __init__(self, print_settings_repo: IPrintSettingsRepository):
        self.print_settings_repo = print_settings_repo

    def execute(
        self,
        request: GetPrintSettingsListRequest | None = None,
    ) -> PrintSettingsListData:
        request = request or GetPrintSettingsListRequest()
        return PrintSettingsListData(
            print_profiles=self.print_settings_repo.list_print_settings_specs(
                document_type=request.document_type,
            ),
        )
