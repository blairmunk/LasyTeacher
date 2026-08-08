"""Run a named, focused subset of the Django test suite."""

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from core.test_slices import TEST_SLICES, get_test_slice


class Command(BaseCommand):
    help = 'Запустить именованный срез тестов с компактным выводом'

    def add_arguments(self, parser):
        parser.set_defaults(verbosity=0)
        parser.add_argument('slice', nargs='?', help='Имя тестового среза')
        parser.add_argument(
            '--list',
            action='store_true',
            help='Показать доступные срезы',
        )
        parser.add_argument(
            '--keepdb',
            action='store_true',
            help='Сохранить тестовую базу между запусками',
        )
        parser.add_argument(
            '--failfast',
            action='store_true',
            help='Остановиться после первой ошибки',
        )

    def handle(self, *args, **options):
        if options['list']:
            self._print_slices()
            return

        slice_name = options['slice']
        if not slice_name:
            raise CommandError('Укажите имя среза или используйте --list.')
        try:
            labels = get_test_slice(slice_name)
        except KeyError as error:
            available = ', '.join(TEST_SLICES)
            raise CommandError(
                f'Неизвестный срез {slice_name!r}. Доступны: {available}.',
            ) from error

        self.stdout.write(
            f'Тестовый срез {slice_name}: '
            f'{len(labels) if labels else "полный набор"}',
        )
        call_command(
            'test',
            *labels,
            verbosity=options['verbosity'],
            interactive=False,
            keepdb=options['keepdb'],
            failfast=options['failfast'],
        )

    def _print_slices(self):
        for name, labels in TEST_SLICES.items():
            description = f'{len(labels)} labels' if labels else 'full suite'
            self.stdout.write(f'{name:14} {description}')

