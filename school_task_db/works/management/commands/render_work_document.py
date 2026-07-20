from django.core.management.base import BaseCommand

from infrastructure.container import container
from works.management.commands._document_rendering import (
    raise_for_work_document_render_error,
    render_work_document_with_container,
    write_work_document_render_result,
)


class Command(BaseCommand):
    help = 'Render a work document through document engine'

    def add_arguments(self, parser):
        parser.add_argument('work_id', type=str, help='ID работы')
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
        parser.add_argument('--with-answers', action='store_true')

    def handle(self, *args, **options):
        result = render_work_document_with_container(
            render_container=container,
            work_id=options['work_id'],
            renderer_type=options['renderer'],
            page_format=options['page_format'],
            with_answers=options['with_answers'],
        )

        raise_for_work_document_render_error(
            result=result,
            work_id=options['work_id'],
            renderer_type=options['renderer'],
        )
        write_work_document_render_result(self, result)
