from types import SimpleNamespace

from django.test import TestCase

from core_logic.entities.document import (
    Document,
    DocumentRecipe,
    DocumentSourceRef,
    REMEDIAL_VARIANT_SOURCE_TYPE,
    WORK_SOURCE_TYPE,
)
from core_logic.entities.document_rendering import GeneratedDocument
from core.models import ImportLog
from core_logic.entities.task_import import TaskImportPreviewRequest, TaskImportRequest
from core_logic.value_objects.content_config import (
    RemedialSheetDocumentRenderOptions,
    RenderTarget,
    WorkDocumentRenderOptions,
)
from core_logic.value_objects.document_render_plan import DocumentRenderPlan
from curriculum.models import Topic
from infrastructure.services.document_engine import (
    DjangoDocumentEngine,
)
from infrastructure.services.task_import_service import DjangoTaskImportService
from tasks.models import Task
from works.models import Variant, Work


class FakeDocumentBuilder:
    def __init__(self, document='document'):
        self.request = None
        self.document = document

    def build(self, source, recipe):
        self.request = (source, recipe)
        return self.document


class FakeDocumentRendererRegistry:
    def __init__(self):
        self.request = None

    def render(self, request):
        self.request = request
        return GeneratedDocument(file_type=request.render_target.renderer_type)


class FakeLegacyFileRenderer:
    def __init__(self):
        self.html_work_request = None

    def render_latex_work(self, work, content_config, page_format='A4'):
        return []

    def render_html_work(self, work, content_config):
        self.html_work_request = (work, content_config)
        return ['work.html']

    def render_pdf_work(self, work, content_config, page_format='A4'):
        return []

    def render_remedial_latex(self, variant, content_config, page_format='A4'):
        return []

    def render_remedial_html(self, variant, content_config):
        return []

    def render_remedial_pdf(self, variant, content_config, page_format='A4'):
        return []


class DjangoDocumentEngineTests(TestCase):
    def test_build_document_uses_configured_builder(self):
        builder = FakeDocumentBuilder()
        service = DjangoDocumentEngine(
            get_remedial_sheet_data_use_case=None,
            document_builder=builder,
        )
        source = DocumentSourceRef(source_type='work', source_id='work-1')
        recipe = DocumentRecipe(document_type='work')
        plan = DocumentRenderPlan(
            source=source,
            recipe=recipe,
            render_target=RenderTarget(renderer_type='html'),
        )

        document = service._build_document(plan)

        self.assertEqual(document, 'document')
        self.assertEqual(builder.request, (source, recipe))

    def test_build_document_returns_none_without_render_plan(self):
        service = DjangoDocumentEngine()

        self.assertIsNone(service._build_document())

    def test_render_work_document_uses_document_renderer_registry(self):
        document = Document(title='Контрольная', document_type='work')
        builder = FakeDocumentBuilder(document=document)
        registry = FakeDocumentRendererRegistry()
        service = DjangoDocumentEngine(
            get_remedial_sheet_data_use_case=None,
            document_builder=builder,
            document_renderer_registry=registry,
        )
        options = WorkDocumentRenderOptions(renderer_type='html')
        plan = DocumentRenderPlan(
            source=DocumentSourceRef(source_type='work', source_id='missing'),
            recipe=DocumentRecipe(document_type='work'),
            render_target=RenderTarget(renderer_type='html'),
        )

        result = service.render_work_document(
            work_id='missing',
            options=options,
            render_plan=plan,
        )

        self.assertEqual(result.file_type, 'html')
        self.assertEqual(registry.request.document, document)
        self.assertEqual(registry.request.render_target.renderer_type, 'html')

    def test_render_remedial_sheet_document_uses_document_renderer_registry(self):
        document = Document(title='Разбор', document_type='remedial_sheet')
        builder = FakeDocumentBuilder(document=document)
        registry = FakeDocumentRendererRegistry()
        service = DjangoDocumentEngine(
            get_remedial_sheet_data_use_case=None,
            document_builder=builder,
            document_renderer_registry=registry,
        )
        options = RemedialSheetDocumentRenderOptions(renderer_type='pdf')
        plan = DocumentRenderPlan(
            source=DocumentSourceRef(
                source_type=REMEDIAL_VARIANT_SOURCE_TYPE,
                source_id='missing',
            ),
            recipe=DocumentRecipe(document_type='remedial_sheet'),
            render_target=RenderTarget(renderer_type='pdf'),
        )

        result = service.render_remedial_sheet_document(
            variant_id='missing',
            options=options,
            render_plan=plan,
        )

        self.assertEqual(result.file_type, 'pdf')
        self.assertEqual(registry.request.document, document)
        self.assertEqual(registry.request.render_target.renderer_type, 'pdf')

    def test_render_from_plan_returns_none_without_plan(self):
        service = DjangoDocumentEngine()

        result = service._render_from_plan()

        self.assertIsNone(result)

    def test_legacy_work_render_uses_options_target(self):
        legacy_file_renderer = FakeLegacyFileRenderer()
        service = DjangoDocumentEngine(
            get_remedial_sheet_data_use_case=None,
            legacy_file_renderer=legacy_file_renderer,
        )
        service._document_from_paths = (
            lambda file_type, file_paths:
                GeneratedDocument(file_type=file_type)
        )

        result = service._render_legacy_work_document(
            work='work-object',
            options=WorkDocumentRenderOptions(renderer_type='html'),
        )

        self.assertEqual(result.file_type, 'html')
        self.assertEqual(legacy_file_renderer.html_work_request[0], 'work-object')

    def test_generate_work_alias_builds_render_plan(self):
        work = Work.objects.create(name='Контрольная')
        document = Document(title='Контрольная', document_type='work')
        builder = FakeDocumentBuilder(document=document)
        registry = FakeDocumentRendererRegistry()
        service = DjangoDocumentEngine(
            get_remedial_sheet_data_use_case=None,
            document_builder=builder,
            document_renderer_registry=registry,
        )

        result = service.generate_work(
            work_id=str(work.pk),
            options=WorkDocumentRenderOptions(renderer_type='html'),
        )

        source, recipe = builder.request
        self.assertEqual(result.file_type, 'html')
        self.assertEqual(source.source_type, WORK_SOURCE_TYPE)
        self.assertEqual(source.source_id, str(work.pk))
        self.assertEqual(source.title, 'Контрольная')
        self.assertEqual(recipe.document_type, 'work')

    def test_generate_work_alias_uses_given_render_plan(self):
        work = Work.objects.create(name='Контрольная')
        document = Document(title='Контрольная', document_type='work')
        builder = FakeDocumentBuilder(document=document)
        registry = FakeDocumentRendererRegistry()
        service = DjangoDocumentEngine(
            get_remedial_sheet_data_use_case=None,
            document_builder=builder,
            document_renderer_registry=registry,
        )
        plan = DocumentRenderPlan(
            source=DocumentSourceRef(
                source_type=WORK_SOURCE_TYPE,
                source_id=str(work.pk),
                title='Переопределённое имя',
            ),
            recipe=DocumentRecipe(document_type='work'),
            render_target=RenderTarget(renderer_type='pdf'),
        )

        result = service.generate_work(
            work_id=str(work.pk),
            options=WorkDocumentRenderOptions(renderer_type='html'),
            render_plan=plan,
        )

        source, recipe = builder.request
        self.assertEqual(result.file_type, 'pdf')
        self.assertEqual(source.title, 'Переопределённое имя')
        self.assertEqual(recipe.document_type, 'work')

    def test_generate_work_uses_configured_source_getter(self):
        calls = []
        work = SimpleNamespace(pk='work-1', name='Контрольная')
        document = Document(title='Контрольная', document_type='work')
        builder = FakeDocumentBuilder(document=document)
        registry = FakeDocumentRendererRegistry()
        service = DjangoDocumentEngine(
            get_remedial_sheet_data_use_case=None,
            document_builder=builder,
            document_renderer_registry=registry,
            get_work_source=lambda work_id: calls.append(work_id) or work,
        )

        result = service.generate_work(
            work_id='work-1',
            options=WorkDocumentRenderOptions(renderer_type='html'),
        )

        source, recipe = builder.request
        self.assertEqual(result.file_type, 'html')
        self.assertEqual(calls, ['work-1'])
        self.assertEqual(source.source_id, 'work-1')
        self.assertEqual(source.title, 'Контрольная')
        self.assertEqual(recipe.document_type, 'work')

    def test_generate_remedial_sheet_alias_builds_render_plan(self):
        variant = Variant.objects.create(
            work=None,
            number=1,
            variant_type='remedial',
        )
        document = Document(title='Разбор', document_type='remedial_sheet')
        builder = FakeDocumentBuilder(document=document)
        registry = FakeDocumentRendererRegistry()
        service = DjangoDocumentEngine(
            get_remedial_sheet_data_use_case=None,
            document_builder=builder,
            document_renderer_registry=registry,
        )

        result = service.generate_remedial_sheet(
            variant_id=str(variant.pk),
            options=RemedialSheetDocumentRenderOptions(renderer_type='pdf'),
        )

        source, recipe = builder.request
        self.assertEqual(result.file_type, 'pdf')
        self.assertEqual(source.source_type, REMEDIAL_VARIANT_SOURCE_TYPE)
        self.assertEqual(source.source_id, str(variant.pk))
        self.assertEqual(recipe.document_type, 'remedial_sheet')

    def test_generate_remedial_sheet_alias_uses_given_render_plan(self):
        variant = Variant.objects.create(
            work=None,
            number=1,
            variant_type='remedial',
        )
        document = Document(title='Разбор', document_type='remedial_sheet')
        builder = FakeDocumentBuilder(document=document)
        registry = FakeDocumentRendererRegistry()
        service = DjangoDocumentEngine(
            get_remedial_sheet_data_use_case=None,
            document_builder=builder,
            document_renderer_registry=registry,
        )
        plan = DocumentRenderPlan(
            source=DocumentSourceRef(
                source_type=REMEDIAL_VARIANT_SOURCE_TYPE,
                source_id=str(variant.pk),
            ),
            recipe=DocumentRecipe(document_type='remedial_sheet'),
            render_target=RenderTarget(renderer_type='html'),
        )

        result = service.generate_remedial_sheet(
            variant_id=str(variant.pk),
            options=RemedialSheetDocumentRenderOptions(renderer_type='pdf'),
            render_plan=plan,
        )

        source, recipe = builder.request
        self.assertEqual(result.file_type, 'html')
        self.assertEqual(source.source_type, REMEDIAL_VARIANT_SOURCE_TYPE)
        self.assertEqual(recipe.document_type, 'remedial_sheet')

    def test_generate_remedial_sheet_uses_configured_source_getter(self):
        calls = []
        variant = SimpleNamespace(pk='variant-1')
        document = Document(title='Разбор', document_type='remedial_sheet')
        builder = FakeDocumentBuilder(document=document)
        registry = FakeDocumentRendererRegistry()
        service = DjangoDocumentEngine(
            get_remedial_sheet_data_use_case=None,
            document_builder=builder,
            document_renderer_registry=registry,
            get_remedial_source=(
                lambda variant_id: calls.append(variant_id) or variant
            ),
        )

        result = service.generate_remedial_sheet(
            variant_id='variant-1',
            options=RemedialSheetDocumentRenderOptions(renderer_type='pdf'),
        )

        source, recipe = builder.request
        self.assertEqual(result.file_type, 'pdf')
        self.assertEqual(calls, ['variant-1'])
        self.assertEqual(source.source_id, 'variant-1')
        self.assertEqual(recipe.document_type, 'remedial_sheet')


class DjangoTaskImportServiceTests(TestCase):
    def test_preview_import_returns_dry_run_context_without_creating_tasks(self):
        request = TaskImportPreviewRequest(
            data={
                'tasks': [
                    {
                        'id': '550e8400-e29b-41d4-a716-446655440001',
                        'text': 'Задача на силу',
                        'answer': 'Ответ',
                        'task_type': 'computational',
                        'difficulty': 2,
                        'topic': {
                            'name': 'Динамика',
                            'subject': 'Физика',
                            'grade_level': 9,
                        },
                    },
                ],
            },
        )

        result = DjangoTaskImportService().preview_import(request)

        self.assertTrue(result.success)
        self.assertEqual(result.preview['total_created'], 0)
        self.assertEqual(result.preview['tasks_in_context'], 0)
        self.assertFalse(Task.objects.filter(text='Задача на силу').exists())

    def test_execute_import_creates_log_and_tasks(self):
        request = TaskImportRequest(
            data={
                'tasks': [
                    {
                        'id': '550e8400-e29b-41d4-a716-446655440001',
                        'text': 'Задача на силу',
                        'answer': 'Ответ',
                        'task_type': 'computational',
                        'difficulty': 2,
                        'topic': {
                            'name': 'Динамика',
                            'subject': 'Физика',
                            'grade_level': 9,
                            'section': 'Механика',
                        },
                    },
                ],
            },
            filename='tasks.json',
            file_size=256,
            mode='update',
            dry_run=False,
            create_missing=True,
        )

        result = DjangoTaskImportService().execute_import(request)
        log = ImportLog.objects.get(pk=result.log_id)

        self.assertTrue(result.success)
        self.assertEqual(result.stats['created'], 1)
        self.assertEqual(result.stats['context_counts']['tasks'], 1)
        self.assertEqual(log.status, ImportLog.Status.SUCCESS)
        self.assertEqual(log.filename, 'tasks.json')
        self.assertEqual(log.tasks_created, 1)
        self.assertTrue(Topic.objects.filter(name='Динамика').exists())
        self.assertTrue(Task.objects.filter(text='Задача на силу').exists())

    def test_execute_import_returns_error_result_and_failed_log(self):
        request = TaskImportRequest(
            data={'tasks': []},
            filename='tasks.json',
            file_size=128,
            mode='unsupported',
        )

        result = DjangoTaskImportService().execute_import(request)
        log = ImportLog.objects.get(pk=result.log_id)

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'error')
        self.assertIn('Неверный режим импорта', result.error)
        self.assertEqual(log.status, ImportLog.Status.FAILED)
        self.assertEqual(log.error_messages, [result.error])
