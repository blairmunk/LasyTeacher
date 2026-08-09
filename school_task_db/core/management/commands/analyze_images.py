"""Audit task image positions through clean application use cases."""

from collections import Counter

from django.core.management.base import BaseCommand

from infrastructure.container import container


class Command(BaseCommand):
    help = 'Анализ расположения изображений заданий'

    def add_arguments(self, parser):
        parser.add_argument(
            '--show-missing',
            action='store_true',
            help='Показать изображения без позиции',
        )
        parser.add_argument(
            '--fix-missing',
            action='store_true',
            help='Предложить и применить позиции после подтверждения',
        )

    def handle(self, *args, **options):
        report = container.analyze_task_images_use_case().execute()
        self.stdout.write('📊 АНАЛИЗ ИЗОБРАЖЕНИЙ ЗАДАНИЙ:')
        self.stdout.write(f'  🖼️ Всего изображений: {report.total_images}')

        if not report.total_images:
            self.stdout.write('  ℹ️ Изображений нет')
            return

        self.stdout.write('\n📍 РАСПРЕДЕЛЕНИЕ ПО ПОЗИЦИЯМ:')
        for item in report.distribution:
            self.stdout.write(
                f'  {item.label}: {item.count} ({item.percentage:.1f}%)',
            )

        if not report.missing_count:
            self.stdout.write('\n✅ Все изображения имеют заданные позиции')
            return

        self.stdout.write(
            f'\n🔍 ИЗОБРАЖЕНИЯ БЕЗ ПОЗИЦИИ: {report.missing_count}',
        )
        if options['show_missing']:
            self._write_missing_images(report.missing_images)
        if options['fix_missing']:
            self._offer_suggestions(report.suggestions)

        self.stdout.write('\n💡 РЕКОМЕНДАЦИИ:')
        self.stdout.write(
            '  • Для массового обновления: '
            'python manage.py analyze_images --fix-missing',
        )
        self.stdout.write(
            '  • Для ручного редактирования перейдите в админ-панель',
        )
        self.stdout.write(
            '  • При импорте указывайте position в JSON',
        )

    def _write_missing_images(self, images):
        self.stdout.write('\n📝 ДЕТАЛИ:')
        for index, image in enumerate(images[:10], 1):
            task_preview = self._truncate(image.task_text, 40)
            self.stdout.write(
                f'  {index}. [{image.short_id}] {task_preview}',
            )
            self.stdout.write(f'     Тема: {image.topic_name or "—"}')
            self.stdout.write(f'     Файл: {image.filename}')
            if image.caption:
                self.stdout.write(f'     Подпись: {image.caption}')
        if len(images) > 10:
            self.stdout.write(f'     ... и ещё {len(images) - 10}')

    def _offer_suggestions(self, suggestions):
        self.stdout.write('\n🔧 ПРЕДЛОЖЕНИЯ ПО ИСПРАВЛЕНИЮ:')
        grouped = Counter(
            suggestion.position_label
            for suggestion in suggestions
        )
        for label, count in sorted(grouped.items()):
            self.stdout.write(f'  📍 {label}: {count} изображений')

        answer = input('\nПрименить предложенные позиции? (y/n): ')
        if answer.strip().lower() != 'y':
            self.stdout.write('Изменения не применены')
            return

        updated = (
            container.apply_task_image_position_suggestions_use_case()
            .execute(suggestions)
        )
        self.stdout.write(self.style.SUCCESS(f'✅ Обновлено позиций: {updated}'))

    @staticmethod
    def _truncate(value: str, limit: int) -> str:
        if len(value) <= limit:
            return value
        return f'{value[:limit]}...'
