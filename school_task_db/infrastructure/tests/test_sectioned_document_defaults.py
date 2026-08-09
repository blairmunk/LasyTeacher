from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from django.test import TestCase

from infrastructure.tests.variant_task_factory import create_variant_task

from core_logic.entities.document import (
    DocumentPresentation,
    DocumentRecipe,
    DocumentSectionSpec,
    DocumentSourceRef,
    DocumentPresentationProfile,
    EVENT_REPORT_SOURCE_TYPE,
    REMEDIAL_VARIANT_SOURCE_TYPE,
    STUDENT_DIGEST_SOURCE_TYPE,
    WORK_SOURCE_TYPE,
)
from core_logic.entities.work import (
    RemedialContentBlockRow,
    RemedialOriginalTaskRow,
    RemedialSheetData,
    VariantDetailStudentRef,
)
from core_logic.entities.work_document import WorkDocumentSource
from core_logic.services.document_builder import (
    UnsupportedDocumentSectionPayloadBuilder,
)
from core_logic.value_objects.document_render_options import (
    RemedialSheetPrintOptions,
    RenderTarget,
    WorkDocumentPrintOverrides,
)
from core_logic.value_objects.document_build_plan import (
    DocumentSectionPayloadBuildRequest,
)
from core_logic.value_objects.document_render_plan import DocumentRenderPlan
from core_logic.value_objects.document_render_recipe_factories import (
    build_remedial_sheet_document_recipe_for_render,
    build_work_document_recipe_for_render,
)
from core_logic.value_objects.document_source_factories import (
    build_remedial_sheet_document_source,
    build_work_document_source,
)
from core_logic.value_objects.document_recipes import (
    EVENT_PERFORMANCE_REPORT_DOCUMENT_TYPE,
    HEADER_SECTION,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    STUDENT_DIGEST_DOCUMENT_TYPE,
    WORK_DOCUMENT_TYPE,
)
from curriculum.models import Topic
from infrastructure.repositories.django_work_document_repo import (
    DjangoWorkDocumentRepository,
)
from infrastructure.services.document_engine import DjangoDocumentEngine
from infrastructure.services.rendered_document_file_store import (
    RenderedDocumentFileStore,
)
from infrastructure.services.sectioned_document_defaults import (
    build_sectioned_document_components,
    build_sectioned_document_payload_builder_registry,
    build_sectioned_html_document_components,
    build_sectioned_html_pdf_document_components,
)
from infrastructure.services.sectioned_document_filenames import (
    remedial_html_filename,
    remedial_latex_filename,
    work_html_filename,
    work_latex_filename,
)
from tasks.models import Task
from works.models import (
    Variant,
    VariantContentBlockSnapshot,
    Work,
)


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
        create_variant_task(
            variant=variant,
            task=task,
            order=1,
            max_points=4,
        )

        with TemporaryDirectory() as output_dir:
            file_store = RenderedDocumentFileStore(
                output_dirs={'html': output_dir},
            )
            components = build_sectioned_document_components(
                file_store=file_store,
                work_document_repo=DjangoWorkDocumentRepository(),
            )
            engine = DjangoDocumentEngine(
                document_builder=components.document_builder,
                document_renderer_registry=components.document_renderer_registry,
            )
            print_overrides = WorkDocumentPrintOverrides(
                append_answers=True,
            )
            presentation_profile = DocumentPresentationProfile(
                name='Профиль оформления',
                document_type=WORK_DOCUMENT_TYPE,
                presentation=DocumentPresentation(
                    custom_css='.task-item { margin-bottom: 1rem; }',
                ),
            )

            result = engine.render_document(
                _work_document_render_plan(
                    work_id=str(work.pk),
                    work_name=work.name,
                    renderer_type='html',
                    print_overrides=print_overrides,
                    presentation_profile=presentation_profile,
                ),
            )

            filename = work_html_filename_from_id(work.pk)
            html = (Path(output_dir) / filename).read_text(encoding='utf-8')
            self.assertEqual(result.file_type, 'html')
            self.assertEqual(result.files[0].filename, filename)
            self.assertIn('<h1>Контрольная</h1>', html)
            self.assertIn('Вариант 1', html)
            self.assertIn('Найдите силу', html)
            self.assertIn('Ответы', html)
            self.assertIn('10 Н', html)
            self.assertIn('.task-item { margin-bottom: 1rem; }', html)

    def test_work_html_can_render_sections_per_variant(self):
        work = Work.objects.create(name='Контрольная', duration=45, max_score=4)
        first_variant = Variant.objects.create(
            work=work,
            number=1,
            work_name_snapshot=work.name,
            max_score_snapshot=4,
            duration_snapshot=45,
        )
        second_variant = Variant.objects.create(
            work=work,
            number=2,
            work_name_snapshot=work.name,
            max_score_snapshot=4,
            duration_snapshot=45,
        )
        first_task = self.create_task(text='Первое задание', answer='1')
        second_task = self.create_task(text='Второе задание', answer='2')
        create_variant_task(
            variant=first_variant,
            task=first_task,
            order=1,
            max_points=4,
        )
        create_variant_task(
            variant=second_variant,
            task=second_task,
            order=1,
            max_points=4,
        )

        with TemporaryDirectory() as output_dir:
            components = build_sectioned_document_components(
                file_store=RenderedDocumentFileStore(
                    output_dirs={'html': output_dir},
                ),
                work_document_repo=DjangoWorkDocumentRepository(),
            )
            engine = DjangoDocumentEngine(
                document_builder=components.document_builder,
                document_renderer_registry=components.document_renderer_registry,
            )

            result = engine.render_document(
                _work_document_render_plan(
                    work_id=str(work.pk),
                    work_name=work.name,
                    renderer_type='html',
                    variant_ids=[
                        str(first_variant.pk),
                        str(second_variant.pk),
                    ],
                ),
            )

            filename = work_html_filename_from_id(work.pk)
            html = (Path(output_dir) / filename).read_text(encoding='utf-8')
            self.assertEqual(result.files[0].filename, filename)
            self.assertIn('<h1>Контрольная. Вариант 1</h1>', html)
            self.assertIn('<h1>Контрольная. Вариант 2</h1>', html)
            self.assertIn('Первое задание', html)
            self.assertIn('Второе задание', html)
            self.assertIn('page-break-after: always', html)

    def test_work_html_supports_task_list_and_answers_sections(self):
        work = Work.objects.create(name='Контрольная', duration=45, max_score=4)
        variant = Variant.objects.create(
            work=work,
            number=1,
            work_name_snapshot=work.name,
            max_score_snapshot=4,
            duration_snapshot=45,
        )
        task = self.create_task(text='Найдите силу', answer='10 Н')
        create_variant_task(
            variant=variant,
            task=task,
            order=1,
            max_points=4,
        )

        with TemporaryDirectory() as output_dir:
            components = build_sectioned_document_components(
                file_store=RenderedDocumentFileStore(
                    output_dirs={'html': output_dir},
                ),
                work_document_repo=DjangoWorkDocumentRepository(),
            )
            engine = DjangoDocumentEngine(
                document_builder=components.document_builder,
                document_renderer_registry=components.document_renderer_registry,
            )
            print_overrides = WorkDocumentPrintOverrides(
                append_answers=True,
            )

            result = engine.render_document(
                _work_document_render_plan(
                    work_id=str(work.pk),
                    work_name=work.name,
                    renderer_type='html',
                    print_overrides=print_overrides,
                ),
            )

            filename = work_html_filename_from_id(work.pk)
            html = (Path(output_dir) / filename).read_text(encoding='utf-8')
            self.assertEqual(result.files[0].filename, filename)
            self.assertIn('Найдите силу', html)
            self.assertIn('Ответы', html)
            self.assertIn('10 Н', html)

    def test_work_html_supports_legacy_answer_key_section(self):
        work = Work.objects.create(name='Контрольная', duration=45, max_score=4)
        variant = Variant.objects.create(
            work=work,
            number=1,
            work_name_snapshot=work.name,
            max_score_snapshot=4,
            duration_snapshot=45,
        )
        task = self.create_task(text='Найдите силу', answer='10 Н')
        create_variant_task(
            variant=variant,
            task=task,
            order=1,
            max_points=4,
        )

        with TemporaryDirectory() as output_dir:
            components = build_sectioned_document_components(
                file_store=RenderedDocumentFileStore(
                    output_dirs={'html': output_dir},
                ),
                work_document_repo=DjangoWorkDocumentRepository(),
            )
            engine = DjangoDocumentEngine(
                document_builder=components.document_builder,
                document_renderer_registry=components.document_renderer_registry,
            )
            print_overrides = WorkDocumentPrintOverrides(
                append_answers=True,
            )

            result = engine.render_document(
                _work_document_render_plan(
                    work_id=str(work.pk),
                    work_name=work.name,
                    renderer_type='html',
                    print_overrides=print_overrides,
                ),
            )

            filename = work_html_filename_from_id(work.pk)
            html = (Path(output_dir) / filename).read_text(encoding='utf-8')
            self.assertEqual(result.files[0].filename, filename)
            self.assertIn('Ответы', html)
            self.assertIn('10 Н', html)

    def test_work_html_renders_theory_from_variant_content_snapshot(self):
        work = Work.objects.create(name='Контрольная', duration=45, max_score=4)
        variant = Variant.objects.create(
            work=work,
            number=1,
            work_name_snapshot=work.name,
            max_score_snapshot=4,
            duration_snapshot=45,
        )
        VariantContentBlockSnapshot.objects.create(
            variant=variant,
            content_type='theory',
            order=1,
            title='Теоретическая справка',
            content={
                'topics': [
                    {
                        'name': 'Динамика',
                        'content': (
                            'Сила равна произведению массы на ускорение.'
                        ),
                        'subtopics': [],
                    },
                ],
            },
        )

        with TemporaryDirectory() as output_dir:
            components = build_sectioned_document_components(
                file_store=RenderedDocumentFileStore(
                    output_dirs={'html': output_dir},
                ),
                work_document_repo=DjangoWorkDocumentRepository(),
            )
            engine = DjangoDocumentEngine(
                document_builder=components.document_builder,
                document_renderer_registry=components.document_renderer_registry,
            )

            result = engine.render_document(
                _work_document_render_plan(
                    work_id=str(work.pk),
                    work_name=work.name,
                    renderer_type='html',
                ),
            )

            filename = work_html_filename_from_id(work.pk)
            html = (Path(output_dir) / filename).read_text(encoding='utf-8')
            self.assertEqual(result.files[0].filename, filename)
            self.assertIn('Теоретическая справка', html)
            self.assertIn('Динамика', html)
            self.assertIn('Сила равна произведению массы на ускорение.', html)

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
        create_variant_task(
            variant=variant,
            task=task,
            order=1,
            max_points=4,
        )

        with TemporaryDirectory() as output_dir:
            components = build_sectioned_document_components(
                file_store=RenderedDocumentFileStore(
                    output_dirs={'latex': output_dir},
                ),
                work_document_repo=DjangoWorkDocumentRepository(),
            )
            engine = DjangoDocumentEngine(
                document_builder=components.document_builder,
                document_renderer_registry=components.document_renderer_registry,
            )
            presentation_profile = DocumentPresentationProfile(
                name='Профиль оформления',
                document_type=WORK_DOCUMENT_TYPE,
                presentation=DocumentPresentation(
                    custom_latex_preamble='\\renewcommand{\\familydefault}{\\sfdefault}',
                ),
            )

            result = engine.render_document(
                _work_document_render_plan(
                    work_id=str(work.pk),
                    work_name=work.name,
                    renderer_type='latex',
                    presentation_profile=presentation_profile,
                ),
            )

            filename = work_latex_filename_from_id(work.pk)
            latex = (Path(output_dir) / filename).read_text(encoding='utf-8')
            self.assertEqual(result.file_type, 'latex')
            self.assertEqual(result.files[0].filename, filename)
            self.assertIn(r'\documentclass', latex)
            self.assertIn(r'\schoolvariantheading{ Вариант 1 }', latex)
            self.assertIn(r'Найдите силу \& ускорение \(F=ma\)', latex)
            self.assertIn(
                r'\renewcommand{\familydefault}{\sfdefault}',
                latex,
            )

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
        training_variant_task = create_variant_task(
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
            content_blocks=[
                RemedialContentBlockRow(
                    pk='content-1',
                    source_content_id='source-content-1',
                    content_type='text',
                    order=0,
                    title='Памятка',
                    content={'body': 'Сначала вспомните формулу $F=ma$.'},
                ),
            ],
        )

        with TemporaryDirectory() as output_dir:
            file_store = RenderedDocumentFileStore(
                output_dirs={'html': output_dir},
            )
            components = build_sectioned_document_components(
                file_store=file_store,
                get_remedial_sheet_data=lambda variant_id: sheet_data,
            )
            engine = DjangoDocumentEngine(
                document_builder=components.document_builder,
                document_renderer_registry=components.document_renderer_registry,
            )
            print_options = RemedialSheetPrintOptions(
                answer_type='with_short_solutions',
            )

            result = engine.render_document(
                _remedial_sheet_document_render_plan(
                    variant_id=str(remedial_variant.pk),
                    renderer_type='html',
                    print_options=print_options,
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
            self.assertIn('Памятка', html)
            self.assertIn('Сначала вспомните формулу', html)
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
        training_variant_task = create_variant_task(
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
            content_blocks=[
                RemedialContentBlockRow(
                    pk='content-1',
                    source_content_id='source-content-1',
                    content_type='text',
                    order=0,
                    title='Памятка',
                    content={'body': 'Формула $F=ma$ & единицы.'},
                ),
            ],
        )

        with TemporaryDirectory() as output_dir:
            components = build_sectioned_document_components(
                file_store=RenderedDocumentFileStore(
                    output_dirs={'latex': output_dir},
                ),
                get_remedial_sheet_data=lambda variant_id: sheet_data,
            )
            engine = DjangoDocumentEngine(
                document_builder=components.document_builder,
                document_renderer_registry=components.document_renderer_registry,
            )
            print_options = RemedialSheetPrintOptions(
                answer_type='with_short_solutions',
            )

            result = engine.render_document(
                _remedial_sheet_document_render_plan(
                    variant_id=str(remedial_variant.pk),
                    renderer_type='latex',
                    print_options=print_options,
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
            self.assertIn('Памятка', latex)
            self.assertIn(r'Формула \(F=ma\) \& единицы.', latex)
            self.assertIn(r'Тренировка \& \(a=F/m\)', latex)
            self.assertIn(r'Кратко \(a=F/m\)', latex)

    def test_builds_combined_sectioned_html_components(self):
        with TemporaryDirectory() as output_dir:
            components = build_sectioned_html_document_components(
                file_store=RenderedDocumentFileStore(
                    output_dirs={'html': output_dir},
                ),
                get_work_document_source=_work_document_source,
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

    def test_builds_combined_section_payload_registry(self):
        registry = build_sectioned_document_payload_builder_registry(
            get_work_document_source=_work_document_source,
            get_remedial_sheet_data=lambda variant_id: RemedialSheetData(
                variant='variant',
                student=None,
                source_work=Work(name='Исходная работа'),
                mark=None,
                new_tasks=[],
            ),
        )

        work_payload = registry.build_payload(
            DocumentSectionPayloadBuildRequest(
                source=DocumentSourceRef(
                    source_type=WORK_SOURCE_TYPE,
                    source_id='work-1',
                ),
                recipe=DocumentRecipe(document_type=WORK_DOCUMENT_TYPE),
                section=DocumentSectionSpec(section_type=HEADER_SECTION),
            )
        )
        remedial_payload = registry.build_payload(
            DocumentSectionPayloadBuildRequest(
                source=DocumentSourceRef(
                    source_type=REMEDIAL_VARIANT_SOURCE_TYPE,
                    source_id='variant-1',
                ),
                recipe=DocumentRecipe(
                    document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
                ),
                section=DocumentSectionSpec(section_type=HEADER_SECTION),
            )
        )

        self.assertEqual(work_payload['title'], 'Контрольная')
        self.assertEqual(remedial_payload['title'], 'Работа над ошибками')

    def test_registers_event_report_payloads_without_digest_dependency(self):
        report = object()
        registry = build_sectioned_document_payload_builder_registry(
            get_event_report=lambda event_id: report,
        )

        payload = registry.build_payload(
            DocumentSectionPayloadBuildRequest(
                source=DocumentSourceRef(
                    source_type=EVENT_REPORT_SOURCE_TYPE,
                    source_id='event-1',
                ),
                recipe=DocumentRecipe(
                    document_type=EVENT_PERFORMANCE_REPORT_DOCUMENT_TYPE,
                ),
                section=DocumentSectionSpec(section_type=HEADER_SECTION),
            )
        )

        self.assertIs(payload['report'], report)

    def test_registers_digest_payloads_without_event_report_dependency(self):
        digest_request = object()
        digest = SimpleNamespace(
            student=SimpleNamespace(pk='student-1'),
        )
        page = SimpleNamespace(digests=(digest,))
        registry = build_sectioned_document_payload_builder_registry(
            get_student_digests=lambda request: page,
        )

        payload = registry.build_payload(
            DocumentSectionPayloadBuildRequest(
                source=DocumentSourceRef(
                    source_type=STUDENT_DIGEST_SOURCE_TYPE,
                    source_id='group-1',
                ),
                recipe=DocumentRecipe(
                    document_type=STUDENT_DIGEST_DOCUMENT_TYPE,
                ),
                section=DocumentSectionSpec(
                    section_type=HEADER_SECTION,
                    options={
                        'digest_request': digest_request,
                        'student_id': 'student-1',
                    },
                ),
            )
        )

        self.assertIs(payload['page'], page)
        self.assertIs(payload['digest'], digest)

    def test_payload_registry_has_no_hidden_default_sources(self):
        registry = build_sectioned_document_payload_builder_registry()

        with self.assertRaises(UnsupportedDocumentSectionPayloadBuilder):
            registry.get(
                HEADER_SECTION,
                document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
                source_type=REMEDIAL_VARIANT_SOURCE_TYPE,
            )

    def test_builds_combined_sectioned_html_pdf_components(self):
        with TemporaryDirectory() as output_dir:
            components = build_sectioned_html_pdf_document_components(
                file_store=RenderedDocumentFileStore(
                    output_dirs={'html': output_dir, 'pdf': output_dir},
                ),
                get_work_document_source=_work_document_source,
                get_remedial_sheet_data=lambda variant_id: RemedialSheetData(
                    variant='variant',
                    student=None,
                    source_work=None,
                    mark=None,
                    new_tasks=[],
                ),
                html_to_pdf_renderer_factory=lambda request: FakeHtmlToPdfRenderer(),
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
                get_work_document_source=_work_document_source,
                get_remedial_sheet_data=lambda variant_id: RemedialSheetData(
                    variant='variant',
                    student=None,
                    source_work=None,
                    mark=None,
                    new_tasks=[],
                ),
                html_to_pdf_renderer_factory=lambda request: FakeHtmlToPdfRenderer(),
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


def _work_document_source(work_id):
    return WorkDocumentSource(
        pk=str(work_id),
        name='Контрольная',
        work_type='test',
        duration=45,
        max_score=4,
    )


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


def _work_document_render_plan(
    work_id,
    work_name,
    renderer_type,
    print_overrides=None,
    presentation_profile=None,
    variant_ids=None,
):
    print_overrides = print_overrides or WorkDocumentPrintOverrides()
    return DocumentRenderPlan(
        source=build_work_document_source(work_id, work_name),
        recipe=build_work_document_recipe_for_render(
            print_overrides=print_overrides,
            presentation_profile=presentation_profile,
            variant_ids=variant_ids,
        ),
        render_target=RenderTarget(renderer_type=renderer_type),
    )


def _remedial_sheet_document_render_plan(
    variant_id,
    renderer_type,
    print_options=None,
    presentation_profile=None,
):
    print_options = print_options or RemedialSheetPrintOptions()
    return DocumentRenderPlan(
        source=build_remedial_sheet_document_source(variant_id),
        recipe=build_remedial_sheet_document_recipe_for_render(
            print_options=print_options,
            presentation_profile=presentation_profile,
        ),
        render_target=RenderTarget(renderer_type=renderer_type),
    )


class FakeMark:
    def __init__(self, score, points, max_points):
        self.score = score
        self.points = points
        self.max_points = max_points


class FakeHtmlToPdfRenderer:
    def __init__(self):
        self.html_content = ''

    def generate_pdf(self, html_path, pdf_path):
        self.html_content = html_path.read_text(encoding='utf-8')
        pdf_path.write_bytes(b'pdf')
        return pdf_path
