"""Infrastructure helpers for document presentation profile screens."""

from urllib.parse import urlencode

from core_logic.entities.document import (
    CreatePresentationProfileParams,
    DocumentPresentation,
    UpdatePresentationProfileParams,
)
from core_logic.use_cases.get_presentation_profile_editor_data import (
    GetPresentationProfileEditorDataRequest,
)
from core_logic.value_objects.document_render_options import FILE_TYPE_LABELS


class PresentationProfileFormAdapter:
    def editor_data_request_from_query(self, query_data):
        return GetPresentationProfileEditorDataRequest(
            document_type=query_data.get('type', ''),
            renderable_only=query_data.get('renderable', '1') == '1',
        )

    def editor_context(self, editor_data, request):
        return {
            'document_types': [
                self._document_type_context(document_type, request)
                for document_type in editor_data.document_types
            ],
            'presentation_profiles': [
                self._presentation_profile_context(presentation_profile)
                for presentation_profile in editor_data.presentation_profiles
            ],
            'current_document_type': request.document_type,
            'renderable_only': request.renderable_only,
        }

    def create_presentation_profile_params_from_form(self, form):
        return CreatePresentationProfileParams(
            name=form.cleaned_data['name'],
            description=form.cleaned_data.get('description', ''),
            document_type=form.cleaned_data['document_type'],
            is_default=form.cleaned_data.get('is_default', False),
            presentation=self._presentation_from_form(form),
        )

    def update_presentation_profile_params_from_form(
        self,
        form,
        presentation_profile_id,
    ):
        return UpdatePresentationProfileParams(
            presentation_profile_id=presentation_profile_id,
            name=form.cleaned_data['name'],
            description=form.cleaned_data.get('description', ''),
            document_type=form.cleaned_data['document_type'],
            is_default=form.cleaned_data.get('is_default', False),
            presentation=self._presentation_from_form(form),
        )

    def form_initial_from_profile(self, presentation_profile):
        return {
            'name': presentation_profile.name,
            'description': presentation_profile.description,
            'document_type': presentation_profile.document_type,
            'custom_css': presentation_profile.presentation.custom_css,
            'custom_latex_preamble': (
                presentation_profile.presentation.custom_latex_preamble
            ),
            'html_template_override': (
                presentation_profile.presentation.html_template_override
            ),
            'latex_template_override': (
                presentation_profile.presentation.latex_template_override
            ),
            'is_default': presentation_profile.is_default,
        }

    @staticmethod
    def create_context(form, document_types):
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
    def _presentation_profile_context(presentation_profile):
        presentation = presentation_profile.presentation
        return {
            'presentation_profile_id': presentation_profile.presentation_profile_id,
            'name': presentation_profile.name,
            'description': presentation_profile.description,
            'document_type': presentation_profile.document_type,
            'is_default': presentation_profile.is_default,
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
