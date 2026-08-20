"""Document subsystem wiring for the application dependency container."""

from core_logic.use_cases.create_presentation_profile import (
    CreatePresentationProfileUseCase,
)
from core_logic.use_cases.get_document_section_catalog import (
    GetDocumentSectionCatalogUseCase,
)
from core_logic.use_cases.get_document_type_catalog import (
    GetDocumentTypeCatalogUseCase,
)
from core_logic.use_cases.get_presentation_profile import (
    GetPresentationProfileUseCase,
)
from core_logic.use_cases.get_presentation_profile_editor_data import (
    GetPresentationProfileEditorDataUseCase,
)
from core_logic.use_cases.get_presentation_profile_form_data import (
    GetPresentationProfileFormDataUseCase,
)
from core_logic.use_cases.get_presentation_profile_list import (
    GetPresentationProfileListUseCase,
)
from core_logic.use_cases.get_rendered_document_file import (
    GetRenderedDocumentFileUseCase,
)
from core_logic.use_cases.render_document_from_recipe import (
    RenderDocumentFromRecipeUseCase,
)
from core_logic.use_cases.render_event_performance_report_document import (
    RenderEventPerformanceReportDocumentUseCase,
)
from core_logic.use_cases.render_remedial_sheet_batch_document import (
    RenderRemedialSheetBatchDocumentUseCase,
)
from core_logic.use_cases.render_remedial_sheet_document import (
    RenderRemedialSheetDocumentUseCase,
)
from core_logic.use_cases.render_student_digest_document import (
    RenderStudentDigestDocumentUseCase,
)
from core_logic.use_cases.render_work_document import RenderWorkDocumentUseCase
from core_logic.use_cases.update_presentation_profile import (
    UpdatePresentationProfileUseCase,
)
from infrastructure.forms.presentation_profile_forms import (
    PresentationProfileFormAdapter,
)
from infrastructure.presenters.rendered_document_file import (
    RenderedDocumentFilePresenter,
)
from infrastructure.presenters.report_document import (
    ReportDocumentWebPresenter,
)
from infrastructure.presenters.work_document import WorkDocumentWebPresenter
from infrastructure.repositories.django_presentation_profile_catalog_repo import (
    DjangoPresentationProfileCatalogRepository,
)
from infrastructure.repositories.django_presentation_profile_command_repo import (
    DjangoPresentationProfileCommandRepository,
)
from infrastructure.repositories.django_work_document_repo import (
    DjangoWorkDocumentRepository,
)
from infrastructure.services.document_engine import SectionedDocumentEngine
from infrastructure.services.rendered_document_file_store import (
    RenderedDocumentFileStore,
)
from infrastructure.services.sectioned_document_defaults import (
    build_sectioned_document_components,
)


class DocumentCompositionMixin:
    """Owns infrastructure wiring for sectioned document rendering."""

    def _initialize_document_composition(self):
        self._work_document_repo = None
        self._presentation_profile_catalog_repo = None
        self._presentation_profile_command_repo = None
        self._presentation_profile_form_adapter = None
        self._work_document_web_presenter = None
        self._rendered_document_file_presenter = None
        self._report_document_web_presenter = None
        self._document_engine = None
        self._rendered_document_file_store = None

    @property
    def work_document_repo(self):
        if self._work_document_repo is None:
            self._work_document_repo = DjangoWorkDocumentRepository()
        return self._work_document_repo

    @property
    def presentation_profile_catalog_repo(self):
        if self._presentation_profile_catalog_repo is None:
            self._presentation_profile_catalog_repo = (
                DjangoPresentationProfileCatalogRepository()
            )
        return self._presentation_profile_catalog_repo

    @property
    def presentation_profile_command_repo(self):
        if self._presentation_profile_command_repo is None:
            self._presentation_profile_command_repo = (
                DjangoPresentationProfileCommandRepository()
            )
        return self._presentation_profile_command_repo

    @property
    def presentation_profile_form_adapter(self):
        if self._presentation_profile_form_adapter is None:
            self._presentation_profile_form_adapter = (
                PresentationProfileFormAdapter()
            )
        return self._presentation_profile_form_adapter

    @property
    def work_document_web_presenter(self):
        if self._work_document_web_presenter is None:
            self._work_document_web_presenter = WorkDocumentWebPresenter()
        return self._work_document_web_presenter

    @property
    def rendered_document_file_presenter(self):
        if self._rendered_document_file_presenter is None:
            self._rendered_document_file_presenter = (
                RenderedDocumentFilePresenter()
            )
        return self._rendered_document_file_presenter

    @property
    def report_document_web_presenter(self):
        if self._report_document_web_presenter is None:
            self._report_document_web_presenter = ReportDocumentWebPresenter()
        return self._report_document_web_presenter

    @property
    def document_engine(self):
        if self._document_engine is None:
            components = build_sectioned_document_components(
                work_document_repo=self.work_document_repo,
                get_remedial_sheet_data=(
                    self.get_remedial_sheet_data_use_case().execute
                ),
                get_event_report=(
                    self.get_event_performance_report_use_case().execute
                ),
                get_student_digests=(
                    self.get_student_digests_use_case().execute
                ),
                file_store=self.rendered_document_file_store,
            )
            self._document_engine = SectionedDocumentEngine(
                document_builder=components.document_builder,
                document_renderer_registry=(
                    components.document_renderer_registry
                ),
            )
        return self._document_engine

    @property
    def rendered_document_file_store(self):
        if self._rendered_document_file_store is None:
            self._rendered_document_file_store = RenderedDocumentFileStore()
        return self._rendered_document_file_store

    def get_presentation_profile_list_use_case(self):
        return GetPresentationProfileListUseCase(
            presentation_profile_repo=self.presentation_profile_catalog_repo,
        )

    def get_presentation_profile_use_case(self):
        return GetPresentationProfileUseCase(
            presentation_profile_repo=self.presentation_profile_catalog_repo,
        )

    def create_presentation_profile_use_case(self):
        return CreatePresentationProfileUseCase(
            presentation_profile_repo=self.presentation_profile_command_repo,
        )

    def update_presentation_profile_use_case(self):
        return UpdatePresentationProfileUseCase(
            presentation_profile_repo=self.presentation_profile_command_repo,
        )

    def get_document_section_catalog_use_case(self):
        return GetDocumentSectionCatalogUseCase()

    def get_presentation_profile_editor_data_use_case(self):
        return GetPresentationProfileEditorDataUseCase(
            presentation_profile_repo=self.presentation_profile_catalog_repo,
        )

    def get_presentation_profile_form_data_use_case(self):
        return GetPresentationProfileFormDataUseCase(
            presentation_profile_repo=self.presentation_profile_catalog_repo,
        )

    def get_document_type_catalog_use_case(self):
        return GetDocumentTypeCatalogUseCase()

    def render_work_document_use_case(self):
        return RenderWorkDocumentUseCase(
            work_repo=self.work_document_repo,
            presentation_profile_repo=self.presentation_profile_catalog_repo,
            render_document_from_recipe_use_case=(
                self.render_document_from_recipe_use_case()
            ),
        )

    def render_document_from_recipe_use_case(self):
        return RenderDocumentFromRecipeUseCase(
            document_engine=self.document_engine,
        )

    def render_remedial_sheet_document_use_case(self):
        return RenderRemedialSheetDocumentUseCase(
            remedial_repo=self.remedial_sheet_repo,
            presentation_profile_repo=self.presentation_profile_catalog_repo,
            render_document_from_recipe_use_case=(
                self.render_document_from_recipe_use_case()
            ),
        )

    def render_event_performance_report_document_use_case(self):
        return RenderEventPerformanceReportDocumentUseCase(
            get_event_report_use_case=(
                self.get_event_performance_report_use_case()
            ),
            presentation_profile_repo=self.presentation_profile_catalog_repo,
            render_document_from_recipe_use_case=(
                self.render_document_from_recipe_use_case()
            ),
        )

    def render_student_digest_document_use_case(self):
        return RenderStudentDigestDocumentUseCase(
            get_student_digests_use_case=self.get_student_digests_use_case(),
            presentation_profile_repo=self.presentation_profile_catalog_repo,
            render_document_from_recipe_use_case=(
                self.render_document_from_recipe_use_case()
            ),
        )

    def render_remedial_sheet_batch_document_use_case(self):
        return RenderRemedialSheetBatchDocumentUseCase(
            work_repo=self.work_document_repo,
            remedial_repo=self.remedial_sheet_repo,
            presentation_profile_repo=self.presentation_profile_catalog_repo,
            render_document_from_recipe_use_case=(
                self.render_document_from_recipe_use_case()
            ),
        )

    def get_rendered_document_file_use_case(self):
        return GetRenderedDocumentFileUseCase(
            file_store=self.rendered_document_file_store,
        )
