import os
import subprocess
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from works.models import Work, Variant
from works.latex.generator import LaTeXGenerator

class Command(BaseCommand):
    help = 'Генерация LaTeX/PDF для работы (все варианты в одном файле)'
    
    def add_arguments(self, parser):
        parser.add_argument('work_id', type=int, help='ID работы')
        parser.add_argument(
            '--format',
            choices=['latex', 'pdf'],
            default='pdf',
            help='Формат вывода: latex или pdf'
        )
        parser.add_argument(
            '--output-dir',
            default='latex_output',
            help='Папка для сохранения файлов'
        )
        parser.add_argument(
            '--with-answers',
            action='store_true',
            help='Добавить лист ответов в конце'
        )

    def handle(self, *args, **options):
        work_id = options['work_id']
        output_format = options['format']
        output_dir = Path(options['output_dir'])
        with_answers = options['with_answers']
        
        try:
            work = Work.objects.get(pk=work_id)
        except Work.DoesNotExist:
            raise CommandError(f'Работа с ID {work_id} не найдена')
        
        # Создаем папку для вывода
        output_dir.mkdir(exist_ok=True)
        
        variants = Variant.objects.filter(work=work).order_by('number')
        if not variants.exists():
            raise CommandError('У работы нет вариантов. Сначала сгенерируйте варианты.')
        
        self.stdout.write(f'🚀 Генерация LaTeX для работы: {work.name}')
        self.stdout.write(f'📋 Найдено вариантов: {variants.count()}')
        
        generator = LaTeXGenerator(work, output_dir)
        
        # Генерируем ОДИН документ со ВСЕМИ вариантами
        files = generator.generate_all_variants(variants, output_format, with_answers)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'🎉 Готово! Создан файл с {variants.count()} вариантами: {files}'
            )
        )
