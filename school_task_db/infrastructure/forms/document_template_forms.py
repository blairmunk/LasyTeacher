"""Infrastructure helpers for document template screens."""

from core_logic.use_cases.get_document_template_editor_data import (
    GetDocumentTemplateEditorDataRequest,
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
                self._document_type_context(document_type)
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

    def _document_type_context(self, document_type):
        return {
            'document_type': document_type.document_type,
            'title': document_type.title,
            'description': document_type.description,
            'source_type': document_type.source_type,
            'is_renderable': document_type.is_renderable,
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
            'name': template.name,
            'template_type': template.template_type,
            'section_types': template.section_types,
            'sections_count': len(template.sections),
            'default_content_config': template.default_content_config,
        }
