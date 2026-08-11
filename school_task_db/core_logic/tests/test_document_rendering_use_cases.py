"""Document rendering use case tests."""

from types import SimpleNamespace
from unittest import TestCase

from core_logic.entities.document import (
    DocumentPresentation,
    DocumentPresentationProfile,
)
from core_logic.entities.document_rendering import (
    DocumentRenderResult,
    DOCUMENT_RENDER_STATUS_NOT_PERSONALIZED,
    DOCUMENT_RENDER_STATUS_PERSONAL_REMEDIAL_REQUIRED,
    DOCUMENT_RENDER_STATUS_VARIANTS_NOT_REQUIRED,
    DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER,
    GeneratedDocument,
    GeneratedDocumentFile,
    GeneratedFile,
    GeneratedFileResult,
)
from core_logic.entities.work import RemedialSheetSource, WorkDocumentRef
from core_logic.use_cases.get_rendered_document_file import (
    GetRenderedDocumentFileRequest,
    GetRenderedDocumentFileUseCase,
)
from core_logic.use_cases.render_document_from_recipe import (
    RenderDocumentFromRecipeUseCase,
)
from core_logic.use_cases.render_remedial_sheet_document import (
    RenderRemedialSheetDocumentRequest,
    RenderRemedialSheetDocumentUseCase,
)
from core_logic.use_cases.render_remedial_sheet_batch_document import (
    RenderRemedialSheetBatchDocumentRequest,
    RenderRemedialSheetBatchDocumentUseCase,
)
from core_logic.use_cases.render_work_document import (
    RenderWorkDocumentRequest,
    RenderWorkDocumentUseCase,
)
from core_logic.value_objects.document_render_options import (
    RenderTarget,
)
from core_logic.value_objects.document_recipes import (
    ANSWERS_SECTION,
    HEADER_SECTION,
    PAGE_BREAK_SECTION,
    SHORT_SOLUTIONS_SECTION,
    TASK_LIST_SECTION,
)
from core_logic.value_objects.work_assessment import (
    WORK_ASSESSMENT_MODE_AGGREGATE,
    WORK_ASSESSMENT_MODE_VARIANT,
)


class FakeDocumentEngine:
    def __init__(self):
        self.render_request = None
        self.work_document = GeneratedDocument(
            file_type='html',
            files=[GeneratedDocumentFile(filename='work.html', size_kb=1.0)],
        )
        self.remedial_document = GeneratedDocument(
            file_type='pdf',
            files=[GeneratedDocumentFile(filename='remedial.pdf', size_kb=2.0)],
        )

    def render_document(self, render_plan):
        self.render_request = render_plan
        if render_plan.recipe.document_type == 'remedial_sheet':
            return self.remedial_document
        return self.work_document


class FakeRenderedDocumentFileStore:
    def __init__(self):
        self.file_request = None
        self.file_result = GeneratedFileResult(
            status='ready',
            file=GeneratedFile(
                filename='work.html',
                content=b'html',
                content_type='text/html',
            ),
        )

    def get_file(self, file_type, filename):
        self.file_request = (file_type, filename)
        return self.file_result


def recipe_renderer(document_engine):
    return RenderDocumentFromRecipeUseCase(
        document_engine=document_engine,
    )


class FakeWorkRepository:
    def __init__(
        self,
        variant_type='remedial',
        work_name='Контрольная',
        variant_ids=None,
        remedial_variant_ids=None,
        remedial_sheet_data=None,
        work_type='test',
        assessment_mode=WORK_ASSESSMENT_MODE_VARIANT,
    ):
        self.variant_type = variant_type
        self.variant_type_request = None
        self.work_name = work_name
        self.work_name_request = None
        self.work_type = work_type
        self.assessment_mode = assessment_mode
        self.remedial_variant_ids = remedial_variant_ids or []
        self.remedial_variant_ids_request = None
        self.remedial_sheet_source = (
            remedial_sheet_data
            if remedial_sheet_data is not None
            else RemedialSheetSource(
                variant=None,
                student=object(),
                source_work=None,
                mark=None,
            )
        )
        self.variant_ids = variant_ids or ['variant-1']
        self.variant_ids_request = None

    def get_work_document_ref(self, work_id):
        self.work_name_request = work_id
        if self.work_name is None:
            return None
        return WorkDocumentRef(
            pk=work_id,
            name=self.work_name,
            work_type=self.work_type,
            assessment_mode=self.assessment_mode,
        )

    def get_variant_type(self, variant_id):
        self.variant_type_request = variant_id
        return self.variant_type

    def get_work_personal_remedial_variant_ids(self, work_id):
        self.remedial_variant_ids_request = work_id
        return self.remedial_variant_ids

    def get_work_variant_ids(self, work_id):
        self.variant_ids_request = work_id
        return self.variant_ids

    def get_remedial_sheet_source(self, variant_id):
        source = self.remedial_sheet_source
        if source is None or isinstance(source, RemedialSheetSource):
            return source
        return RemedialSheetSource(
            variant=getattr(source, 'variant', None),
            student=getattr(source, 'student', None),
            source_work=getattr(source, 'source_work', None),
            mark=getattr(source, 'mark', None),
        )


class FakeRenderRemedialSheetDocumentUseCase:
    def __init__(self):
        self.requests = []
        self.results_by_variant_id = {}

    def execute(self, request):
        self.requests.append(request)
        return self.results_by_variant_id.get(
            request.variant_id,
            DocumentRenderResult(
                status='generated',
                renderer_type=request.render_target.renderer_type,
                file_type=request.render_target.renderer_type,
                files=[
                    GeneratedDocumentFile(
                        filename=f'remedial_{request.variant_id}.pdf',
                        size_kb=2.0,
                    ),
                ],
            ),
        )


class FakePresentationProfileRepository:
    def __init__(self):
        self.requested_presentation_profile_ids = []
        self.presentation_profiles_by_id = {}

    def list_presentation_profiles(self, document_type=''):
        return []

    def get_presentation_profile(self, presentation_profile_id, document_type=''):
        self.requested_presentation_profile_ids.append(
            (presentation_profile_id, document_type),
        )
        return self.presentation_profiles_by_id.get(
            (presentation_profile_id, document_type),
        )


class DocumentRenderingUseCaseTests(TestCase):
    def test_document_render_result_exposes_renderer_type(self):
        result = DocumentRenderResult(status='generated', renderer_type='html')

        self.assertEqual(result.renderer_type, 'html')

    def test_render_work_document_rejects_unsupported_renderer(self):
        service = FakeDocumentEngine()
        work_repo = FakeWorkRepository()
        use_case = RenderWorkDocumentUseCase(
            render_document_from_recipe_use_case=recipe_renderer(service),
            work_repo=work_repo,
        )

        result = use_case.execute(
            RenderWorkDocumentRequest(
                work_id='work-1',
                render_target=RenderTarget(renderer_type='docx'),
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER)
        self.assertEqual(result.renderer_type, 'docx')
        self.assertEqual(result.source_name, 'Контрольная')
        self.assertEqual(work_repo.work_name_request, 'work-1')
        self.assertIsNone(service.render_request)

    def test_render_work_document_delegates_to_service(self):
        service = FakeDocumentEngine()
        work_repo = FakeWorkRepository()
        use_case = RenderWorkDocumentUseCase(
            render_document_from_recipe_use_case=recipe_renderer(service),
            work_repo=work_repo,
        )
        render_target = RenderTarget(renderer_type='html')

        result = use_case.execute(
            RenderWorkDocumentRequest(
                work_id='work-1',
                render_target=render_target,
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.file_type, 'html')
        self.assertEqual(result.files[0].filename, 'work.html')
        self.assertEqual(result.files[0].size_kb, 1.0)
        self.assertEqual(result.source_name, 'Контрольная')
        self.assertEqual(work_repo.work_name_request, 'work-1')
        render_plan = service.render_request
        self.assertEqual(render_plan.source.source_type, 'work')
        self.assertEqual(render_plan.source.source_id, 'work-1')
        self.assertEqual(render_plan.source.title, 'Контрольная')
        self.assertEqual(render_plan.render_target.renderer_type, 'html')
        self.assertEqual(
            render_plan.recipe.section_types,
            (HEADER_SECTION, TASK_LIST_SECTION),
        )

    def test_render_work_document_rejects_remedial_work(self):
        service = FakeDocumentEngine()
        use_case = RenderWorkDocumentUseCase(
            render_document_from_recipe_use_case=recipe_renderer(service),
            work_repo=FakeWorkRepository(work_type='remedial'),
        )

        result = use_case.execute(
            RenderWorkDocumentRequest(
                work_id='work-1',
                render_target=RenderTarget(renderer_type='pdf'),
            )
        )

        self.assertEqual(
            result.status,
            DOCUMENT_RENDER_STATUS_PERSONAL_REMEDIAL_REQUIRED,
        )
        self.assertIsNone(service.render_request)

    def test_render_work_document_rejects_aggregate_work(self):
        service = FakeDocumentEngine()
        use_case = RenderWorkDocumentUseCase(
            render_document_from_recipe_use_case=recipe_renderer(service),
            work_repo=FakeWorkRepository(
                assessment_mode=WORK_ASSESSMENT_MODE_AGGREGATE,
            ),
        )

        result = use_case.execute(
            RenderWorkDocumentRequest(
                work_id='work-1',
                render_target=RenderTarget(renderer_type='pdf'),
            )
        )

        self.assertEqual(
            result.status,
            DOCUMENT_RENDER_STATUS_VARIANTS_NOT_REQUIRED,
        )
        self.assertIsNone(service.render_request)

    def test_render_work_document_uses_recipe_renderer_dependency(self):
        service = FakeDocumentEngine()
        use_case = RenderWorkDocumentUseCase(
            render_document_from_recipe_use_case=recipe_renderer(service),
            work_repo=FakeWorkRepository(),
        )

        result = use_case.execute(
            RenderWorkDocumentRequest(
                work_id='work-1',
                render_target=RenderTarget(renderer_type='html'),
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(service.render_request.source.source_id, 'work-1')

    def test_render_work_document_uses_request_presentation_profile(self):
        service = FakeDocumentEngine()
        presentation_profile_repo = FakePresentationProfileRepository()
        use_case = RenderWorkDocumentUseCase(
            render_document_from_recipe_use_case=recipe_renderer(service),
            work_repo=FakeWorkRepository(),
            presentation_profile_repo=presentation_profile_repo,
        )
        self.assertIs(use_case.presentation_profile_repo, presentation_profile_repo)
        presentation_profile = DocumentPresentationProfile(
            name='Кастомная работа',
            document_type='work',
            presentation=DocumentPresentation(
                custom_latex_preamble='\\usepackage{multicol}',
            ),
        )

        result = use_case.execute(
            RenderWorkDocumentRequest(
                work_id='work-1',
                render_target=RenderTarget(renderer_type='html'),
                presentation_profile=presentation_profile,
            )
        )

        self.assertTrue(result.success)
        render_plan = service.render_request
        self.assertEqual(
            render_plan.recipe.section_types,
            (HEADER_SECTION, TASK_LIST_SECTION),
        )
        self.assertEqual(
            render_plan.recipe.presentation.custom_latex_preamble,
            '\\usepackage{multicol}',
        )

    def test_render_work_document_without_profile_uses_builtin_presentation(self):
        service = FakeDocumentEngine()
        presentation_profile_repo = FakePresentationProfileRepository()
        use_case = RenderWorkDocumentUseCase(
            render_document_from_recipe_use_case=recipe_renderer(service),
            work_repo=FakeWorkRepository(),
            presentation_profile_repo=presentation_profile_repo,
        )

        result = use_case.execute(
            RenderWorkDocumentRequest(
                work_id='work-1',
                render_target=RenderTarget(renderer_type='html'),
            )
        )

        self.assertTrue(result.success)
        render_plan = service.render_request
        self.assertEqual(
            render_plan.recipe.section_types,
            (HEADER_SECTION, TASK_LIST_SECTION),
        )
        self.assertEqual(render_plan.recipe.presentation.custom_css, '')

    def test_render_work_document_uses_presentation_profile_id(self):
        service = FakeDocumentEngine()
        presentation_profile_repo = FakePresentationProfileRepository()
        presentation_profile_repo.presentation_profiles_by_id[('template-work', 'work')] = (
            DocumentPresentationProfile(
                name='Selected work',
                document_type='work',
                presentation_profile_id='template-work',
                presentation=DocumentPresentation(
                    custom_css='.task { margin-bottom: 1rem; }',
                ),
            )
        )
        use_case = RenderWorkDocumentUseCase(
            render_document_from_recipe_use_case=recipe_renderer(service),
            work_repo=FakeWorkRepository(),
            presentation_profile_repo=presentation_profile_repo,
        )

        result = use_case.execute(
            RenderWorkDocumentRequest(
                work_id='work-1',
                render_target=RenderTarget(renderer_type='html'),
                presentation_profile_id='template-work',
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(
            presentation_profile_repo.requested_presentation_profile_ids,
            [('template-work', 'work')],
        )
        self.assertEqual(
            service.render_request.recipe.section_types,
            (HEADER_SECTION, TASK_LIST_SECTION),
        )
        self.assertEqual(
            service.render_request.recipe.presentation.custom_css,
            '.task { margin-bottom: 1rem; }',
        )

    def test_render_work_document_handles_missing_work(self):
        service = FakeDocumentEngine()
        use_case = RenderWorkDocumentUseCase(
            render_document_from_recipe_use_case=recipe_renderer(service),
            work_repo=FakeWorkRepository(work_name=None),
        )

        result = use_case.execute(
            RenderWorkDocumentRequest(
                work_id='missing-work',
                render_target=RenderTarget(renderer_type='html'),
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'not_found')
        self.assertIsNone(service.render_request)

    def test_render_work_document_can_select_one_work_variant(self):
        service = FakeDocumentEngine()
        use_case = RenderWorkDocumentUseCase(
            render_document_from_recipe_use_case=recipe_renderer(service),
            work_repo=FakeWorkRepository(
                variant_ids=['variant-1', 'variant-2'],
            ),
        )

        result = use_case.execute(
            RenderWorkDocumentRequest(
                work_id='work-1',
                variant_id='variant-2',
                render_target=RenderTarget(renderer_type='html'),
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(
            [
                section.options.get('variant_id')
                for section in service.render_request.recipe.sections
            ],
            ['variant-2', 'variant-2'],
        )

    def test_render_work_document_rejects_foreign_variant(self):
        service = FakeDocumentEngine()
        use_case = RenderWorkDocumentUseCase(
            render_document_from_recipe_use_case=recipe_renderer(service),
            work_repo=FakeWorkRepository(variant_ids=['variant-1']),
        )

        result = use_case.execute(
            RenderWorkDocumentRequest(
                work_id='work-1',
                variant_id='foreign-variant',
                render_target=RenderTarget(renderer_type='html'),
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'not_found')
        self.assertIsNone(service.render_request)

    def test_render_remedial_sheet_document_delegates_to_service(self):
        service = FakeDocumentEngine()
        work_repo = FakeWorkRepository()
        use_case = RenderRemedialSheetDocumentUseCase(
            render_document_from_recipe_use_case=recipe_renderer(service),
            remedial_repo=work_repo,
        )
        render_target = RenderTarget(renderer_type='pdf')

        result = use_case.execute(
            RenderRemedialSheetDocumentRequest(
                variant_id='variant-1',
                render_target=render_target,
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.file_type, 'pdf')
        self.assertEqual(result.files[0].filename, 'remedial.pdf')
        self.assertEqual(result.files[0].size_kb, 2.0)
        self.assertEqual(work_repo.variant_type_request, 'variant-1')
        render_plan = service.render_request
        self.assertEqual(render_plan.source.source_type, 'remedial_variant')
        self.assertEqual(render_plan.source.source_id, 'variant-1')
        self.assertEqual(render_plan.render_target.renderer_type, 'pdf')
        self.assertEqual(
            render_plan.recipe.section_types,
            (
                HEADER_SECTION,
                'original_mistakes',
                PAGE_BREAK_SECTION,
                'training_tasks',
                PAGE_BREAK_SECTION,
                ANSWERS_SECTION,
                PAGE_BREAK_SECTION,
                SHORT_SOLUTIONS_SECTION,
            ),
        )

    def test_render_remedial_sheet_uses_recipe_renderer_dependency(self):
        service = FakeDocumentEngine()
        use_case = RenderRemedialSheetDocumentUseCase(
            render_document_from_recipe_use_case=recipe_renderer(service),
            remedial_repo=FakeWorkRepository(),
        )

        result = use_case.execute(
            RenderRemedialSheetDocumentRequest(
                variant_id='variant-1',
                render_target=RenderTarget(renderer_type='pdf'),
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(service.render_request.source.source_id, 'variant-1')

    def test_render_remedial_sheet_document_uses_request_presentation_profile(self):
        service = FakeDocumentEngine()
        presentation_profile_repo = FakePresentationProfileRepository()
        use_case = RenderRemedialSheetDocumentUseCase(
            render_document_from_recipe_use_case=recipe_renderer(service),
            remedial_repo=FakeWorkRepository(),
            presentation_profile_repo=presentation_profile_repo,
        )
        presentation_profile = DocumentPresentationProfile(
            name='Кастомная работа над ошибками',
            document_type='remedial_sheet',
            presentation=DocumentPresentation(
                custom_latex_preamble='\\usepackage{microtype}',
            ),
        )

        result = use_case.execute(
            RenderRemedialSheetDocumentRequest(
                variant_id='variant-1',
                render_target=RenderTarget(renderer_type='pdf'),
                presentation_profile=presentation_profile,
            )
        )

        self.assertTrue(result.success)
        render_plan = service.render_request
        self.assertEqual(
            render_plan.recipe.section_types,
            (
                HEADER_SECTION,
                'original_mistakes',
                PAGE_BREAK_SECTION,
                'training_tasks',
                PAGE_BREAK_SECTION,
                ANSWERS_SECTION,
                PAGE_BREAK_SECTION,
                SHORT_SOLUTIONS_SECTION,
            ),
        )
        self.assertEqual(
            render_plan.recipe.presentation.custom_latex_preamble,
            '\\usepackage{microtype}',
        )

    def test_render_remedial_sheet_without_profile_uses_builtin_presentation(self):
        service = FakeDocumentEngine()
        presentation_profile_repo = FakePresentationProfileRepository()
        use_case = RenderRemedialSheetDocumentUseCase(
            render_document_from_recipe_use_case=recipe_renderer(service),
            remedial_repo=FakeWorkRepository(),
            presentation_profile_repo=presentation_profile_repo,
        )

        result = use_case.execute(
            RenderRemedialSheetDocumentRequest(
                variant_id='variant-1',
                render_target=RenderTarget(renderer_type='pdf'),
            )
        )

        self.assertTrue(result.success)
        render_plan = service.render_request
        self.assertEqual(
            render_plan.recipe.section_types,
            (
                HEADER_SECTION,
                'original_mistakes',
                PAGE_BREAK_SECTION,
                'training_tasks',
                PAGE_BREAK_SECTION,
                ANSWERS_SECTION,
                PAGE_BREAK_SECTION,
                SHORT_SOLUTIONS_SECTION,
            ),
        )
        self.assertEqual(render_plan.recipe.presentation.custom_css, '')

    def test_render_remedial_sheet_document_uses_selected_presentation_profile_id(
        self,
    ):
        service = FakeDocumentEngine()
        presentation_profile_repo = FakePresentationProfileRepository()
        presentation_profile_repo.presentation_profiles_by_id[('template-rno', 'remedial_sheet')] = (
            DocumentPresentationProfile(
                name='Selected remedial',
                document_type='remedial_sheet',
                presentation_profile_id='template-rno',
                presentation=DocumentPresentation(
                    custom_css='.student-name { font-weight: bold; }',
                ),
            )
        )
        use_case = RenderRemedialSheetDocumentUseCase(
            render_document_from_recipe_use_case=recipe_renderer(service),
            remedial_repo=FakeWorkRepository(),
            presentation_profile_repo=presentation_profile_repo,
        )

        result = use_case.execute(
            RenderRemedialSheetDocumentRequest(
                variant_id='variant-1',
                render_target=RenderTarget(renderer_type='pdf'),
                presentation_profile_id='template-rno',
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(
            presentation_profile_repo.requested_presentation_profile_ids,
            [('template-rno', 'remedial_sheet')],
        )
        self.assertEqual(
            service.render_request.recipe.section_types,
            (
                HEADER_SECTION,
                'original_mistakes',
                PAGE_BREAK_SECTION,
                'training_tasks',
                PAGE_BREAK_SECTION,
                ANSWERS_SECTION,
                PAGE_BREAK_SECTION,
                SHORT_SOLUTIONS_SECTION,
            ),
        )
        self.assertEqual(
            service.render_request.recipe.presentation.custom_css,
            '.student-name { font-weight: bold; }',
        )

    def test_render_remedial_sheet_document_handles_empty_files(self):
        service = FakeDocumentEngine()
        service.remedial_document = GeneratedDocument(file_type='pdf')
        use_case = RenderRemedialSheetDocumentUseCase(
            render_document_from_recipe_use_case=recipe_renderer(service),
            remedial_repo=FakeWorkRepository(),
        )

        result = use_case.execute(
            RenderRemedialSheetDocumentRequest(
                variant_id='variant-1',
                render_target=RenderTarget(),
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'empty')

    def test_render_remedial_sheet_document_rejects_unsupported_renderer(self):
        service = FakeDocumentEngine()
        use_case = RenderRemedialSheetDocumentUseCase(
            render_document_from_recipe_use_case=recipe_renderer(service),
            remedial_repo=FakeWorkRepository(),
        )

        result = use_case.execute(
            RenderRemedialSheetDocumentRequest(
                variant_id='variant-1',
                render_target=RenderTarget(renderer_type='docx'),
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER)
        self.assertEqual(result.renderer_type, 'docx')
        self.assertIsNone(service.render_request)

    def test_render_remedial_sheet_document_rejects_non_remedial_variant(self):
        service = FakeDocumentEngine()
        use_case = RenderRemedialSheetDocumentUseCase(
            render_document_from_recipe_use_case=recipe_renderer(service),
            remedial_repo=FakeWorkRepository(variant_type='regular'),
        )

        result = use_case.execute(
            RenderRemedialSheetDocumentRequest(
                variant_id='variant-1',
                render_target=RenderTarget(),
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'not_remedial')
        self.assertIsNone(service.render_request)

    def test_render_remedial_sheet_document_rejects_unsigned_variant(self):
        service = FakeDocumentEngine()
        use_case = RenderRemedialSheetDocumentUseCase(
            render_document_from_recipe_use_case=recipe_renderer(service),
            remedial_repo=FakeWorkRepository(
                remedial_sheet_data=SimpleNamespace(student=None),
            ),
        )

        result = use_case.execute(
            RenderRemedialSheetDocumentRequest(
                variant_id='variant-1',
                render_target=RenderTarget(),
            )
        )

        self.assertEqual(
            result.status,
            DOCUMENT_RENDER_STATUS_NOT_PERSONALIZED,
        )
        self.assertIsNone(service.render_request)

    def test_render_remedial_sheet_document_handles_missing_variant(self):
        service = FakeDocumentEngine()
        use_case = RenderRemedialSheetDocumentUseCase(
            render_document_from_recipe_use_case=recipe_renderer(service),
            remedial_repo=FakeWorkRepository(variant_type=None),
        )

        result = use_case.execute(
            RenderRemedialSheetDocumentRequest(
                variant_id='variant-1',
                render_target=RenderTarget(),
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'not_found')
        self.assertIsNone(service.render_request)

    def test_render_remedial_sheet_batch_document_builds_one_batch_plan(self):
        work_repo = FakeWorkRepository(
            work_name='Работа над ошибками',
            remedial_variant_ids=['variant-1', 'variant-2'],
        )
        service = FakeDocumentEngine()
        use_case = RenderRemedialSheetBatchDocumentUseCase(
            work_repo=work_repo,
            remedial_repo=work_repo,
            render_document_from_recipe_use_case=recipe_renderer(service),
        )

        result = use_case.execute(
            RenderRemedialSheetBatchDocumentRequest(
                work_id='work-1',
                render_target=RenderTarget(renderer_type='pdf'),
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.file_type, 'pdf')
        self.assertEqual(result.source_name, 'Работа над ошибками')
        self.assertEqual(work_repo.work_name_request, 'work-1')
        self.assertEqual(work_repo.remedial_variant_ids_request, 'work-1')
        self.assertEqual(result.files[0].filename, 'remedial.pdf')
        render_plan = service.render_request
        self.assertEqual(render_plan.source.source_type, 'remedial_work')
        self.assertEqual(render_plan.source.source_id, 'work-1')
        self.assertEqual(
            render_plan.recipe.section_types,
            (
                HEADER_SECTION,
                'original_mistakes',
                PAGE_BREAK_SECTION,
                'training_tasks',
                PAGE_BREAK_SECTION,
                ANSWERS_SECTION,
                PAGE_BREAK_SECTION,
                SHORT_SOLUTIONS_SECTION,
                PAGE_BREAK_SECTION,
                HEADER_SECTION,
                'original_mistakes',
                PAGE_BREAK_SECTION,
                'training_tasks',
                PAGE_BREAK_SECTION,
                ANSWERS_SECTION,
                PAGE_BREAK_SECTION,
                SHORT_SOLUTIONS_SECTION,
            ),
        )
        self.assertEqual(
            [
                section.options.get('variant_id')
                for section in render_plan.recipe.sections
                if section.section_type != 'page_break'
            ],
            [
                'variant-1',
                'variant-1',
                'variant-1',
                'variant-1',
                'variant-1',
                'variant-2',
                'variant-2',
                'variant-2',
                'variant-2',
                'variant-2',
            ],
        )

    def test_render_remedial_sheet_batch_document_uses_presentation_profile(self):
        work_repo = FakeWorkRepository(
            work_name='Работа над ошибками',
            remedial_variant_ids=['variant-1'],
        )
        service = FakeDocumentEngine()
        use_case = RenderRemedialSheetBatchDocumentUseCase(
            work_repo=work_repo,
            remedial_repo=work_repo,
            render_document_from_recipe_use_case=recipe_renderer(service),
        )
        presentation_profile = DocumentPresentationProfile(
            name='Профиль РнО',
            document_type='remedial_sheet',
            presentation=DocumentPresentation(
                custom_css='.remedial-sheet { break-after: page; }',
            ),
        )

        result = use_case.execute(
            RenderRemedialSheetBatchDocumentRequest(
                work_id='work-1',
                render_target=RenderTarget(renderer_type='pdf'),
                presentation_profile=presentation_profile,
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(
            service.render_request.recipe.section_types,
            (
                HEADER_SECTION,
                'original_mistakes',
                PAGE_BREAK_SECTION,
                'training_tasks',
                PAGE_BREAK_SECTION,
                ANSWERS_SECTION,
                PAGE_BREAK_SECTION,
                SHORT_SOLUTIONS_SECTION,
            ),
        )
        self.assertEqual(
            service.render_request.recipe.presentation.custom_css,
            '.remedial-sheet { break-after: page; }',
        )

    def test_render_remedial_sheet_batch_document_handles_missing_work(self):
        service = FakeDocumentEngine()
        work_repo = FakeWorkRepository(work_name=None)
        use_case = RenderRemedialSheetBatchDocumentUseCase(
            work_repo=work_repo,
            remedial_repo=work_repo,
            render_document_from_recipe_use_case=recipe_renderer(service),
        )

        result = use_case.execute(
            RenderRemedialSheetBatchDocumentRequest(
                work_id='missing-work',
                render_target=RenderTarget(renderer_type='pdf'),
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'not_found')
        self.assertIsNone(service.render_request)

    def test_render_remedial_sheet_batch_document_handles_empty_work(self):
        work_repo = FakeWorkRepository(
            work_name='Работа над ошибками',
            remedial_variant_ids=[],
        )
        service = FakeDocumentEngine()
        use_case = RenderRemedialSheetBatchDocumentUseCase(
            work_repo=work_repo,
            remedial_repo=work_repo,
            render_document_from_recipe_use_case=recipe_renderer(service),
        )

        result = use_case.execute(
            RenderRemedialSheetBatchDocumentRequest(
                work_id='work-1',
                render_target=RenderTarget(renderer_type='pdf'),
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'empty')
        self.assertEqual(result.source_name, 'Работа над ошибками')
        self.assertIsNone(service.render_request)

    def test_render_remedial_sheet_batch_document_handles_empty_rendered_file(self):
        work_repo = FakeWorkRepository(
            work_name='Работа над ошибками',
            remedial_variant_ids=['variant-1', 'variant-2'],
        )
        service = FakeDocumentEngine()
        service.remedial_document = GeneratedDocument(file_type='pdf')
        use_case = RenderRemedialSheetBatchDocumentUseCase(
            work_repo=work_repo,
            remedial_repo=work_repo,
            render_document_from_recipe_use_case=recipe_renderer(service),
        )

        result = use_case.execute(
            RenderRemedialSheetBatchDocumentRequest(
                work_id='work-1',
                render_target=RenderTarget(renderer_type='pdf'),
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'empty')
        self.assertEqual(result.files, [])

    def test_get_rendered_document_file_delegates_to_service(self):
        service = FakeRenderedDocumentFileStore()
        use_case = GetRenderedDocumentFileUseCase(
            file_store=service,
        )

        result = use_case.execute(
            GetRenderedDocumentFileRequest(
                file_type='html',
                filename='work.html',
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.file.content, b'html')
        self.assertEqual(service.file_request, ('html', 'work.html'))

    def test_get_rendered_document_file_requires_file_store(self):
        with self.assertRaisesRegex(
            ValueError,
            'Rendered document file store is required.',
        ):
            GetRenderedDocumentFileUseCase()

    def test_get_rendered_document_file_accepts_file_store_keyword(self):
        service = FakeRenderedDocumentFileStore()
        use_case = GetRenderedDocumentFileUseCase(file_store=service)

        result = use_case.execute(
            GetRenderedDocumentFileRequest(
                file_type='html',
                filename='work.html',
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(service.file_request, ('html', 'work.html'))
