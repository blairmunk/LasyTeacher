from django.core.management.base import BaseCommand, CommandError

from infrastructure.container import container
from works.management.commands._document_rendering import (
    raise_for_work_document_render_error,
    render_work_document_with_container,
    write_work_document_render_result,
)


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

        result = render_work_document_with_container(
            render_container=container,
            work_id=options['object_id'],
            renderer_type='pdf',
            page_format=options['format'],
            with_answers=options['with_answers'],
        )

        raise_for_work_document_render_error(
            result=result,
            work_id=options['object_id'],
            renderer_type='pdf',
        )
        write_work_document_render_result(
            self,
            result,
            file_type_label='PDF',
        )
