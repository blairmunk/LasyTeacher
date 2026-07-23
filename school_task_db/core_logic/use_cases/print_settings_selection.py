"""Print settings selection helpers."""

from core_logic.entities.document import PrintSettingsSpec
from core_logic.interfaces.print_settings_repo import (
    IPrintSettingsRepository,
)


def resolve_document_print_settings_spec(
    document_type: str,
    request_print_settings_spec: PrintSettingsSpec | None = None,
    request_print_settings_id: str = '',
    print_settings_repo: IPrintSettingsRepository | None = None,
    document_template_repo: IPrintSettingsRepository | None = None,
) -> PrintSettingsSpec | None:
    print_settings_repo = print_settings_repo or document_template_repo
    if request_print_settings_spec is not None:
        return request_print_settings_spec
    if print_settings_repo is None:
        return None
    if request_print_settings_id:
        return print_settings_repo.get_print_settings_spec(
            print_settings_id=request_print_settings_id,
            document_type=document_type,
        )
    return print_settings_repo.get_default_print_settings_spec(document_type)
