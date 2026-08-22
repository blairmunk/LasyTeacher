from tempfile import TemporaryDirectory

from django.test import TestCase

from core_logic.entities.document import (
    Document,
    DocumentRecipe,
    DocumentSectionSpec,
    DocumentSourceRef,
    REMEDIAL_VARIANT_SOURCE_TYPE,
)
from core_logic.entities.document_rendering import GeneratedDocument
from core.models import ImportLog
from core_logic.entities.task_import import TaskImportPreviewRequest, TaskImportRequest
from core_logic.services.task_import_runner import TaskImportRunnerService
from core_logic.use_cases.execute_task_import import ExecuteTaskImportUseCase
from core_logic.services.document_builder import (
    DocumentSectionPayloadBuilderRegistry,
)
from core_logic.value_objects.document_render_options import (
    RenderTarget,
)
from core_logic.value_objects.document_render_plan import (
    DocumentRenderPlan,
)
from curriculum.models import Topic
from infrastructure.services.document_engine import (
    SectionedDocumentEngine,
)
from infrastructure.repositories.django_task_import_log_repo import (
    DjangoTaskImportLogRepository,
)
from infrastructure.importers.tasks import (
    DjangoTaskImportWriteSessionFactory,
)
from infrastructure.repositories.django_task_import_preview_repo import (
    DjangoTaskImportPreviewRepository,
)
from infrastructure.services.django_transaction_manager import (
    DjangoTransactionManager,
)
from tasks.models import Task
from works.models import Work


class FakeDocumentBuilder:
    def __init__(self, document='document'):
        self.request = None
        self.document = document

    def build(self, source, recipe, render_target=None):
        self.request = (source, recipe, render_target)
        return self.document


class FakeDocumentRendererRegistry:
    def __init__(self):
        self.request = None

    def render(self, request):
        self.request = request
        return GeneratedDocument(file_type=request.render_target.renderer_type)


class FakeSectionPayloadBuilder:
    def __init__(self, payload):
        self.payload = payload
        self.request = None

    def build_payload(self, request):
        self.request = request
        return self.payload


class SectionedDocumentEngineTests(TestCase):
    def test_build_document_uses_configured_builder(self):
        builder = FakeDocumentBuilder()
        service = SectionedDocumentEngine(
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
        self.assertEqual(builder.request, (source, recipe, plan.render_target))

    def test_default_document_builder_uses_section_payload_registry(self):
        payload_registry = DocumentSectionPayloadBuilderRegistry()
        payload_builder = FakeSectionPayloadBuilder(
            payload={'title': 'Из payload'},
        )
        payload_registry.register('header', payload_builder, document_type='work')
        registry = FakeDocumentRendererRegistry()
        service = SectionedDocumentEngine(
            section_payload_builder_registry=payload_registry,
            document_renderer_registry=registry,
        )
        plan = DocumentRenderPlan(
            source=DocumentSourceRef(source_type='work', source_id='work-1'),
            recipe=DocumentRecipe(
                document_type='work',
                sections=[DocumentSectionSpec(section_type='header')],
            ),
            render_target=RenderTarget(renderer_type='html'),
        )

        result = service.render_document(plan)

        self.assertEqual(result.file_type, 'html')
        self.assertEqual(
            registry.request.document.sections[0].payload,
            {'title': 'Из payload'},
        )
        self.assertEqual(payload_builder.request.source.source_id, 'work-1')

    def test_render_document_uses_document_renderer_registry(self):
        document = Document(title='Контрольная', document_type='work')
        builder = FakeDocumentBuilder(document=document)
        registry = FakeDocumentRendererRegistry()
        service = SectionedDocumentEngine(
            document_builder=builder,
            document_renderer_registry=registry,
        )
        plan = DocumentRenderPlan(
            source=DocumentSourceRef(source_type='work', source_id='missing'),
            recipe=DocumentRecipe(document_type='work'),
            render_target=RenderTarget(renderer_type='html'),
        )

        result = service.render_document(plan)

        self.assertEqual(result.file_type, 'html')
        self.assertEqual(registry.request.document, document)
        self.assertEqual(registry.request.render_target.renderer_type, 'html')

    def test_render_document_handles_remedial_sheet_plan(self):
        document = Document(title='Разбор', document_type='remedial_sheet')
        builder = FakeDocumentBuilder(document=document)
        registry = FakeDocumentRendererRegistry()
        service = SectionedDocumentEngine(
            document_builder=builder,
            document_renderer_registry=registry,
        )
        plan = DocumentRenderPlan(
            source=DocumentSourceRef(
                source_type=REMEDIAL_VARIANT_SOURCE_TYPE,
                source_id='missing',
            ),
            recipe=DocumentRecipe(document_type='remedial_sheet'),
            render_target=RenderTarget(renderer_type='pdf'),
        )

        result = service.render_document(plan)

        self.assertEqual(result.file_type, 'pdf')
        self.assertEqual(registry.request.document, document)
        self.assertEqual(registry.request.render_target.renderer_type, 'pdf')

    def test_render_document_requires_render_plan(self):
        service = SectionedDocumentEngine()

        with self.assertRaisesRegex(
            ValueError,
            'Document render plan is required.',
        ):
            service.render_document(None)

class TaskImportRunnerIntegrationTests(TestCase):
    def test_preview_import_returns_dry_run_context_without_creating_tasks(self):
        topic_id = '660e8400-e29b-41d4-a716-446655440001'
        request = TaskImportPreviewRequest(
            data={
                'topics': [{
                    'id': topic_id,
                    'name': 'Динамика',
                    'subject': 'Физика',
                    'grade_level': 9,
                }],
                'tasks': [
                    {
                        'id': '550e8400-e29b-41d4-a716-446655440001',
                        'text': 'Задача на силу',
                        'answer': 'Ответ',
                        'task_type': 'computational',
                        'difficulty': 2,
                        'topic': {'id': topic_id},
                    },
                ],
            },
        )

        result = self._runner().preview_import(request)

        self.assertEqual(result.preview['file_counts']['tasks'], 1)
        self.assertEqual(result.preview['task_uuid_counts']['new'], 1)
        self.assertEqual(result.preview['task_uuid_counts']['existing'], 0)
        self.assertFalse(Task.objects.filter(text='Задача на силу').exists())

    def test_execute_import_creates_log_and_tasks(self):
        topic_id = '660e8400-e29b-41d4-a716-446655440001'
        request = TaskImportRequest(
            data={
                'topics': [{
                    'id': topic_id,
                    'name': 'Динамика',
                    'subject': 'Физика',
                    'grade_level': 9,
                    'section': 'Механика',
                }],
                'analog_groups': [
                    {
                        'id': '770e8400-e29b-41d4-a716-446655440001',
                        'name': 'Силы',
                        'difficulty': 2,
                    },
                ],
                'tasks': [
                    {
                        'id': '550e8400-e29b-41d4-a716-446655440001',
                        'text': 'Задача на силу',
                        'answer': 'Ответ',
                        'task_type': 'computational',
                        'difficulty': 2,
                        'topic': {'id': topic_id},
                        'groups': [
                            '770e8400-e29b-41d4-a716-446655440001',
                        ],
                    },
                ],
            },
            filename='tasks.json',
            file_size=256,
            mode='update',
            dry_run=False,
            create_missing=True,
        )

        result = self._execute(request)
        log = ImportLog.objects.get(pk=result.log_id)

        self.assertTrue(result.success)
        self.assertEqual(result.stats['created'], 1)
        self.assertEqual(result.stats['context_counts']['tasks'], 1)
        self.assertEqual(log.status, ImportLog.Status.SUCCESS)
        self.assertEqual(log.filename, 'tasks.json')
        self.assertEqual(log.tasks_created, 1)
        self.assertEqual(log.groups_created, 1)
        self.assertEqual(log.topics_created, 1)
        self.assertEqual(log.images_created, 0)
        self.assertEqual(result.stats['by_type']['created']['tasks'], 1)
        self.assertEqual(result.stats['by_type']['created']['groups'], 1)
        self.assertEqual(result.stats['by_type']['created']['topics'], 1)
        self.assertIn('Файл: tasks.json (256 Б)', result.message)
        self.assertIn('Время:', result.message)
        self.assertTrue(Topic.objects.filter(name='Динамика').exists())
        self.assertTrue(Task.objects.filter(text='Задача на силу').exists())

    def test_execute_import_returns_error_result_and_failed_log(self):
        request = TaskImportRequest(
            data={'tasks': []},
            filename='tasks.json',
            file_size=128,
            mode='unsupported',
        )

        result = self._execute(request)
        log = ImportLog.objects.get(pk=result.log_id)

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'error')
        self.assertIn('Неверный режим импорта', result.error)
        self.assertEqual(log.status, ImportLog.Status.FAILED)
        self.assertEqual(log.error_messages, [result.error])

    def test_execute_import_persists_warnings_without_partial_status(self):
        request = TaskImportRequest(
            data={
                'format_version': '1.2',
                'tasks': [],
            },
            filename='old-format.json',
            file_size=64,
        )

        result = self._execute(request)
        log = ImportLog.objects.get(pk=result.log_id)

        self.assertTrue(result.success)
        self.assertEqual(log.status, ImportLog.Status.SUCCESS)
        self.assertEqual(log.errors_count, 0)
        self.assertEqual(log.error_messages, [])
        self.assertEqual(len(log.details['warning_messages']), 2)
        self.assertTrue(any(
            'формате 1.5' in warning
            for warning in log.details['warning_messages']
        ))
        self.assertIn(
            'Массив "tasks" пуст',
            log.details['warning_messages'],
        )

    def test_execute_import_preserves_partial_import_error_messages(self):
        request = TaskImportRequest(
            data={
                'tasks': [
                    {
                        'id': '550e8400-e29b-41d4-a716-446655440001',
                        'text': 'Задание без объявленной темы',
                        'topic': {
                            'id': '660e8400-e29b-41d4-a716-446655440099',
                        },
                    },
                ],
            },
            filename='broken-tasks.json',
            file_size=128,
        )

        result = self._execute(request)
        log = ImportLog.objects.get(pk=result.log_id)

        self.assertTrue(result.success)
        self.assertEqual(result.stats['errors'], 1)
        self.assertEqual(log.status, ImportLog.Status.PARTIAL)
        self.assertEqual(log.errors_count, 1)
        self.assertTrue(log.error_messages)
        self.assertIn('тему для задания', log.error_messages[0])

    @staticmethod
    def _execute(request):
        return ExecuteTaskImportUseCase(
            task_import_runner=(
                TaskImportRunnerIntegrationTests._runner()
            ),
            task_import_log_repo=DjangoTaskImportLogRepository(),
        ).execute(request)

    @staticmethod
    def _runner():
        return TaskImportRunnerService(
            write_session_factory=DjangoTaskImportWriteSessionFactory(),
            preview_repo=DjangoTaskImportPreviewRepository(),
            transaction_manager=DjangoTransactionManager(),
        )
