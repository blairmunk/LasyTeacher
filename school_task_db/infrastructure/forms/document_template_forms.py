"""Infrastructure helpers for document template screens."""

from urllib.parse import urlencode

from core_logic.entities.document import CreateDocumentTemplateParams
from core_logic.use_cases.get_document_template_editor_data import (
    GetDocumentTemplateEditorDataRequest,
)
from core_logic.value_objects.document_render_options import FILE_TYPE_LABELS


class DocumentTemplateFormAdapter:
    def editor_data_request_from_query(self, query_data):
        return GetDocumentTemplateEditorDataRequest(
            document_type=query_data.get('type', ''),
            renderable_only=query_data.get('renderable') == '1',
            include_legacy_sections=query_data.get('legacy') == '1',
        )

    def editor_context(self, editor_data, request):
        return {
            'document_types': [
                self._document_type_context(document_type, request)
                for document_type in editor_data.document_types
            ],
            'sections': [
                self._section_context(section)
                for section in editor_data.sections
            ],
            'templates': [
                self._template_context(template)
                for template in editor_data.templates
            ],
            'current_document_type': request.document_type,
            'renderable_only': request.renderable_only,
            'include_legacy_sections': request.include_legacy_sections,
        }

    def create_params_from_form(self, form):
        return CreateDocumentTemplateParams(
            name=form.cleaned_data['name'],
            description=form.cleaned_data.get('description', ''),
            template_type=form.cleaned_data['template_type'],
            section_types=tuple(form.cleaned_data['sections']),
            is_default=form.cleaned_data.get('is_default', False),
        )

    def create_context(self, form, document_types, sections):
        return {
            'form': form,
            'document_types': document_types,
            'section_options': [
                self._section_context(section)
                for section in sections
            ],
            'selected_sections': set(
                form.data.getlist('sections')
                if form.is_bound
                else form.initial.get('sections', [])
            ),
            'selected_document_type': (
                form.data.get('template_type')
                if form.is_bound
                else form.initial.get('template_type', '')
            ),
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

    def _section_context(self, section):
        return {
            'section_type': section.section_type,
            'title': section.title,
            'description': section.description,
            'supported_document_types': section.supported_document_types,
            'renderable_document_types': section.renderable_document_types,
            'is_legacy': section.is_legacy,
        }

    def _template_context(self, template):
        return {
            'template_id': template.template_id,
            'name': template.name,
            'template_type': template.template_type,
            'section_types': template.section_types,
            'sections_count': len(template.sections),
            'default_content_config': template.default_content_config,
            'has_customization': template.presentation.has_customization,
        }

    def _document_type_url(self, document_type, request):
        params = []
        if document_type:
            params.append(('type', document_type))
        if request.renderable_only:
            params.append(('renderable', '1'))
        if request.include_legacy_sections:
            params.append(('legacy', '1'))

        query = urlencode(params)
        if not query:
            return '?'
        return f'?{query}'
