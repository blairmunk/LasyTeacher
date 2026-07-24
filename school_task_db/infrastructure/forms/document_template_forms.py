"""Legacy adapter for document print settings screens."""

from infrastructure.forms.print_settings_forms import (
    PrintSettingsFormAdapter,
)


class DocumentTemplateFormAdapter(PrintSettingsFormAdapter):
    """Adapt former template-oriented form and context names."""

    def editor_context(self, editor_data, request):
        context = super().editor_context(editor_data, request)
        legacy_print_profiles = [
            {
                **self._print_profile_context(print_profile),
                'template_id': print_profile.print_settings_id,
                'template_type': print_profile.document_type,
            }
            for print_profile in editor_data.print_profiles
        ]
        context['print_profiles'] = legacy_print_profiles
        context['templates'] = legacy_print_profiles
        return context

    def create_params_from_form(self, form):
        return self.create_print_settings_params_from_form(form)

    def update_params_from_form(self, form, template_id):
        return self.update_print_settings_params_from_form(
            form,
            print_settings_id=template_id,
        )

    def form_initial_from_template(self, template):
        return self.form_initial_from_print_settings(template)
