from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_GENERATED,
    DOCUMENT_RENDER_STATUS_NOT_FOUND,
    DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER,
)
from core_logic.use_cases.render_work_document import RenderWorkDocumentRequest
from core_logic.value_objects.document_render_options import WorkDocumentRenderOptions
from infrastructure.container import container


class Command(BaseCommand):
    help = 'Generate LaTeX/PDF document for a work through document engine'

    def add_arguments(self, parser):
        parser.add_argument('work_id', type=str, help='ID работы')
        parser.add_argument('--format', choices=['latex', 'pdf'], default='pdf')
        parser.add_argument('--with-answers', action='store_true')
        parser.add_argument('--output-dir', default='latex_output')

    def handle(self, *args, **options):
        if options.get('output_dir') != 'latex_output':
            self.stdout.write(
                self.style.WARNING(
                    '--output-dir is deprecated and ignored by document engine.'
                )
            )

        result = container.render_work_document_use_case().execute(
            RenderWorkDocumentRequest(
                work_id=str(options['work_id']),
                options=WorkDocumentRenderOptions(
                    renderer_type=options['format'],
                    answer_type=(
                        'with_answers'
                        if options['with_answers']
                        else 'tasks_only'
                    ),
                ),
            )
        )

        if result.status == DOCUMENT_RENDER_STATUS_NOT_FOUND:
            raise CommandError(f'Work {options["work_id"]} not found')
        if result.status == DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER:
            raise CommandError(f'Unsupported renderer: {options["format"]}')
        if result.status != DOCUMENT_RENDER_STATUS_GENERATED:
            raise CommandError(f'Document render failed: {result.status}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Created {result.file_type} document for {result.source_name}'
            )
        )
        for generated_file in result.files:
            self.stdout.write(
                f'  {generated_file.filename} '
                f'({generated_file.size_kb:.1f} KB)'
            )
