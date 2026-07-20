from django.core.management.base import BaseCommand

from infrastructure.container import container
from works.management.commands._document_rendering import (
    raise_for_work_document_render_error,
    render_work_document_with_container,
    write_work_document_render_result,
)


class Command(BaseCommand):
    help = (
        'Deprecated alias for render_work_document. '
        'Renders LaTeX/PDF document for a work through document engine.'
    )

    def add_arguments(self, parser):
        parser.add_argument('work_id', type=str, help='ID работы')
        parser.add_argument('--format', choices=['latex', 'pdf'], default='pdf')
        parser.add_argument('--with-answers', action='store_true')
        parser.add_argument('--output-dir', default='latex_output')

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING(
                'generate_work_latex is deprecated; '
                'use render_work_document instead.'
            )
        )

        if options.get('output_dir') != 'latex_output':
            self.stdout.write(
                self.style.WARNING(
                    '--output-dir is deprecated and ignored by document engine.'
                )
            )

        result = render_work_document_with_container(
            render_container=container,
            work_id=options['work_id'],
            renderer_type=options['format'],
            with_answers=options['with_answers'],
        )

        raise_for_work_document_render_error(
            result=result,
            work_id=options['work_id'],
            renderer_type=options['format'],
        )
        write_work_document_render_result(self, result)
