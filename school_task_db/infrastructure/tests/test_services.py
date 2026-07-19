from django.test import TestCase

from core_logic.entities.document import DocumentRecipe, DocumentSourceRef
from core.models import ImportLog
from core_logic.entities.task_import import TaskImportPreviewRequest, TaskImportRequest
from core_logic.value_objects.content_config import (
    RenderTarget,
    WorkDocumentRenderOptions,
)
from core_logic.value_objects.document_render_plan import DocumentRenderPlan
from curriculum.models import Topic
from infrastructure.services.document_generation_service import (
    DjangoDocumentGenerationService,
)
from infrastructure.services.task_import_service import DjangoTaskImportService
from tasks.models import Task


class FakeDocumentBuilder:
    def __init__(self):
        self.request = None

    def build(self, source, recipe):
        self.request = (source, recipe)
        return 'document'


class DjangoDocumentGenerationServiceTests(TestCase):
    def test_resolve_render_target_prefers_render_plan(self):
        service = DjangoDocumentGenerationService(
            get_remedial_sheet_data_use_case=None,
        )
        options = WorkDocumentRenderOptions(renderer_type='pdf')
        plan = DocumentRenderPlan(
            source=DocumentSourceRef(source_type='work', source_id='work-1'),
            recipe=DocumentRecipe(document_type='work'),
            render_target=RenderTarget(renderer_type='html', page_format='A5'),
        )

        target = service._resolve_render_target(options, plan)

        self.assertEqual(target.renderer_type, 'html')
        self.assertEqual(target.page_format, 'A5')

    def test_resolve_render_target_falls_back_to_legacy_options(self):
        service = DjangoDocumentGenerationService(
            get_remedial_sheet_data_use_case=None,
        )
        options = WorkDocumentRenderOptions(renderer_type='latex')

        target = service._resolve_render_target(options)

        self.assertEqual(target.renderer_type, 'latex')
        self.assertEqual(target.page_format, 'A4')

    def test_build_document_uses_configured_builder(self):
        builder = FakeDocumentBuilder()
        service = DjangoDocumentGenerationService(
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
        service = DjangoDocumentGenerationService(
            get_remedial_sheet_data_use_case=None,
        )

        self.assertIsNone(service._build_document())


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
