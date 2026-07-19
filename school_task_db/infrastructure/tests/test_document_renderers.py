from django.test import SimpleTestCase

from core_logic.entities.document import (
    Document,
    DocumentSection,
    DocumentSourceRef,
)
from core_logic.entities.document_generation import GeneratedDocument
from core_logic.value_objects.content_config import RenderTarget
from core_logic.value_objects.document_render_plan import DocumentRenderRequest
from infrastructure.services.document_renderers import LegacyDocumentRenderer


class LegacyDocumentRendererTests(SimpleTestCase):
    def test_renders_document_through_legacy_callbacks(self):
        calls = {}

        def get_source(source_id):
            calls['source_id'] = source_id
            return 'work-object'

        def render_files(source, content_config, render_target):
            calls['render'] = (source, content_config, render_target)
            return ['work.html']

        def document_from_paths(file_type, file_paths):
            calls['document'] = (file_type, file_paths)
            return GeneratedDocument(file_type=file_type)

        renderer = LegacyDocumentRenderer(
            file_type='html',
            source_getter=get_source,
            render_files=render_files,
            document_from_paths=document_from_paths,
        )
        request = DocumentRenderRequest(
            document=Document(
                title='Контрольная',
                document_type='work',
                source=DocumentSourceRef(source_type='work', source_id='work-1'),
                sections=[
                    DocumentSection(
                        section_type='task_variants',
                        payload={'include_hints': True},
                    ),
                    DocumentSection(section_type='answers'),
                ],
            ),
            render_target=RenderTarget(renderer_type='html', page_format='A5'),
        )

        result = renderer.render(request)

        self.assertEqual(result.file_type, 'html')
        self.assertEqual(calls['source_id'], 'work-1')
        self.assertEqual(
            calls['render'],
            (
                'work-object',
                {
                    'include_answers': True,
                    'include_short_solutions': False,
                    'include_full_solutions': False,
                    'answer_type': 'with_answers',
                    'include_hints': True,
                    'include_instructions': False,
                    'page_format': 'A5',
                },
                request.render_target,
            ),
        )
        self.assertEqual(calls['document'], ('html', ['work.html']))

    def test_rejects_document_without_source(self):
        renderer = LegacyDocumentRenderer(
            file_type='html',
            source_getter=lambda source_id: None,
            render_files=lambda source, content_config, render_target: [],
            document_from_paths=lambda file_type, file_paths: None,
        )

        with self.assertRaises(ValueError):
            renderer.render(
                DocumentRenderRequest(
                    document=Document(title='Без источника'),
                    render_target=RenderTarget(renderer_type='html'),
                )
            )
