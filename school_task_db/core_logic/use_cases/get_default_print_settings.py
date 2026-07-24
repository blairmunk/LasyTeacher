"""Find the default document print settings for a document type."""

from dataclasses import dataclass

from core_logic.entities.document import PrintSettingsSpec
from core_logic.interfaces.print_settings_repo import (
    IPrintSettingsRepository,
)


@dataclass(frozen=True)
class GetDefaultPrintSettingsRequest:
    document_type: str


@dataclass(frozen=True)
class DefaultPrintSettingsData:
    print_profile: PrintSettingsSpec | None = None


class GetDefaultPrintSettingsUseCase:
    """Find the default document print settings for a document type."""

    def __init__(self, print_settings_repo: IPrintSettingsRepository):
        self.print_settings_repo = print_settings_repo

    def execute(
        self,
        request: GetDefaultPrintSettingsRequest,
    ) -> DefaultPrintSettingsData:
        return DefaultPrintSettingsData(
            print_profile=(
                self.print_settings_repo.get_default_print_settings_spec(
                    request.document_type,
                )
            ),
        )
