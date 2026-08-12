"""Preview or apply explicit links for legacy task classification codes."""

from django.core.management.base import BaseCommand

from core_logic.entities.task_classification_backfill import (
    BackfillTaskClassificationsRequest,
)
from infrastructure.container import container


class Command(BaseCommand):
    help = 'Восстановить явные связи классификации из старых кодов заданий'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Применить однозначные связи; без флага выводится только план',
        )

    def handle(self, *args, **options):
        result = container.backfill_task_classifications_use_case().execute(
            BackfillTaskClassificationsRequest(apply=options['apply']),
        )
        plan = result.plan
        self.stdout.write(
            f'Элементы содержания: {plan.content_count}; '
            f'требования: {plan.requirement_count}; '
            f'проблемы: {len(plan.issues)}',
        )
        for issue in plan.issues:
            self.stdout.write(self.style.WARNING(
                f'{issue.task_id}: {issue.relation_type} {issue.code} — '
                f'{issue.status} ({len(issue.candidate_ids)} кандидатов)',
            ))
        if result.status == 'applied':
            self.stdout.write(self.style.SUCCESS('Однозначные связи применены.'))
        else:
            self.stdout.write('Dry-run: добавьте --apply для записи.')
