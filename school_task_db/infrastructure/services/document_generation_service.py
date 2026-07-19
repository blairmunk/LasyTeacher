"""Django document generation service."""

import mimetypes
from pathlib import Path

from django.template.loader import render_to_string

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
    ):
        self.get_remedial_sheet_data_use_case = get_remedial_sheet_data_use_case
        self.document_builder = document_builder or RecipeDocumentBuilder()
        self.document_renderer_registry = (
            document_renderer_registry
            or build_legacy_document_renderer_registry(
                document_from_paths=self._document_from_paths,
                generate_latex_work=self._generate_latex_work,
                generate_html_work=self._generate_html_work,
                generate_pdf_work=self._generate_pdf_work,
                generate_remedial_latex=self._generate_remedial_latex,
                generate_remedial_html=self._generate_remedial_html,
                generate_remedial_pdf=self._generate_remedial_pdf,
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
                file_paths=self._generate_latex_work(
                    work,
                    content_config,
                    render_target.page_format,
                ),
            )
        if renderer_type == 'html':
            return self._document_from_paths(
                file_type='html',
                file_paths=self._generate_html_work(work, content_config),
            )
        return self._document_from_paths(
            file_type='pdf',
            file_paths=self._generate_pdf_work(
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
                file_paths=self._generate_remedial_latex(
                    variant,
                    content_config,
                    render_target.page_format,
                ),
            )
        if renderer_type == 'html':
            return self._document_from_paths(
                file_type='html',
                file_paths=self._generate_remedial_html(
                    variant,
                    content_config,
                ),
            )
        return self._document_from_paths(
            file_type='pdf',
            file_paths=self._generate_remedial_pdf(
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

    def _generate_latex_work(self, work, content_config, pdf_format='A4'):
        from latex_generator.generators.work_generator import WorkLatexGenerator

        content_config['page_format'] = pdf_format
        generator = WorkLatexGenerator(output_dir='web_latex_output')
        generator._content_config = content_config

        if self._should_include_answers(content_config):
            return generator.generate_with_answers(work)
        return generator.generate(work)

    def _generate_html_work(self, work, content_config):
        from html_generator.generators.work_generator import WorkHtmlGenerator

        generator = WorkHtmlGenerator(output_dir='web_html_output')
        generator._content_config = content_config

        if self._should_include_answers(content_config):
            return generator.generate_with_answers(work)
        return generator.generate(work)

    def _generate_pdf_work(self, work, content_config, pdf_format='A4'):
        import tempfile

        from html_generator.generators.work_generator import WorkHtmlGenerator
        from pdf_generator.generators.html_to_pdf import HtmlToPdfGenerator

        with tempfile.TemporaryDirectory() as temp_dir:
            html_gen = WorkHtmlGenerator(output_dir=temp_dir)
            html_gen._content_config = content_config

            if self._should_include_answers(content_config):
                html_files = html_gen.generate_with_answers(work)
            else:
                html_files = html_gen.generate(work)

            pdf_gen = HtmlToPdfGenerator(format=pdf_format, wait_for_mathjax=True)
            pdf_files = []
            output_dir = Path('web_pdf_output')
            output_dir.mkdir(parents=True, exist_ok=True)

            for html_file in html_files:
                html_path = Path(html_file)
                pdf_path = output_dir / (html_path.stem + '.pdf')
                result = pdf_gen.generate_pdf(html_path, pdf_path)
                pdf_files.append(str(result))

        return pdf_files

    def _generate_remedial_latex(
        self,
        variant,
        content_config,
        pdf_format='A4',
    ):
        from latex_generator.generators.remedial_generator import (
            RemedialSheetLatexGenerator,
        )

        content_config['page_format'] = pdf_format
        generator = RemedialSheetLatexGenerator(output_dir='web_latex_output')
        return generator.generate_for_variant(
            variant,
            output_format='pdf',
            content_config=content_config,
        )

    def _generate_remedial_html(self, variant, content_config):
        sheet_data = self.get_remedial_sheet_data_use_case.execute(
            str(variant.pk),
        )

        html_content = render_to_string('works/remedial_sheet_print.html', {
            'variant': sheet_data.variant,
            'student': sheet_data.student,
            'source_work': sheet_data.source_work,
            'mark': sheet_data.mark,
            'original_tasks': sheet_data.original_tasks,
            'new_tasks': sheet_data.new_tasks,
            'show_solutions': content_config.get('include_short_solutions', True),
            'show_full_solutions': content_config.get(
                'include_full_solutions',
                False,
            ),
            'show_answers': content_config.get('include_answers', False),
        })

        output_dir = Path('web_html_output')
        output_dir.mkdir(parents=True, exist_ok=True)

        student_name = (
            sheet_data.student.short_name
            if sheet_data.student
            else 'unknown'
        )
        filepath = output_dir / f'remedial_{student_name}.html'
        filepath.write_text(html_content, encoding='utf-8')

        return [str(filepath)]

    def _generate_remedial_pdf(self, variant, content_config, pdf_format='A4'):
        from pdf_generator.generators.html_to_pdf import HtmlToPdfGenerator

        html_files = self._generate_remedial_html(variant, content_config)
        if not html_files:
            return []

        pdf_gen = HtmlToPdfGenerator(format=pdf_format, wait_for_mathjax=True)
        pdf_files = []
        output_dir = Path('web_pdf_output')
        output_dir.mkdir(parents=True, exist_ok=True)

        for html_file in html_files:
            html_path = Path(html_file)
            pdf_path = output_dir / (html_path.stem + '.pdf')
            result = pdf_gen.generate_pdf(html_path, pdf_path)
            pdf_files.append(str(result))

        return pdf_files

    def _should_include_answers(self, content_config):
        return (
            content_config['include_answers']
            or content_config['include_short_solutions']
            or content_config['include_full_solutions']
        )
