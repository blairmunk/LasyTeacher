from django.test import SimpleTestCase

from core_logic.entities.document import Document, DocumentSection
from core_logic.entities.document_rendering import GeneratedDocument
from core_logic.value_objects.content_config import RenderTarget
from core_logic.value_objects.document_render_plan import (
    DocumentRenderRequest,
)
from infrastructure.services.sectioned_document_renderer_factory import (
    TemplateSectionedTextDocumentRendererSpec,
    build_sectioned_text_document_renderer,
    build_template_sectioned_text_document_renderer,
    build_template_sectioned_text_document_renderer_registry,
)


class SectionedDocumentRendererFactoryTests(SimpleTestCase):
    def test_builds_renderer_from_section_registry(self):
        section_registry = FakeSectionRendererRegistry()
        file_store = FakeFileStore()
        renderer = build_sectioned_text_document_renderer(
            renderer_type='html',
            section_renderer_registry=section_registry,
            filename_builder=lambda request: 'work.html',
            file_store=file_store,
            section_separator='\n\n',
        )
        request = DocumentRenderRequest(
            document=Document(
                title='Контрольная',
                sections=[
                    DocumentSection(section_type='header'),
                    DocumentSection(section_type='tasks'),
                ],
            ),
            render_target=RenderTarget(renderer_type='html'),
        )

        result = renderer.render(request)

        self.assertEqual(result.file_type, 'html')
        self.assertEqual(
            file_store.request,
            ('html', 'work.html', '<html:header>\n\n<html:tasks>'),
        )

    def test_builds_renderer_from_section_templates(self):
        template_calls = []

        def template_renderer(template_name, context):
            template_calls.append((template_name, context))
            return f'<section>{template_name}</section>'

        file_store = FakeFileStore()
        renderer = build_template_sectioned_text_document_renderer(
            renderer_type='html',
            section_templates={
                'header': 'documents/html/header.html',
                'tasks': 'documents/html/tasks.html',
            },
            filename_builder=lambda request: 'work.html',
            file_store=file_store,
            template_renderer=template_renderer,
        )
        document = Document(
            title='Контрольная',
            sections=[
                DocumentSection(section_type='header'),
                DocumentSection(section_type='tasks'),
            ],
        )

        renderer.render(
            DocumentRenderRequest(
                document=document,
                render_target=RenderTarget(renderer_type='html'),
            )
        )

        self.assertEqual(
            file_store.request,
            (
                'html',
                'work.html',
                (
                    '<section>documents/html/header.html</section>\n'
                    '<section>documents/html/tasks.html</section>'
                ),
            ),
        )
        self.assertEqual(
            [template_name for template_name, _ in template_calls],
            ['documents/html/header.html', 'documents/html/tasks.html'],
        )

    def test_builds_renderer_registry_from_template_specs(self):
        file_store = FakeFileStore()
        registry = build_template_sectioned_text_document_renderer_registry(
            renderer_type='html',
            renderer_specs=[
                TemplateSectionedTextDocumentRendererSpec(
                    document_type='work',
                    section_templates={
                        'tasks': 'documents/html/work_tasks.html',
                    },
                    filename_builder=lambda request: 'work.html',
                ),
                TemplateSectionedTextDocumentRendererSpec(
                    document_type='remedial_sheet',
                    section_templates={
                        'tasks': 'documents/html/remedial_tasks.html',
                    },
                    filename_builder=lambda request: 'remedial.html',
                    section_separator='\n\n',
                ),
            ],
            file_store=file_store,
            template_renderer=(
                lambda template_name, context:
                    f'<section>{template_name}</section>'
            ),
        )

        registry.render(
            DocumentRenderRequest(
                document=Document(
                    title='Контрольная',
                    document_type='work',
                    sections=[DocumentSection(section_type='tasks')],
                ),
                render_target=RenderTarget(renderer_type='html'),
            )
        )
        registry.render(
            DocumentRenderRequest(
                document=Document(
                    title='Разбор',
                    document_type='remedial_sheet',
                    sections=[DocumentSection(section_type='tasks')],
                ),
                render_target=RenderTarget(renderer_type='html'),
            )
        )

        self.assertEqual(
            file_store.requests,
            [
                (
                    'html',
                    'work.html',
                    '<section>documents/html/work_tasks.html</section>',
                ),
                (
                    'html',
                    'remedial.html',
                    '<section>documents/html/remedial_tasks.html</section>',
                ),
            ],
        )

    def test_renderer_spec_rejects_empty_document_type(self):
        with self.assertRaises(ValueError):
            TemplateSectionedTextDocumentRendererSpec(
                document_type='',
                section_templates={},
                filename_builder=lambda request: 'work.html',
            )

    def test_rejects_empty_renderer_type(self):
        with self.assertRaises(ValueError):
            build_sectioned_text_document_renderer(
                renderer_type='',
                section_renderer_registry=FakeSectionRendererRegistry(),
                filename_builder=lambda request: 'work.html',
                file_store=FakeFileStore(),
            )


class FakeSectionRendererRegistry:
    def render_section(self, request):
        return (
            f'<{request.render_target.renderer_type}:'
            f'{request.section.section_type}>'
        )


class FakeFileStore:
    def __init__(self):
        self.request = None
        self.requests = []

    def write_text_document(self, file_type, filename, content):
        self.request = (file_type, filename, content)
        self.requests.append(self.request)
        return GeneratedDocument(file_type=file_type)
