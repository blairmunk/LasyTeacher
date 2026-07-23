"""Print settings selection helpers."""

from core_logic.entities.document import PrintSettingsSpec
from core_logic.interfaces.print_settings_repo import (
    IPrintSettingsRepository,
)


def resolve_document_print_settings_spec(
    document_type: str,
    request_print_settings_spec: PrintSettingsSpec | None = None,
    request_print_settings_id: str = '',
    document_template_repo: IPrintSettingsRepository | None = None,
) -> PrintSettingsSpec | None:
    if request_print_settings_spec is not None:
        return request_print_settings_spec
    if document_template_repo is None:
        return None
    if request_print_settings_id:
        return document_template_repo.get_print_settings_spec(
            print_settings_id=request_print_settings_id,
            document_type=document_type,
        )
    return document_template_repo.get_default_print_settings_spec(document_type)
