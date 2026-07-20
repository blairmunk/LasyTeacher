from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import TestCase

from core_logic.value_objects.content_config import WorkDocumentRenderOptions
from core_logic.value_objects.document_render_plan import (
    build_work_document_render_plan,
)
from curriculum.models import Topic
from infrastructure.services.document_engine import DjangoDocumentEngine
from infrastructure.services.rendered_document_file_store import (
    RenderedDocumentFileStore,
)
from infrastructure.services.sectioned_document_defaults import (
    build_sectioned_work_html_document_components,
    work_html_filename,
)
from tasks.models import Task
from works.models import Variant, VariantTask, Work


class SectionedDocumentDefaultsTests(TestCase):
    def test_builds_sectioned_work_html_document_through_document_engine(self):
        work = Work.objects.create(name='Контрольная', duration=45, max_score=4)
        variant = Variant.objects.create(
            work=work,
            number=1,
            work_name_snapshot=work.name,
            max_score_snapshot=4,
            duration_snapshot=45,
        )
        topic = Topic.objects.create(
            name='Динамика',
            subject='Физика',
            section='Механика',
            grade_level=9,
        )
        task = Task.objects.create(
            text='Найдите силу',
            answer='10 Н',
            hint='F = ma',
            topic=topic,
            task_type='computational',
            difficulty=3,
        )
        VariantTask.objects.create(
            variant=variant,
            task=task,
            order=1,
            max_points=4,
        )

        with TemporaryDirectory() as output_dir:
            file_store = RenderedDocumentFileStore(
                output_dirs={'html': output_dir},
            )
            components = build_sectioned_work_html_document_components(
                file_store=file_store,
            )
            engine = DjangoDocumentEngine(
                document_builder=components.document_builder,
                document_renderer_registry=components.document_renderer_registry,
            )
            options = WorkDocumentRenderOptions(
                renderer_type='html',
                include_hints=True,
            )

            result = engine.render_work_document(
                work_id=str(work.pk),
                options=options,
                render_plan=build_work_document_render_plan(
                    work_id=str(work.pk),
                    work_name=work.name,
                    options=options,
                ),
            )

            filename = work_html_filename_from_id(work.pk)
            html = (Path(output_dir) / filename).read_text(encoding='utf-8')
            self.assertEqual(result.file_type, 'html')
            self.assertEqual(result.files[0].filename, filename)
            self.assertIn('<h1>Контрольная</h1>', html)
            self.assertIn('Вариант 1', html)
            self.assertIn('Найдите силу', html)
            self.assertIn('Подсказка: F = ma', html)

    def test_work_html_filename_uses_source_id(self):
        request = FakeRenderRequest(source_id='work-1')

        self.assertEqual(work_html_filename(request), 'work_work-1.html')

    def test_work_html_filename_uses_fallback_without_source_id(self):
        request = FakeRenderRequest(source_id='')

        self.assertEqual(work_html_filename(request), 'work.html')


class FakeRenderRequest:
    def __init__(self, source_id):
        self.document = FakeDocument(source_id)


class FakeDocument:
    def __init__(self, source_id):
        self.source = FakeSource(source_id)


class FakeSource:
    def __init__(self, source_id):
        self.source_id = source_id


def work_html_filename_from_id(work_id):
    return f'work_{work_id}.html'
