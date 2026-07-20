from types import SimpleNamespace
from tempfile import TemporaryDirectory

from django.test import TestCase

from core_logic.entities.document import (
    Document,
    DocumentRecipe,
    DocumentSectionSpec,
    DocumentSourceRef,
    REMEDIAL_VARIANT_SOURCE_TYPE,
    WORK_SOURCE_TYPE,
)
from core_logic.entities.document_rendering import GeneratedDocument
from core.models import ImportLog
from core_logic.entities.task_import import TaskImportPreviewRequest, TaskImportRequest
from core_logic.services.document_builder import (
    DocumentSectionPayloadBuilderRegistry,
)
from core_logic.value_objects.content_config import (
    RemedialSheetDocumentRenderOptions,
    RenderTarget,
    WorkDocumentRenderOptions,
)
from core_logic.value_objects.document_render_plan import (
    DocumentRenderPlan,
    build_work_document_render_plan,
)
from curriculum.models import Topic
from infrastructure.services.document_engine import (
    DjangoDocumentEngine,
)
from infrastructure.services.rendered_document_file_store import (
    RenderedDocumentFileStore,
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
        self.pdf_work_request = None

    def render_latex_work(self, work, content_config, page_format='A4'):
        return []

    def render_html_work(self, work, content_config):
        self.html_work_request = (work, content_config)
        return ['work.html']

    def render_pdf_work(self, work, content_config, page_format='A4'):
        self.pdf_work_request = (work, content_config, page_format)
        return []

    def render_remedial_latex(self, variant, content_config, page_format='A4'):
        return []

    def render_remedial_html(self, variant, content_config):
        return []

    def render_remedial_pdf(self, variant, content_config, page_format='A4'):
        return []


class FakeDocumentSourceProvider:
    def __init__(self):
        self.work_requests = []
        self.remedial_requests = []

    def get_work_source(self, work_id):
        self.work_requests.append(work_id)
        return SimpleNamespace(pk=work_id, name='Контрольная')

    def get_remedial_source(self, variant_id):
        self.remedial_requests.append(variant_id)
        return SimpleNamespace(pk=variant_id)


class FakeRenderedDocumentFileStore:
    def __init__(self):
        self.requests = []
        self.path_requests = []
        self.result = 'file-result'

    def get_file(self, file_type, filename):
        self.requests.append((file_type, filename))
        return self.result

    def document_from_paths(self, file_type, file_paths):
        self.path_requests.append((file_type, file_paths))
        return GeneratedDocument(file_type=file_type)


class FakeLegacyRenderRouter:
    def __init__(self):
        self.work_requests = []
        self.remedial_requests = []

    def render_work(self, work, options):
        self.work_requests.append((work, options))
        return GeneratedDocument(file_type=options.renderer_type)

    def render_remedial_sheet(self, variant, options):
        self.remedial_requests.append((variant, options))
        return GeneratedDocument(file_type=options.renderer_type)


class FakeSectionPayloadBuilder:
    def __init__(self, payload):
        self.payload = payload
        self.request = None

    def build_payload(self, request):
        self.request = request
        return self.payload


class FakePdfGenerator:
    def __init__(self):
        self.html_content = ''

    def generate_pdf(self, html_path, pdf_path):
        self.html_content = html_path.read_text(encoding='utf-8')
        pdf_path.write_bytes(b'pdf')
        return pdf_path


def empty_work_render_plan(work_id, work_name, renderer_type):
    return DocumentRenderPlan(
        source=DocumentSourceRef(
            source_type=WORK_SOURCE_TYPE,
            source_id=work_id,
            title=work_name,
        ),
        recipe=DocumentRecipe(document_type='work'),
        render_target=RenderTarget(renderer_type=renderer_type),
    )


class DjangoDocumentEngineTests(TestCase):
    def test_build_document_uses_configured_builder(self):
        builder = FakeDocumentBuilder()
        service = DjangoDocumentEngine(
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

    def test_default_document_builder_uses_section_payload_registry(self):
        payload_registry = DocumentSectionPayloadBuilderRegistry()
        payload_builder = FakeSectionPayloadBuilder(
            payload={'title': 'Из payload'},
        )
        payload_registry.register('header', payload_builder, document_type='work')
        registry = FakeDocumentRendererRegistry()
        service = DjangoDocumentEngine(
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

        result = service.render_work_document(
            work_id='work-1',
            options=WorkDocumentRenderOptions(renderer_type='html'),
            render_plan=plan,
        )

        self.assertEqual(result.file_type, 'html')
        self.assertEqual(
            registry.request.document.sections[0].payload,
            {'title': 'Из payload'},
        )
        self.assertEqual(payload_builder.request.source.source_id, 'work-1')

    def test_render_work_document_uses_document_renderer_registry(self):
        document = Document(title='Контрольная', document_type='work')
        builder = FakeDocumentBuilder(document=document)
        registry = FakeDocumentRendererRegistry()
        service = DjangoDocumentEngine(
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
        legacy_render_router = FakeLegacyRenderRouter()
        service = DjangoDocumentEngine(
            legacy_render_router=legacy_render_router,
        )
        options = WorkDocumentRenderOptions(renderer_type='html')

        result = service._render_legacy_work_document(
            work='work-object',
            options=options,
        )

        self.assertEqual(result.file_type, 'html')
        self.assertEqual(
            legacy_render_router.work_requests,
            [('work-object', options)],
        )

    def test_generate_work_alias_builds_render_plan(self):
        work = Work.objects.create(name='Контрольная')
        document = Document(title='Контрольная', document_type='work')
        builder = FakeDocumentBuilder(document=document)
        registry = FakeDocumentRendererRegistry()
        service = DjangoDocumentEngine(
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

    def test_generate_work_uses_configured_source_provider(self):
        source_provider = FakeDocumentSourceProvider()
        document = Document(title='Контрольная', document_type='work')
        builder = FakeDocumentBuilder(document=document)
        registry = FakeDocumentRendererRegistry()
        service = DjangoDocumentEngine(
            document_builder=builder,
            document_renderer_registry=registry,
            source_provider=source_provider,
        )

        result = service.generate_work(
            work_id='work-1',
            options=WorkDocumentRenderOptions(renderer_type='html'),
        )

        source, recipe = builder.request
        self.assertEqual(result.file_type, 'html')
        self.assertEqual(source_provider.work_requests, ['work-1'])
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

    def test_generate_remedial_sheet_uses_configured_source_provider(self):
        source_provider = FakeDocumentSourceProvider()
        document = Document(title='Разбор', document_type='remedial_sheet')
        builder = FakeDocumentBuilder(document=document)
        registry = FakeDocumentRendererRegistry()
        service = DjangoDocumentEngine(
            document_builder=builder,
            document_renderer_registry=registry,
            source_provider=source_provider,
        )

        result = service.generate_remedial_sheet(
            variant_id='variant-1',
            options=RemedialSheetDocumentRenderOptions(renderer_type='pdf'),
        )

        source, recipe = builder.request
        self.assertEqual(result.file_type, 'pdf')
        self.assertEqual(source_provider.remedial_requests, ['variant-1'])
        self.assertEqual(source.source_id, 'variant-1')
        self.assertEqual(recipe.document_type, 'remedial_sheet')

    def test_get_rendered_file_uses_configured_file_store(self):
        file_store = FakeRenderedDocumentFileStore()
        service = DjangoDocumentEngine(file_store=file_store)

        result = service.get_rendered_file(
            file_type='html',
            filename='work.html',
        )

        self.assertEqual(result, 'file-result')
        self.assertEqual(file_store.requests, [('html', 'work.html')])

    def test_legacy_work_render_uses_configured_file_store(self):
        file_store = FakeRenderedDocumentFileStore()
        legacy_file_renderer = FakeLegacyFileRenderer()
        service = DjangoDocumentEngine(
            file_store=file_store,
            legacy_file_renderer=legacy_file_renderer,
        )

        result = service._render_legacy_work_document(
            work='work-object',
            options=WorkDocumentRenderOptions(renderer_type='html'),
        )

        self.assertEqual(result.file_type, 'html')
        self.assertEqual(file_store.path_requests, [('html', ['work.html'])])

    def test_sectioned_factory_uses_sectioned_html_pdf_and_legacy_latex(self):
        work = Work.objects.create(name='Контрольная', duration=45)
        legacy_file_renderer = FakeLegacyFileRenderer()
        pdf_generator = FakePdfGenerator()

        with TemporaryDirectory() as output_dir:
            service = DjangoDocumentEngine.with_sectioned_renderers(
                file_store=RenderedDocumentFileStore(
                    output_dirs={
                        'html': output_dir,
                        'pdf': output_dir,
                        'latex': output_dir,
                    },
                ),
                legacy_file_renderer=legacy_file_renderer,
                pdf_generator_factory=lambda request: pdf_generator,
            )
            html_options = WorkDocumentRenderOptions(renderer_type='html')
            pdf_options = WorkDocumentRenderOptions(renderer_type='pdf')
            latex_options = WorkDocumentRenderOptions(renderer_type='latex')

            html_result = service.render_work_document(
                work_id=str(work.pk),
                options=html_options,
                render_plan=empty_work_render_plan(
                    work_id=str(work.pk),
                    work_name=work.name,
                    renderer_type='html',
                ),
            )
            pdf_result = service.render_work_document(
                work_id=str(work.pk),
                options=pdf_options,
                render_plan=build_work_document_render_plan(
                    work_id=str(work.pk),
                    work_name=work.name,
                    options=pdf_options,
                ),
            )
            latex_result = service.render_work_document(
                work_id=str(work.pk),
                options=latex_options,
                render_plan=build_work_document_render_plan(
                    work_id=str(work.pk),
                    work_name=work.name,
                    options=latex_options,
                ),
            )

        self.assertEqual(html_result.file_type, 'html')
        self.assertEqual(pdf_result.file_type, 'pdf')
        self.assertEqual(latex_result.file_type, 'latex')
        self.assertIsNone(legacy_file_renderer.html_work_request)
        self.assertIsNone(legacy_file_renderer.pdf_work_request)
        self.assertIn('<title>Контрольная</title>', pdf_generator.html_content)


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
