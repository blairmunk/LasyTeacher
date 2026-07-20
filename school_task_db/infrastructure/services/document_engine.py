"""Django document engine."""

from core_logic.entities.document_rendering import (
    GeneratedDocument,
    GeneratedFileResult,
)
from core_logic.interfaces.document_engine import IDocumentEngine
from core_logic.services.document_builder import RecipeDocumentBuilder
from core_logic.value_objects.document_render_plan import (
    DocumentRenderRequest,
    build_remedial_sheet_document_render_plan,
    build_work_document_render_plan,
)
from infrastructure.services.document_renderer_registry_factory import (
    build_legacy_document_renderer_registry_from_adapters,
)
from infrastructure.services.django_document_source_provider import (
    DjangoDocumentSourceProvider,
)
from infrastructure.services.legacy_document_file_renderer import (
    LegacyDocumentFileRenderer,
)
from infrastructure.services.legacy_document_render_router import (
    LegacyDocumentRenderRouter,
)
from infrastructure.services.rendered_document_file_store import (
    RenderedDocumentFileStore,
)
from infrastructure.services.sectioned_document_defaults import (
    build_sectioned_document_components_with_legacy_fallback,
)


class DjangoDocumentEngine(IDocumentEngine):
    @classmethod
    def with_sectioned_renderers(
        cls,
        get_remedial_sheet_data_use_case=None,
        source_provider=None,
        file_store=None,
        legacy_file_renderer=None,
        template_renderer=None,
        pdf_generator_factory=None,
    ):
        source_provider = source_provider or DjangoDocumentSourceProvider()
        file_store = file_store or RenderedDocumentFileStore()
        legacy_file_renderer = (
            legacy_file_renderer
            or LegacyDocumentFileRenderer(get_remedial_sheet_data_use_case)
        )
        get_remedial_sheet_data = (
            get_remedial_sheet_data_use_case.execute
            if get_remedial_sheet_data_use_case
            else None
        )
        components = build_sectioned_document_components_with_legacy_fallback(
            file_store=file_store,
            get_work_source=source_provider.get_work_source,
            get_remedial_source=source_provider.get_remedial_source,
            legacy_file_renderer=legacy_file_renderer,
            get_remedial_sheet_data=get_remedial_sheet_data,
            template_renderer=template_renderer,
            pdf_generator_factory=pdf_generator_factory,
        )
        return cls(
            get_remedial_sheet_data_use_case=get_remedial_sheet_data_use_case,
            document_builder=components.document_builder,
            document_renderer_registry=components.document_renderer_registry,
            legacy_file_renderer=legacy_file_renderer,
            source_provider=source_provider,
            file_store=file_store,
        )

    def __init__(
        self,
        get_remedial_sheet_data_use_case=None,
        document_builder=None,
        document_renderer_registry=None,
        legacy_file_renderer=None,
        legacy_render_router=None,
        get_work_source=None,
        get_remedial_source=None,
        source_provider=None,
        file_store=None,
        section_payload_builder_registry=None,
    ):
        self.source_provider = source_provider or DjangoDocumentSourceProvider()
        self.file_store = file_store or RenderedDocumentFileStore()
        self.document_builder = document_builder or RecipeDocumentBuilder(
            section_payload_builder_registry=section_payload_builder_registry,
        )
        self.get_work_source = (
            get_work_source
            or self.source_provider.get_work_source
        )
        self.get_remedial_source = (
            get_remedial_source
            or self.source_provider.get_remedial_source
        )
        self.legacy_file_renderer = (
            legacy_file_renderer
            or LegacyDocumentFileRenderer(get_remedial_sheet_data_use_case)
        )
        self.legacy_render_router = (
            legacy_render_router
            or LegacyDocumentRenderRouter(
                legacy_file_renderer=self.legacy_file_renderer,
                file_store=self.file_store,
            )
        )
        self.document_renderer_registry = (
            document_renderer_registry
            or build_legacy_document_renderer_registry_from_adapters(
                file_store=self.file_store,
                get_work_source=self.get_work_source,
                get_remedial_source=self.get_remedial_source,
                legacy_file_renderer=self.legacy_file_renderer,
            )
        )

    def render_work_document(
        self,
        work_id: str,
        options,
        render_plan=None,
    ) -> GeneratedDocument:
        planned_document = self._render_from_plan(render_plan)
        if planned_document is not None:
            return planned_document

        work = self.get_work_source(work_id)
        return self._render_legacy_work_document(
            work,
            options,
        )

    def _render_legacy_work_document(
        self,
        work,
        options,
    ) -> GeneratedDocument:
        return self.legacy_render_router.render_work(work, options)

    def generate_work(
        self,
        work_id: str,
        options,
        render_plan=None,
    ) -> GeneratedDocument:
        work = self.get_work_source(work_id)
        return self.render_work_document(
            work_id=str(work.pk),
            options=options,
            render_plan=render_plan or build_work_document_render_plan(
                work_id=str(work.pk),
                work_name=work.name,
                options=options,
            ),
        )

    def render_remedial_sheet_document(
        self,
        variant_id: str,
        options,
        render_plan=None,
    ) -> GeneratedDocument:
        planned_document = self._render_from_plan(render_plan)
        if planned_document is not None:
            return planned_document

        variant = self.get_remedial_source(variant_id)
        return self._render_legacy_remedial_sheet_document(
            variant,
            options,
        )

    def _render_legacy_remedial_sheet_document(
        self,
        variant,
        options,
    ) -> GeneratedDocument:
        return self.legacy_render_router.render_remedial_sheet(variant, options)

    def generate_remedial_sheet(
        self,
        variant_id: str,
        options,
        render_plan=None,
    ) -> GeneratedDocument:
        variant = self.get_remedial_source(variant_id)
        return self.render_remedial_sheet_document(
            variant_id=str(variant.pk),
            options=options,
            render_plan=render_plan or build_remedial_sheet_document_render_plan(
                variant_id=str(variant.pk),
                options=options,
            ),
        )

    def get_rendered_file(
        self,
        file_type: str,
        filename: str,
    ) -> GeneratedFileResult:
        return self.file_store.get_file(file_type, filename)

    def get_generated_file(
        self,
        file_type: str,
        filename: str,
    ) -> GeneratedFileResult:
        return self.get_rendered_file(file_type, filename)

    def _build_document(self, render_plan=None):
        if render_plan is None:
            return None
        return self.document_builder.build(
            render_plan.source,
            render_plan.recipe,
            render_plan.render_target,
        )

    def _render_from_plan(self, render_plan=None):
        if render_plan is None:
            return None

        render_target = render_plan.render_target
        document = self._build_document(render_plan)
        if document is None:
            return None

        return self.document_renderer_registry.render(
            DocumentRenderRequest(
                document=document,
                render_target=render_target,
            )
        )


DjangoDocumentRenderingService = DjangoDocumentEngine
