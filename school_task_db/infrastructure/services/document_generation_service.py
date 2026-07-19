"""Django document generation service."""

import mimetypes
from pathlib import Path

from core_logic.entities.document_generation import (
    GeneratedDocument,
    GeneratedDocumentFile,
    GeneratedFile,
    GeneratedFileResult,
)
from core_logic.interfaces.document_generation import IDocumentGenerationService
from core_logic.services.document_builder import RecipeDocumentBuilder
from core_logic.value_objects.document_render_plan import (
    DocumentRenderRequest,
    build_remedial_sheet_document_render_plan,
    build_work_document_render_plan,
)
from infrastructure.services.document_renderer_registry_factory import (
    build_legacy_document_renderer_registry,
)
from infrastructure.services.legacy_document_file_renderer import (
    LegacyDocumentFileRenderer,
)
from works.models import Variant, Work


class DjangoDocumentGenerationService(IDocumentGenerationService):
    type_to_output_dir = {
        'latex': 'web_latex_output',
        'html': 'web_html_output',
        'pdf': 'web_pdf_output',
    }

    def __init__(
        self,
        get_remedial_sheet_data_use_case,
        document_builder=None,
        document_renderer_registry=None,
        legacy_file_renderer=None,
    ):
        self.get_remedial_sheet_data_use_case = get_remedial_sheet_data_use_case
        self.document_builder = document_builder or RecipeDocumentBuilder()
        self.legacy_file_renderer = (
            legacy_file_renderer
            or LegacyDocumentFileRenderer(get_remedial_sheet_data_use_case)
        )
        self.document_renderer_registry = (
            document_renderer_registry
            or build_legacy_document_renderer_registry(
                document_from_paths=self._document_from_paths,
                render_latex_work_files=(
                    self.legacy_file_renderer.render_latex_work
                ),
                render_html_work_files=self.legacy_file_renderer.render_html_work,
                render_pdf_work_files=self.legacy_file_renderer.render_pdf_work,
                render_remedial_latex_files=(
                    self.legacy_file_renderer.render_remedial_latex
                ),
                render_remedial_html_files=(
                    self.legacy_file_renderer.render_remedial_html
                ),
                render_remedial_pdf_files=(
                    self.legacy_file_renderer.render_remedial_pdf
                ),
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

        work = Work.objects.get(pk=work_id)
        return self._render_legacy_work_document(
            work,
            options,
        )

    def _render_legacy_work_document(
        self,
        work,
        options,
    ) -> GeneratedDocument:
        render_target = options.render_target
        renderer_type = render_target.renderer_type
        content_config = options.content_config

        if renderer_type == 'latex':
            return self._document_from_paths(
                file_type='latex',
                file_paths=self.legacy_file_renderer.render_latex_work(
                    work,
                    content_config,
                    render_target.page_format,
                ),
            )
        if renderer_type == 'html':
            return self._document_from_paths(
                file_type='html',
                file_paths=self.legacy_file_renderer.render_html_work(
                    work,
                    content_config,
                ),
            )
        return self._document_from_paths(
            file_type='pdf',
            file_paths=self.legacy_file_renderer.render_pdf_work(
                work,
                content_config,
                render_target.page_format,
            ),
        )

    def generate_work(
        self,
        work_id: str,
        options,
        render_plan=None,
    ) -> GeneratedDocument:
        work = Work.objects.get(pk=work_id)
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

        variant = Variant.objects.get(pk=variant_id)
        return self._render_legacy_remedial_sheet_document(
            variant,
            options,
        )

    def _render_legacy_remedial_sheet_document(
        self,
        variant,
        options,
    ) -> GeneratedDocument:
        render_target = options.render_target
        content_config = options.content_config
        renderer_type = render_target.renderer_type

        if renderer_type == 'latex':
            return self._document_from_paths(
                file_type='latex',
                file_paths=self.legacy_file_renderer.render_remedial_latex(
                    variant,
                    content_config,
                    render_target.page_format,
                ),
            )
        if renderer_type == 'html':
            return self._document_from_paths(
                file_type='html',
                file_paths=self.legacy_file_renderer.render_remedial_html(
                    variant,
                    content_config,
                ),
            )
        return self._document_from_paths(
            file_type='pdf',
            file_paths=self.legacy_file_renderer.render_remedial_pdf(
                variant,
                content_config,
                render_target.page_format,
            ),
        )

    def generate_remedial_sheet(
        self,
        variant_id: str,
        options,
        render_plan=None,
    ) -> GeneratedDocument:
        variant = Variant.objects.get(pk=variant_id)
        return self.render_remedial_sheet_document(
            variant_id=str(variant.pk),
            options=options,
            render_plan=render_plan or build_remedial_sheet_document_render_plan(
                variant_id=str(variant.pk),
                options=options,
            ),
        )

    def get_generated_file(
        self,
        file_type: str,
        filename: str,
    ) -> GeneratedFileResult:
        output_dir = self.type_to_output_dir.get(file_type)
        if not output_dir:
            return GeneratedFileResult(status='unsupported_type')

        file_path = Path(output_dir) / filename
        if not file_path.exists():
            return GeneratedFileResult(status='not_found')

        content_type, _ = mimetypes.guess_type(str(file_path))
        if not content_type:
            content_type = 'application/octet-stream'

        try:
            return GeneratedFileResult(
                status='ready',
                file=GeneratedFile(
                    filename=filename,
                    content=file_path.read_bytes(),
                    content_type=content_type,
                ),
            )
        except OSError:
            return GeneratedFileResult(status='read_error')

    def _document_from_paths(self, file_type: str, file_paths):
        files = []
        for file_path in file_paths:
            path = Path(file_path)
            if path.exists():
                files.append(
                    GeneratedDocumentFile(
                        filename=path.name,
                        size_kb=path.stat().st_size / 1024,
                    )
                )

        return GeneratedDocument(file_type=file_type, files=files)

    def _build_document(self, render_plan=None):
        if render_plan is None:
            return None
        return self.document_builder.build(
            render_plan.source,
            render_plan.recipe,
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
