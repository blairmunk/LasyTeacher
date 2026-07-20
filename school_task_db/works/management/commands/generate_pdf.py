from django.core.management.base import BaseCommand, CommandError

from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_GENERATED,
    DOCUMENT_RENDER_STATUS_NOT_FOUND,
    DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER,
)
from core_logic.use_cases.render_work_document import RenderWorkDocumentRequest
from core_logic.value_objects.content_config import WorkDocumentRenderOptions
from infrastructure.container import container


class Command(BaseCommand):
    help = 'Generate PDF documents through the sectioned document engine'

    def add_arguments(self, parser):
        parser.add_argument('object_type', choices=['work'])
        parser.add_argument('object_id', type=str)
        parser.add_argument('--with-answers', action='store_true')
        parser.add_argument('--output-dir', default='pdf_output')
        parser.add_argument(
            '--keep-html',
            action='store_true',
            help='Deprecated; ignored by the sectioned document engine',
        )
        parser.add_argument(
            '--format',
            choices=['A4', 'A5', 'Letter'],
            default='A4',
        )
        parser.add_argument(
            '--fast',
            action='store_true',
            help='Deprecated; PDF backend settings are configured centrally',
        )
        parser.add_argument(
            '--mathjax-timeout',
            type=int,
            default=8,
            help='Deprecated; PDF backend settings are configured centrally',
        )

    def handle(self, *args, **options):
        if options['object_type'] != 'work':
            raise CommandError(f'Unsupported object type: {options["object_type"]}')

        if options.get('output_dir') != 'pdf_output':
            self.stdout.write(
                self.style.WARNING(
                    '--output-dir is deprecated and ignored by document engine.'
                )
            )
        if options.get('keep_html') or options.get('fast'):
            self.stdout.write(
                self.style.WARNING(
                    '--keep-html and --fast are deprecated and ignored.'
                )
            )

        result = container.render_work_document_use_case().execute(
            RenderWorkDocumentRequest(
                work_id=str(options['object_id']),
                options=WorkDocumentRenderOptions(
                    renderer_type='pdf',
                    pdf_format=options['format'],
                    answer_type=(
                        'with_answers'
                        if options['with_answers']
                        else 'tasks_only'
                    ),
                ),
            )
        )

        if result.status == DOCUMENT_RENDER_STATUS_NOT_FOUND:
            raise CommandError(f'Work {options["object_id"]} not found')
        if result.status == DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER:
            raise CommandError('PDF renderer is not supported')
        if result.status != DOCUMENT_RENDER_STATUS_GENERATED:
            raise CommandError(f'Document render failed: {result.status}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Created PDF document for {result.source_name}'
            )
        )
        for generated_file in result.files:
            self.stdout.write(
                f'  {generated_file.filename} '
                f'({generated_file.size_kb:.1f} KB)'
            )
