from django.core.management.base import BaseCommand
from events.models import Mark
from students.models import StudentTaskLog


class Command(BaseCommand):
    help = 'Заполняет StudentTaskLog из существующих Mark.task_scores'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                            help='Только показать что будет сделано')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        marks = Mark.objects.exclude(task_scores={}).select_related(
            'participation__student',
            'participation__event',
            'participation__variant',
        )
        
        total_marks = marks.count()
        self.stdout.write(f"Найдено {total_marks} отметок с task_scores")
        
        if dry_run:
            for mark in marks:
                task_count = len(mark.task_scores)
                self.stdout.write(
                    f"  Mark #{str(mark.pk)[-8:]} → "
                    f"{mark.participation.student} → "
                    f"{task_count} заданий"
                )
            return
        
        total_created = 0
        for i, mark in enumerate(marks, 1):
            created = StudentTaskLog.update_from_mark(mark)
            total_created += created
            if i % 50 == 0:
                self.stdout.write(f"  Обработано {i}/{total_marks}...")
        
        self.stdout.write(self.style.SUCCESS(
            f"Готово! Создано {total_created} записей в StudentTaskLog"
        ))
