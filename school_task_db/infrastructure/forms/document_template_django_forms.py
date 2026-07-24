"""Legacy Django form for document print settings."""

from infrastructure.forms.print_settings_django_forms import (
    PrintSettingsForm,
    section_options_field_name,
)


class DocumentTemplateForm(PrintSettingsForm):
    """Adapt the former document template form name."""
