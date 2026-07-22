"""Infrastructure helpers for document template screens."""

import json
from urllib.parse import urlencode

from core_logic.entities.document import (
    CreateDocumentTemplateParams,
    DocumentSectionSpec,
    UpdateDocumentTemplateParams,
)
from core_logic.use_cases.get_document_template_editor_data import (
    GetDocumentTemplateEditorDataRequest,
)
from core_logic.value_objects.document_recipes import COMMON_HEADER_SECTION
from core_logic.value_objects.document_render_options import FILE_TYPE_LABELS
from infrastructure.forms.document_template_django_forms import (
    section_options_field_name,
)


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
            sections=self._section_specs_from_form(form),
            is_default=form.cleaned_data.get('is_default', False),
        )

    def update_params_from_form(self, form, template_id):
        return UpdateDocumentTemplateParams(
            template_id=template_id,
            name=form.cleaned_data['name'],
            description=form.cleaned_data.get('description', ''),
            template_type=form.cleaned_data['template_type'],
            sections=self._section_specs_from_form(form),
            is_default=form.cleaned_data.get('is_default', False),
        )

    def form_initial_from_template(self, template):
        return {
            'name': template.name,
            'description': template.description,
            'template_type': template.template_type,
            'sections': template.section_types,
            'section_order': ','.join(template.section_types),
            'section_options': {
                section.section_type: dict(section.options)
                for section in template.sections
                if section.options
            },
            'is_default': template.is_default,
        }

    def create_context(self, form, document_types, sections):
        section_options_by_type = self._section_options_by_type(form)
        return {
            'form': form,
            'document_types': document_types,
            'section_options': [
                {
                    **self._section_context(section),
                    'options_field_name': section_options_field_name(
                        section.section_type,
                    ),
                    'options_json': self._format_section_options_json(
                        section_options_by_type.get(section.section_type, {}),
                    ),
                }
                for section in sections
            ],
            'selected_sections': set(
                form.data.getlist('sections')
                if form.is_bound
                else form.initial.get('sections', [])
            ),
            'selected_section_order': self._selected_section_order(form),
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
            'is_fixed_order': section.section_type == COMMON_HEADER_SECTION,
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

    def _section_types_from_form(self, form):
        selected_sections = tuple(form.cleaned_data['sections'])
        ordered_sections = self._ordered_sections(
            selected_sections=selected_sections,
            section_order=form.cleaned_data.get('section_order', ''),
        )
        return tuple(ordered_sections)

    def _section_specs_from_form(self, form):
        section_options = form.cleaned_data.get('section_options', {})
        return tuple(
            DocumentSectionSpec(
                section_type=section_type,
                options=section_options.get(section_type, {}),
            )
            for section_type in self._section_types_from_form(form)
        )

    def _selected_section_order(self, form):
        selected_sections = (
            form.data.getlist('sections')
            if form.is_bound
            else list(form.initial.get('sections', []))
        )
        section_order = (
            form.data.get('section_order', '')
            if form.is_bound
            else form.initial.get('section_order', '')
        )
        return self._ordered_sections(
            selected_sections=selected_sections,
            section_order=section_order,
        )

    def _ordered_sections(self, selected_sections, section_order):
        selected = list(selected_sections)
        selected_set = set(selected)
        ordered = [
            section_type.strip()
            for section_type in section_order.split(',')
            if section_type.strip() in selected_set
        ]
        seen = set(ordered)
        ordered.extend(
            section_type
            for section_type in selected
            if section_type not in seen
        )
        return ordered

    def _section_options_by_type(self, form):
        if form.is_bound:
            return {
                section_type: form.data.get(
                    section_options_field_name(section_type),
                    '',
                )
                for section_type, _label in form.fields['sections'].choices
            }
        return form.initial.get('section_options', {})

    def _format_section_options_json(self, value):
        if not value:
            return ''
        if isinstance(value, str):
            return value
        return json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
