"""Get one document print settings profile for editing."""

from dataclasses import dataclass

from core_logic.entities.document import PrintSettingsSpec
from core_logic.interfaces.print_settings_repo import (
    IPrintSettingsRepository,
)


@dataclass(frozen=True)
class GetPrintSettingsRequest:
    print_settings_id: str
    document_type: str = ''


@dataclass(frozen=True)
class GetPrintSettingsData:
    print_profile: PrintSettingsSpec | None = None


class GetPrintSettingsUseCase:
    """Get one document print settings profile for editing."""

    def __init__(self, print_settings_repo: IPrintSettingsRepository):
        self.print_settings_repo = print_settings_repo

    def execute(
        self,
        request: GetPrintSettingsRequest,
    ) -> GetPrintSettingsData:
        return GetPrintSettingsData(
            print_profile=self.print_settings_repo.get_print_settings_spec(
                print_settings_id=request.print_settings_id,
                document_type=request.document_type,
            ),
        )
