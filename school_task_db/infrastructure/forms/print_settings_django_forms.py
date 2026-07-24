"""Django forms for document print settings."""

from infrastructure.forms.document_template_django_forms import (
    DocumentTemplateForm,
    section_options_field_name,
)


class PrintSettingsForm(DocumentTemplateForm):
    """Django form for document print settings."""
