from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import TestCase

from core_logic.entities.document import (
    DocumentRecipe,
    DocumentSectionSpec,
    DocumentSourceRef,
    DocumentTemplateSpec,
    WORK_SOURCE_TYPE,
)
from core_logic.entities.work import (
    RemedialOriginalTaskRow,
    RemedialSheetData,
    VariantDetailStudentRef,
)
from core_logic.value_objects.content_config import (
    RemedialSheetDocumentRenderOptions,
    RenderTarget,
    WorkDocumentRenderOptions,
)
from core_logic.value_objects.document_render_plan import (
    DocumentRenderPlan,
    build_remedial_sheet_document_render_plan,
    build_work_document_render_plan,
)
from core_logic.value_objects.document_recipes import (
    ANSWER_KEY_SECTION,
    TASK_LIST_SECTION,
)
from curriculum.models import Topic
from infrastructure.services.document_engine import DjangoDocumentEngine
from infrastructure.services.rendered_document_file_store import (
    RenderedDocumentFileStore,
)
from infrastructure.services.sectioned_document_defaults import (
    build_sectioned_document_components,
    build_sectioned_document_components_with_legacy_fallback,
    build_sectioned_html_document_components,
    build_sectioned_html_pdf_document_components,
    build_sectioned_remedial_sheet_html_document_components,
    build_sectioned_remedial_sheet_latex_document_components,
    build_sectioned_work_html_document_components,
    build_sectioned_work_latex_document_components,
    remedial_html_filename,
    remedial_latex_filename,
    work_html_filename,
    work_latex_filename,
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

    def test_work_html_supports_legacy_task_list_and_answer_key_sections(self):
        work = Work.objects.create(name='Контрольная', duration=45, max_score=4)
        variant = Variant.objects.create(
            work=work,
            number=1,
            work_name_snapshot=work.name,
            max_score_snapshot=4,
            duration_snapshot=45,
        )
        task = self.create_task(text='Найдите силу', answer='10 Н')
        VariantTask.objects.create(
            variant=variant,
            task=task,
            order=1,
            max_points=4,
        )

        with TemporaryDirectory() as output_dir:
            components = build_sectioned_work_html_document_components(
                file_store=RenderedDocumentFileStore(
                    output_dirs={'html': output_dir},
                ),
            )
            engine = DjangoDocumentEngine(
                document_builder=components.document_builder,
                document_renderer_registry=components.document_renderer_registry,
            )
            options = WorkDocumentRenderOptions(renderer_type='html')

            result = engine.render_work_document(
                work_id=str(work.pk),
                options=options,
                render_plan=build_work_document_render_plan(
                    work_id=str(work.pk),
                    work_name=work.name,
                    options=options,
                    template_spec=DocumentTemplateSpec(
                        name='Legacy work template',
                        template_type='work',
                        sections=[
                            DocumentSectionSpec(section_type=TASK_LIST_SECTION),
                            DocumentSectionSpec(section_type=ANSWER_KEY_SECTION),
                        ],
                    ),
                ),
            )

            filename = work_html_filename_from_id(work.pk)
            html = (Path(output_dir) / filename).read_text(encoding='utf-8')
            self.assertEqual(result.files[0].filename, filename)
            self.assertIn('Найдите силу', html)
            self.assertIn('Ответы', html)
            self.assertIn('10 Н', html)

    def test_builds_sectioned_work_latex_document_through_document_engine(self):
        work = Work.objects.create(name='Контрольная', duration=45, max_score=4)
        variant = Variant.objects.create(
            work=work,
            number=1,
            work_name_snapshot=work.name,
            max_score_snapshot=4,
            duration_snapshot=45,
        )
        task = self.create_task(
            text='Найдите силу & ускорение $F=ma$',
            answer='10 Н',
            short_solution='Используем $F=ma$',
            hint='масса & ускорение',
        )
        VariantTask.objects.create(
            variant=variant,
            task=task,
            order=1,
            max_points=4,
        )

        with TemporaryDirectory() as output_dir:
            components = build_sectioned_work_latex_document_components(
                file_store=RenderedDocumentFileStore(
                    output_dirs={'latex': output_dir},
                ),
            )
            engine = DjangoDocumentEngine(
                document_builder=components.document_builder,
                document_renderer_registry=components.document_renderer_registry,
            )
            options = WorkDocumentRenderOptions(
                renderer_type='latex',
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

            filename = work_latex_filename_from_id(work.pk)
            latex = (Path(output_dir) / filename).read_text(encoding='utf-8')
            self.assertEqual(result.file_type, 'latex')
            self.assertEqual(result.files[0].filename, filename)
            self.assertIn(r'\documentclass', latex)
            self.assertIn(r'\section*{ Вариант 1 }', latex)
            self.assertIn(r'Найдите силу \& ускорение \(F=ma\)', latex)
            self.assertIn(r'Подсказка: масса \& ускорение', latex)
            self.assertIn(r'Используем \(F=ma\)', latex)

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

    def test_builds_sectioned_remedial_latex_document_through_engine(self):
        remedial_variant = Variant.objects.create(
            work=None,
            number=1,
            variant_type='remedial',
        )
        source_work = Work.objects.create(name='Исходная работа')
        original_task = self.create_task(
            text='Ошибка & формула $F=ma$',
            answer='Ответ & исходный',
            short_solution='Разбор $F=ma$',
        )
        training_task = self.create_task(
            text='Тренировка & $a=F/m$',
            answer='Ответ тренировки',
            short_solution='Кратко $a=F/m$',
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
            components = build_sectioned_remedial_sheet_latex_document_components(
                file_store=RenderedDocumentFileStore(
                    output_dirs={'latex': output_dir},
                ),
                get_remedial_sheet_data=lambda variant_id: sheet_data,
            )
            engine = DjangoDocumentEngine(
                document_builder=components.document_builder,
                document_renderer_registry=components.document_renderer_registry,
            )
            options = RemedialSheetDocumentRenderOptions(
                renderer_type='latex',
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

            filename = remedial_latex_filename_from_id(remedial_variant.pk)
            latex = (Path(output_dir) / filename).read_text(encoding='utf-8')
            self.assertEqual(result.file_type, 'latex')
            self.assertEqual(result.files[0].filename, filename)
            self.assertIn(r'\documentclass', latex)
            self.assertIn('Работа над ошибками', latex)
            self.assertIn(r'Ошибка \& формула \(F=ma\)', latex)
            self.assertIn(r'Ответ \& исходный', latex)
            self.assertIn(r'Тренировка \& \(a=F/m\)', latex)
            self.assertIn(r'Кратко \(a=F/m\)', latex)

    def test_builds_combined_sectioned_html_components(self):
        with TemporaryDirectory() as output_dir:
            components = build_sectioned_html_document_components(
                file_store=RenderedDocumentFileStore(
                    output_dirs={'html': output_dir},
                ),
                get_work_source=lambda work_id: Work(
                    id=work_id,
                    name='Контрольная',
                    duration=45,
                    max_score=4,
                ),
                get_remedial_sheet_data=lambda variant_id: RemedialSheetData(
                    variant='variant',
                    student=None,
                    source_work=None,
                    mark=None,
                    new_tasks=[],
                ),
            )

            self.assertIsNotNone(
                components.document_renderer_registry.get(
                    'html',
                    document_type='work',
                )
            )
            self.assertIsNotNone(
                components.document_renderer_registry.get(
                    'html',
                    document_type='remedial_sheet',
                )
            )

    def test_builds_combined_sectioned_html_pdf_components(self):
        with TemporaryDirectory() as output_dir:
            components = build_sectioned_html_pdf_document_components(
                file_store=RenderedDocumentFileStore(
                    output_dirs={'html': output_dir, 'pdf': output_dir},
                ),
                get_work_source=lambda work_id: Work(
                    id=work_id,
                    name='Контрольная',
                    duration=45,
                    max_score=4,
                ),
                get_remedial_sheet_data=lambda variant_id: RemedialSheetData(
                    variant='variant',
                    student=None,
                    source_work=None,
                    mark=None,
                    new_tasks=[],
                ),
                pdf_generator_factory=lambda request: FakePdfGenerator(),
            )

            self.assertIsNotNone(
                components.document_renderer_registry.get(
                    'html',
                    document_type='work',
                )
            )
            self.assertIsNotNone(
                components.document_renderer_registry.get(
                    'pdf',
                    document_type='work',
                )
            )
            self.assertIsNotNone(
                components.document_renderer_registry.get(
                    'pdf',
                    document_type='remedial_sheet',
                )
            )

    def test_builds_combined_sectioned_document_components(self):
        with TemporaryDirectory() as output_dir:
            components = build_sectioned_document_components(
                file_store=RenderedDocumentFileStore(
                    output_dirs={
                        'html': output_dir,
                        'pdf': output_dir,
                        'latex': output_dir,
                    },
                ),
                get_work_source=lambda work_id: Work(
                    id=work_id,
                    name='Контрольная',
                    duration=45,
                    max_score=4,
                ),
                get_remedial_sheet_data=lambda variant_id: RemedialSheetData(
                    variant='variant',
                    student=None,
                    source_work=None,
                    mark=None,
                    new_tasks=[],
                ),
                pdf_generator_factory=lambda request: FakePdfGenerator(),
            )

            self.assertIsNotNone(
                components.document_renderer_registry.get(
                    'latex',
                    document_type='work',
                )
            )
            self.assertIsNotNone(
                components.document_renderer_registry.get(
                    'latex',
                    document_type='remedial_sheet',
                )
            )

    def test_builds_sectioned_components_with_legacy_fallback(self):
        legacy_file_renderer = FakeLegacyFileRenderer()
        pdf_generator = FakePdfGenerator()
        with TemporaryDirectory() as output_dir:
            components = build_sectioned_document_components_with_legacy_fallback(
                file_store=RenderedDocumentFileStore(
                    output_dirs={
                        'html': output_dir,
                        'pdf': output_dir,
                        'latex': output_dir,
                    },
                ),
                get_work_source=lambda work_id: 'work-object',
                get_remedial_source=lambda variant_id: 'variant-object',
                legacy_file_renderer=legacy_file_renderer,
                pdf_generator_factory=lambda request: pdf_generator,
                get_remedial_sheet_data=lambda variant_id: RemedialSheetData(
                    variant='variant',
                    student=None,
                    source_work=None,
                    mark=None,
                    new_tasks=[],
                ),
            )
            engine = DjangoDocumentEngine(
                document_builder=components.document_builder,
                document_renderer_registry=components.document_renderer_registry,
            )
            html_options = WorkDocumentRenderOptions(renderer_type='html')
            pdf_options = WorkDocumentRenderOptions(renderer_type='pdf')
            latex_options = WorkDocumentRenderOptions(renderer_type='latex')

            html_result = engine.render_work_document(
                work_id='work-1',
                options=html_options,
                render_plan=empty_work_render_plan('html'),
            )
            pdf_result = engine.render_work_document(
                work_id='work-1',
                options=pdf_options,
                render_plan=empty_work_render_plan('pdf'),
            )
            latex_result = engine.render_work_document(
                work_id='work-1',
                options=latex_options,
                render_plan=empty_work_render_plan('latex'),
            )

        self.assertEqual(html_result.file_type, 'html')
        self.assertEqual(pdf_result.file_type, 'pdf')
        self.assertEqual(latex_result.file_type, 'latex')
        self.assertEqual(legacy_file_renderer.pdf_work_requests, [])
        self.assertEqual(legacy_file_renderer.latex_work_requests, [])
        self.assertIn('<title>Контрольная</title>', pdf_generator.html_content)

    def test_work_html_filename_uses_source_id(self):
        request = FakeRenderRequest(source_id='work-1')

        self.assertEqual(work_html_filename(request), 'work_work-1.html')

    def test_work_html_filename_uses_fallback_without_source_id(self):
        request = FakeRenderRequest(source_id='')

        self.assertEqual(work_html_filename(request), 'work.html')

    def test_work_latex_filename_uses_source_id(self):
        request = FakeRenderRequest(source_id='work-1')

        self.assertEqual(work_latex_filename(request), 'work_work-1.tex')

    def test_remedial_html_filename_uses_source_id(self):
        request = FakeRenderRequest(source_id='variant-1')

        self.assertEqual(
            remedial_html_filename(request),
            'remedial_variant-1.html',
        )

    def test_remedial_html_filename_uses_fallback_without_source_id(self):
        request = FakeRenderRequest(source_id='')

        self.assertEqual(remedial_html_filename(request), 'remedial.html')

    def test_remedial_latex_filename_uses_source_id(self):
        request = FakeRenderRequest(source_id='variant-1')

        self.assertEqual(
            remedial_latex_filename(request),
            'remedial_variant-1.tex',
        )

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


def work_latex_filename_from_id(work_id):
    return f'work_{work_id}.tex'


def remedial_html_filename_from_id(variant_id):
    return f'remedial_{variant_id}.html'


def remedial_latex_filename_from_id(variant_id):
    return f'remedial_{variant_id}.tex'


def empty_work_render_plan(renderer_type):
    return DocumentRenderPlan(
        source=DocumentSourceRef(
            source_type=WORK_SOURCE_TYPE,
            source_id='work-1',
            title='Контрольная',
        ),
        recipe=DocumentRecipe(document_type='work'),
        render_target=RenderTarget(renderer_type=renderer_type),
    )


class FakeMark:
    def __init__(self, score, points, max_points):
        self.score = score
        self.points = points
        self.max_points = max_points


class FakeLegacyFileRenderer:
    def __init__(self):
        self.latex_work_requests = []
        self.pdf_work_requests = []

    def render_latex_work(self, work, content_config, page_format='A4'):
        self.latex_work_requests.append((work,))
        return []

    def render_html_work(self, work, content_config):
        raise AssertionError('legacy HTML work renderer should not be used')

    def render_pdf_work(self, work, content_config, page_format='A4'):
        self.pdf_work_requests.append((work,))
        return []

    def render_remedial_latex(self, variant, content_config, page_format='A4'):
        return []

    def render_remedial_html(self, variant, content_config):
        raise AssertionError('legacy HTML remedial renderer should not be used')

    def render_remedial_pdf(self, variant, content_config, page_format='A4'):
        return []


class FakePdfGenerator:
    def __init__(self):
        self.html_content = ''

    def generate_pdf(self, html_path, pdf_path):
        self.html_content = html_path.read_text(encoding='utf-8')
        pdf_path.write_bytes(b'pdf')
        return pdf_path
