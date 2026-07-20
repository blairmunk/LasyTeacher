from django.core.management.base import BaseCommand

from infrastructure.container import container
from works.management.commands._document_rendering import (
    raise_for_remedial_sheet_document_render_error,
    render_remedial_sheet_document_with_container,
    write_work_document_render_result,
)


class Command(BaseCommand):
    help = 'Render a remedial sheet document through document engine'

    def add_arguments(self, parser):
        parser.add_argument('variant_id', type=str, help='ID варианта')
        parser.add_argument(
            '--renderer',
            choices=['html', 'latex', 'pdf'],
            default='pdf',
        )
        parser.add_argument(
            '--page-format',
            choices=['A4', 'A5', 'Letter'],
            default='A4',
        )
        parser.add_argument(
            '--answer-type',
            choices=[
                'with_answers',
                'with_short_solutions',
                'with_full_solutions',
            ],
            default='with_short_solutions',
        )

    def handle(self, *args, **options):
        result = render_remedial_sheet_document_with_container(
            render_container=container,
            variant_id=options['variant_id'],
            renderer_type=options['renderer'],
            page_format=options['page_format'],
            answer_type=options['answer_type'],
        )

        raise_for_remedial_sheet_document_render_error(
            result=result,
            variant_id=options['variant_id'],
            renderer_type=options['renderer'],
        )
        write_work_document_render_result(self, result)
