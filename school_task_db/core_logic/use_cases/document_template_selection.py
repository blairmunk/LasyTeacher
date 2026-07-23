"""Print settings selection helpers.

The module name is legacy; persistence is still backed by document templates.
"""

from core_logic.entities.document import PrintSettingsSpec
from core_logic.interfaces.document_template_repo import (
    IDocumentTemplateRepository,
)


def resolve_document_print_settings_spec(
    document_type: str,
    request_print_settings_spec: PrintSettingsSpec | None = None,
    request_print_settings_id: str = '',
    document_template_repo: IDocumentTemplateRepository | None = None,
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


def resolve_document_template_spec(
    template_type: str,
    request_template_spec: PrintSettingsSpec | None = None,
    request_template_id: str = '',
    document_template_repo: IDocumentTemplateRepository | None = None,
) -> PrintSettingsSpec | None:
    """Legacy alias for callers that still use template terminology."""

    return resolve_document_print_settings_spec(
        document_type=template_type,
        request_print_settings_spec=request_template_spec,
        request_print_settings_id=request_template_id,
        document_template_repo=document_template_repo,
    )
