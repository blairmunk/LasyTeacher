from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import TestCase

from core_logic.entities.work import (
    RemedialOriginalTaskRow,
    RemedialSheetData,
    VariantDetailStudentRef,
)
from core_logic.value_objects.content_config import (
    RemedialSheetDocumentRenderOptions,
    WorkDocumentRenderOptions,
)
from core_logic.value_objects.document_render_plan import (
    build_remedial_sheet_document_render_plan,
    build_work_document_render_plan,
)
from curriculum.models import Topic
from infrastructure.services.document_engine import DjangoDocumentEngine
from infrastructure.services.rendered_document_file_store import (
    RenderedDocumentFileStore,
)
from infrastructure.services.sectioned_document_defaults import (
    build_sectioned_remedial_sheet_html_document_components,
    build_sectioned_work_html_document_components,
    remedial_html_filename,
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
            short_solution='Кратко: F = ma',
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
                answer_type='with_short_solutions',
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
            self.assertIn('Ответы', html)
            self.assertIn('10 Н', html)
            self.assertIn('Краткие решения', html)
            self.assertIn('Кратко: F = ma', html)

    def test_builds_sectioned_remedial_html_document_through_engine(self):
        remedial_variant = Variant.objects.create(
            work=None,
            number=1,
            variant_type='remedial',
        )
        source_work = Work.objects.create(name='Исходная работа')
        original_task = self.create_task(
            text='Исходное задание',
            answer='Исходный ответ',
            short_solution='Разбор исходного задания',
        )
        training_task = self.create_task(
            text='Тренировочное задание',
            answer='Тренировочный ответ',
            short_solution='Краткое решение тренировки',
        )
        training_variant_task = VariantTask.objects.create(
            variant=remedial_variant,
            task=training_task,
            order=1,
            max_points=2,
        )
        sheet_data = RemedialSheetData(
            variant=remedial_variant,
            student=VariantDetailStudentRef(
                pk='student-1',
                full_name='Петров Пётр',
                short_name='Петров П.',
            ),
            source_work=source_work,
            mark=FakeMark(score=3, points=2, max_points=5),
            original_tasks=[
                RemedialOriginalTaskRow(
                    task=original_task,
                    order=1,
                    points=2,
                    max_points=5,
                    pct=40.0,
                    status='partial',
                    group_name='Динамика',
                ),
            ],
            new_tasks=[training_variant_task],
        )

        with TemporaryDirectory() as output_dir:
            file_store = RenderedDocumentFileStore(
                output_dirs={'html': output_dir},
            )
            components = build_sectioned_remedial_sheet_html_document_components(
                file_store=file_store,
                get_remedial_sheet_data=lambda variant_id: sheet_data,
            )
            engine = DjangoDocumentEngine(
                document_builder=components.document_builder,
                document_renderer_registry=components.document_renderer_registry,
            )
            options = RemedialSheetDocumentRenderOptions(
                renderer_type='html',
                answer_type='with_short_solutions',
            )

            result = engine.render_remedial_sheet_document(
                variant_id=str(remedial_variant.pk),
                options=options,
                render_plan=build_remedial_sheet_document_render_plan(
                    variant_id=str(remedial_variant.pk),
                    options=options,
                ),
            )

            filename = remedial_html_filename_from_id(remedial_variant.pk)
            html = (Path(output_dir) / filename).read_text(encoding='utf-8')
            self.assertEqual(result.file_type, 'html')
            self.assertEqual(result.files[0].filename, filename)
            self.assertIn('Работа над ошибками', html)
            self.assertIn('Петров Пётр', html)
            self.assertIn('Исходная работа', html)
            self.assertIn('Исходное задание', html)
            self.assertIn('Разбор исходного задания', html)
            self.assertIn('Тренировочное задание', html)
            self.assertIn('Тренировочный ответ', html)
            self.assertIn('Краткое решение тренировки', html)

    def test_work_html_filename_uses_source_id(self):
        request = FakeRenderRequest(source_id='work-1')

        self.assertEqual(work_html_filename(request), 'work_work-1.html')

    def test_work_html_filename_uses_fallback_without_source_id(self):
        request = FakeRenderRequest(source_id='')

        self.assertEqual(work_html_filename(request), 'work.html')

    def test_remedial_html_filename_uses_source_id(self):
        request = FakeRenderRequest(source_id='variant-1')

        self.assertEqual(
            remedial_html_filename(request),
            'remedial_variant-1.html',
        )

    def test_remedial_html_filename_uses_fallback_without_source_id(self):
        request = FakeRenderRequest(source_id='')

        self.assertEqual(remedial_html_filename(request), 'remedial.html')

    def create_task(self, **overrides):
        topic = Topic.objects.create(
            name=f"Тема {overrides.get('text', '')}",
            subject='Физика',
            section='Механика',
            grade_level=9,
        )
        defaults = {
            'text': 'Задание',
            'answer': 'Ответ',
            'topic': topic,
            'task_type': 'computational',
            'difficulty': 2,
        }
        defaults.update(overrides)
        return Task.objects.create(**defaults)


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


def remedial_html_filename_from_id(variant_id):
    return f'remedial_{variant_id}.html'


class FakeMark:
    def __init__(self, score, points, max_points):
        self.score = score
        self.points = points
        self.max_points = max_points
