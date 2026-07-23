"""Legacy aliases for document print settings selection helpers."""

from core_logic.entities.document import PrintSettingsSpec
from core_logic.interfaces.print_settings_repo import (
    IPrintSettingsRepository,
)
from core_logic.use_cases.print_settings_selection import (
    resolve_document_print_settings_spec,
)


def resolve_document_template_spec(
    template_type: str,
    request_template_spec: PrintSettingsSpec | None = None,
    request_template_id: str = '',
    print_settings_repo: IPrintSettingsRepository | None = None,
    document_template_repo: IPrintSettingsRepository | None = None,
) -> PrintSettingsSpec | None:
    """Legacy alias for callers that still use template terminology."""

    return resolve_document_print_settings_spec(
        document_type=template_type,
        request_print_settings_spec=request_template_spec,
        request_print_settings_id=request_template_id,
        print_settings_repo=print_settings_repo,
        document_template_repo=document_template_repo,
    )
