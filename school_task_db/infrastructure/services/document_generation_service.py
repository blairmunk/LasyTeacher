"""Django document generation service."""

from pathlib import Path

from django.template.loader import render_to_string

from core_logic.entities.document_generation import GeneratedDocument
from core_logic.interfaces.document_generation import IDocumentGenerationService


class DjangoDocumentGenerationService(IDocumentGenerationService):
    def __init__(self, get_remedial_sheet_data_use_case):
        self.get_remedial_sheet_data_use_case = get_remedial_sheet_data_use_case

    def generate_work(self, work, options) -> GeneratedDocument:
        generator_type = options.generator_type
        content_config = options.content_config

        if generator_type == 'latex':
            return GeneratedDocument(
                file_type='latex',
                file_paths=self._generate_latex_work(
                    work,
                    content_config,
                    options.pdf_format,
                ),
            )
        if generator_type == 'html':
            return GeneratedDocument(
                file_type='html',
                file_paths=self._generate_html_work(work, content_config),
            )
        return GeneratedDocument(
            file_type='pdf',
            file_paths=self._generate_pdf_work(
                work,
                content_config,
                options.pdf_format,
            ),
        )

    def generate_remedial_sheet(self, variant, options) -> GeneratedDocument:
        content_config = options.content_config
        generator_type = options.generator_type

        if generator_type == 'latex':
            return GeneratedDocument(
                file_type='latex',
                file_paths=self._generate_remedial_latex(
                    variant,
                    content_config,
                    options.pdf_format,
                ),
            )
        if generator_type == 'html':
            return GeneratedDocument(
                file_type='html',
                file_paths=self._generate_remedial_html(
                    variant,
                    content_config,
                ),
            )
        return GeneratedDocument(
            file_type='pdf',
            file_paths=self._generate_remedial_pdf(
                variant,
                content_config,
                options.pdf_format,
            ),
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
            sheet_data.student.get_short_name()
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
