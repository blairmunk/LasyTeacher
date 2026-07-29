"""Infrastructure helpers for document presentation profile screens."""

from urllib.parse import urlencode

from core_logic.entities.document import (
    CreatePrintSettingsParams,
    DocumentPresentation,
    UpdatePrintSettingsParams,
)
from core_logic.use_cases.get_print_settings_editor_data import (
    GetPrintSettingsEditorDataRequest,
)
from core_logic.value_objects.document_render_options import FILE_TYPE_LABELS


class PrintSettingsFormAdapter:
    def editor_data_request_from_query(self, query_data):
        return GetPrintSettingsEditorDataRequest(
            document_type=query_data.get('type', ''),
            renderable_only=query_data.get('renderable', '1') == '1',
        )

    def editor_context(self, editor_data, request):
        return {
            'document_types': [
                self._document_type_context(document_type, request)
                for document_type in editor_data.document_types
            ],
            'print_profiles': [
                self._print_profile_context(print_profile)
                for print_profile in editor_data.print_profiles
            ],
            'current_document_type': request.document_type,
            'renderable_only': request.renderable_only,
        }

    def create_print_settings_params_from_form(self, form):
        return CreatePrintSettingsParams(
            name=form.cleaned_data['name'],
            description=form.cleaned_data.get('description', ''),
            document_type=form.cleaned_data['document_type'],
            is_default=form.cleaned_data.get('is_default', False),
            presentation=self._presentation_from_form(form),
        )

    def update_print_settings_params_from_form(self, form, print_settings_id):
        return UpdatePrintSettingsParams(
            print_settings_id=print_settings_id,
            name=form.cleaned_data['name'],
            description=form.cleaned_data.get('description', ''),
            document_type=form.cleaned_data['document_type'],
            is_default=form.cleaned_data.get('is_default', False),
            presentation=self._presentation_from_form(form),
        )

    def form_initial_from_print_settings(self, print_settings):
        return {
            'name': print_settings.name,
            'description': print_settings.description,
            'document_type': print_settings.document_type,
            'custom_css': print_settings.presentation.custom_css,
            'custom_latex_preamble': (
                print_settings.presentation.custom_latex_preamble
            ),
            'html_template_override': (
                print_settings.presentation.html_template_override
            ),
            'latex_template_override': (
                print_settings.presentation.latex_template_override
            ),
            'is_default': print_settings.is_default,
        }

    @staticmethod
    def create_context(form, document_types, sections=None):
        return {
            'form': form,
            'document_types': document_types,
        }

    def _document_type_context(self, document_type, request):
        return {
            'document_type': document_type.document_type,
            'title': document_type.title,
            'description': document_type.description,
            'source_type': document_type.source_type,
            'is_renderable': document_type.is_renderable,
            'renderer_labels': [
                FILE_TYPE_LABELS[renderer_type]
                for renderer_type in document_type.renderer_types
            ],
            'url': self._document_type_url(
                document_type.document_type,
                request,
            ),
        }

    @staticmethod
    def _print_profile_context(print_profile):
        presentation = print_profile.presentation
        return {
            'print_settings_id': print_profile.print_settings_id,
            'name': print_profile.name,
            'description': print_profile.description,
            'document_type': print_profile.document_type,
            'is_default': print_profile.is_default,
            'has_customization': presentation.has_customization,
            'has_css': bool(presentation.custom_css),
            'has_latex_preamble': bool(
                presentation.custom_latex_preamble,
            ),
            'has_html_wrapper': bool(
                presentation.html_template_override,
            ),
            'has_latex_wrapper': bool(
                presentation.latex_template_override,
            ),
        }

    @staticmethod
    def _presentation_from_form(form):
        return DocumentPresentation(
            custom_css=form.cleaned_data.get('custom_css', ''),
            custom_latex_preamble=form.cleaned_data.get(
                'custom_latex_preamble',
                '',
            ),
            html_template_override=form.cleaned_data.get(
                'html_template_override',
                '',
            ),
            latex_template_override=form.cleaned_data.get(
                'latex_template_override',
                '',
            ),
        )

    @staticmethod
    def _document_type_url(document_type, request):
        params = []
        if document_type:
            params.append(('type', document_type))
        if request.renderable_only:
            params.append(('renderable', '1'))
        query = urlencode(params)
        return f'?{query}' if query else '?'
