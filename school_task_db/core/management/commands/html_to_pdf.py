import logging
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from infrastructure.services.html_to_pdf_renderer import HtmlToPdfRenderer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Convert HTML files to PDF through Playwright'

    def add_arguments(self, parser):
        parser.add_argument(
            'input_path',
            help='Path to an HTML file or a directory with HTML files',
        )
        parser.add_argument(
            '--output-dir',
            default='pdf_output',
            help='Directory for generated PDF files',
        )
        parser.add_argument(
            '--format',
            choices=['A4', 'A3', 'Letter', 'Legal'],
            default='A4',
        )
        parser.add_argument(
            '--margin',
            default='1cm',
            help='Page margin',
        )
        parser.add_argument(
            '--no-background',
            action='store_true',
            help='Do not print background images and colors',
        )
        parser.add_argument(
            '--skip-mathjax',
            action='store_true',
            help='Do not wait for MathJax',
        )

    def handle(self, *args, **options):
        input_path = Path(options['input_path'])
        output_dir = options['output_dir']

        if not input_path.exists():
            raise CommandError(f'Path does not exist: {input_path}')

        renderer = HtmlToPdfRenderer(
            format=options['format'],
            print_background=not options['no_background'],
            wait_for_mathjax=not options['skip_mathjax'],
            margin=self._margin_options(options['margin']),
        )

        try:
            if input_path.is_file():
                self._convert_file(renderer, input_path, output_dir)
            elif input_path.is_dir():
                self._convert_directory(renderer, input_path, output_dir)
        except Exception as exc:
            logger.error('HTML to PDF conversion failed: %s', exc)
            raise CommandError(f'Conversion failed: {exc}') from exc

    def _convert_file(self, renderer, html_path: Path, output_dir):
        if html_path.suffix.lower() != '.html':
            raise CommandError(f'File must have .html extension: {html_path}')

        pdf_path = output_pdf_path(html_path, output_dir)
        self.stdout.write(f'Converting: {html_path.name}')
        result_path = renderer.generate_pdf(html_path, pdf_path)

        if not result_path.exists():
            raise CommandError('PDF file was not created')

        file_size = result_path.stat().st_size / 1024
        self.stdout.write(
            self.style.SUCCESS(
                f'PDF created: {result_path} ({file_size:.1f} KB)'
            )
        )

    def _convert_directory(self, renderer, input_path: Path, output_dir):
        html_files = list(input_path.glob('*.html'))
        if not html_files:
            raise CommandError(f'HTML files not found in directory: {input_path}')

        file_pairs = html_to_pdf_file_pairs(html_files, output_dir)
        if not file_pairs:
            raise CommandError('Valid HTML files were not found')

        self.stdout.write(f'Processing {len(file_pairs)} files...')
        for index, (html_file, pdf_file) in enumerate(file_pairs, 1):
            self.stdout.write(f'  {index}/{len(file_pairs)}: {html_file.name}')
            try:
                result_path = renderer.generate_pdf(html_file, pdf_file)
                file_size = result_path.stat().st_size / 1024
                self.stdout.write(
                    f'    PDF: {result_path.name} ({file_size:.1f} KB)'
                )
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f'    Error: {exc}'))

    def _margin_options(self, margin_value):
        return {
            'top': margin_value,
            'right': margin_value,
            'bottom': margin_value,
            'left': margin_value,
        }


def output_pdf_path(html_file_path: Path, output_dir=None) -> Path:
    html_file_path = Path(html_file_path)
    if not html_file_path.is_absolute():
        html_file_path = html_file_path.resolve()

    output_directory = Path(output_dir or 'pdf_output')
    if not output_directory.is_absolute():
        output_directory = output_directory.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)

    return output_directory / f'{html_file_path.stem}.pdf'


def html_to_pdf_file_pairs(html_files, output_dir=None):
    return [
        (html_file, output_pdf_path(html_file, output_dir))
        for html_file in html_files
        if is_valid_html_file(html_file)
    ]


def is_valid_html_file(html_file_path: Path) -> bool:
    html_file_path = Path(html_file_path)
    if not html_file_path.is_absolute():
        html_file_path = html_file_path.resolve()

    if not html_file_path.exists():
        return False

    try:
        content = html_file_path.read_text(encoding='utf-8').lower()
    except OSError:
        return False

    return all(tag in content for tag in ('<html', '<head', '<body'))
