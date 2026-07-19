"""Legacy file renderers used by document renderer adapters."""

import tempfile
from pathlib import Path

from django.template.loader import render_to_string


class LegacyDocumentFileRenderer:
    def __init__(
        self,
        get_remedial_sheet_data_use_case,
        template_renderer=render_to_string,
        latex_output_dir='web_latex_output',
        html_output_dir='web_html_output',
        pdf_output_dir='web_pdf_output',
        work_file_renderer=None,
        remedial_file_renderer=None,
    ):
        self.work_file_renderer = work_file_renderer or LegacyWorkFileRenderer(
            latex_output_dir=latex_output_dir,
            html_output_dir=html_output_dir,
            pdf_output_dir=pdf_output_dir,
        )
        self.remedial_file_renderer = (
            remedial_file_renderer
            or LegacyRemedialSheetFileRenderer(
                get_remedial_sheet_data_use_case=(
                    get_remedial_sheet_data_use_case
                ),
                template_renderer=template_renderer,
                latex_output_dir=latex_output_dir,
                html_output_dir=html_output_dir,
                pdf_output_dir=pdf_output_dir,
            )
        )

    def render_latex_work(self, work, content_config, page_format='A4'):
        return self.work_file_renderer.render_latex(
            work=work,
            content_config=content_config,
            page_format=page_format,
        )

    def render_html_work(self, work, content_config):
        return self.work_file_renderer.render_html(
            work=work,
            content_config=content_config,
        )

    def render_pdf_work(self, work, content_config, page_format='A4'):
        return self.work_file_renderer.render_pdf(
            work=work,
            content_config=content_config,
            page_format=page_format,
        )

    def render_remedial_latex(
        self,
        variant,
        content_config,
        page_format='A4',
    ):
        return self.remedial_file_renderer.render_latex(
            variant=variant,
            content_config=content_config,
            page_format=page_format,
        )

    def render_remedial_html(self, variant, content_config):
        return self.remedial_file_renderer.render_html(
            variant=variant,
            content_config=content_config,
        )

    def render_remedial_pdf(self, variant, content_config, page_format='A4'):
        return self.remedial_file_renderer.render_pdf(
            variant=variant,
            content_config=content_config,
            page_format=page_format,
        )

    def _render_pdf_files_from_html(self, html_files, pdf_generator):
        return _render_pdf_files_from_html(
            html_files=html_files,
            pdf_generator=pdf_generator,
            pdf_output_dir=self.work_file_renderer.pdf_output_dir,
        )


class LegacyWorkFileRenderer:
    def __init__(
        self,
        latex_output_dir='web_latex_output',
        html_output_dir='web_html_output',
        pdf_output_dir='web_pdf_output',
    ):
        self.latex_output_dir = latex_output_dir
        self.html_output_dir = html_output_dir
        self.pdf_output_dir = pdf_output_dir

    def render_latex(self, work, content_config, page_format='A4'):
        from latex_generator.generators.work_generator import WorkLatexGenerator

        return self._render_work_files(
            generator_class=WorkLatexGenerator,
            output_dir=self.latex_output_dir,
            work=work,
            content_config=content_config,
            page_format=page_format,
        )

    def render_html(self, work, content_config):
        from html_generator.generators.work_generator import WorkHtmlGenerator

        return self._render_work_files(
            generator_class=WorkHtmlGenerator,
            output_dir=self.html_output_dir,
            work=work,
            content_config=content_config,
        )

    def render_pdf(self, work, content_config, page_format='A4'):
        from html_generator.generators.work_generator import WorkHtmlGenerator
        from pdf_generator.generators.html_to_pdf import HtmlToPdfGenerator

        with tempfile.TemporaryDirectory() as temp_dir:
            html_files = self._render_work_files(
                generator_class=WorkHtmlGenerator,
                output_dir=temp_dir,
                work=work,
                content_config=content_config,
            )

            return _render_pdf_files_from_html(
                html_files=html_files,
                pdf_generator=HtmlToPdfGenerator(
                    format=page_format,
                    wait_for_mathjax=True,
                ),
                pdf_output_dir=self.pdf_output_dir,
            )

    def _should_include_answers(self, content_config):
        return (
            content_config['include_answers']
            or content_config['include_short_solutions']
            or content_config['include_full_solutions']
        )

    def _render_work_files(
        self,
        generator_class,
        output_dir,
        work,
        content_config,
        page_format=None,
    ):
        if page_format is not None:
            content_config['page_format'] = page_format

        generator = generator_class(output_dir=output_dir)
        generator._content_config = content_config

        if self._should_include_answers(content_config):
            return generator.generate_with_answers(work)
        return generator.generate(work)


class LegacyRemedialSheetFileRenderer:
    def __init__(
        self,
        get_remedial_sheet_data_use_case,
        template_renderer=render_to_string,
        latex_output_dir='web_latex_output',
        html_output_dir='web_html_output',
        pdf_output_dir='web_pdf_output',
    ):
        self.get_remedial_sheet_data_use_case = get_remedial_sheet_data_use_case
        self.template_renderer = template_renderer
        self.latex_output_dir = latex_output_dir
        self.html_output_dir = html_output_dir
        self.pdf_output_dir = pdf_output_dir

    def render_latex(self, variant, content_config, page_format='A4'):
        from latex_generator.generators.remedial_generator import (
            RemedialSheetLatexGenerator,
        )

        content_config['page_format'] = page_format
        generator = RemedialSheetLatexGenerator(output_dir=self.latex_output_dir)
        return generator.generate_for_variant(
            variant,
            output_format='pdf',
            content_config=content_config,
        )

    def render_html(self, variant, content_config):
        sheet_data = self.get_remedial_sheet_data_use_case.execute(
            str(variant.pk),
        )

        html_content = self.template_renderer(
            'works/remedial_sheet_print.html',
            self._remedial_template_context(sheet_data, content_config),
        )

        output_dir = Path(self.html_output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        student_name = (
            sheet_data.student.short_name
            if sheet_data.student
            else 'unknown'
        )
        filepath = output_dir / f'remedial_{student_name}.html'
        filepath.write_text(html_content, encoding='utf-8')

        return [str(filepath)]

    def render_pdf(self, variant, content_config, page_format='A4'):
        from pdf_generator.generators.html_to_pdf import HtmlToPdfGenerator

        html_files = self.render_html(variant, content_config)
        if not html_files:
            return []

        return _render_pdf_files_from_html(
            html_files=html_files,
            pdf_generator=HtmlToPdfGenerator(
                format=page_format,
                wait_for_mathjax=True,
            ),
            pdf_output_dir=self.pdf_output_dir,
        )

    def _remedial_template_context(self, sheet_data, content_config):
        return {
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
        }


def _render_pdf_files_from_html(html_files, pdf_generator, pdf_output_dir):
    pdf_files = []
    output_dir = Path(pdf_output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for html_file in html_files:
        html_path = Path(html_file)
        pdf_path = output_dir / (html_path.stem + '.pdf')
        result = pdf_generator.generate_pdf(html_path, pdf_path)
        pdf_files.append(str(result))

    return pdf_files
