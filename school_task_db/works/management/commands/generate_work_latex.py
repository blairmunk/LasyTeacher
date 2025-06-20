import os
import subprocess
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from works.models import Work, Variant
from works.latex.generator import LaTeXGenerator

class Command(BaseCommand):
    help = 'Генерация LaTeX/PDF для работы'
    
    def add_arguments(self, parser):
        parser.add_argument('work_id', type=int, help='ID работы')
        parser.add_argument(
            '--variant', 
            type=int, 
            help='Номер конкретного варианта (по умолчанию все)'
        )
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

    def handle(self, *args, **options):
        work_id = options['work_id']
        variant_number = options.get('variant')
        output_format = options['format']
        output_dir = Path(options['output_dir'])
        
        try:
            work = Work.objects.get(pk=work_id)
        except Work.DoesNotExist:
            raise CommandError(f'Работа с ID {work_id} не найдена')
        
        # Создаем папку для вывода
        output_dir.mkdir(exist_ok=True)
        
        self.stdout.write(f'🚀 Генерация LaTeX для работы: {work.name}')
        
        generator = LaTeXGenerator(work, output_dir)
        
        if variant_number:
            # Генерируем один вариант
            try:
                variant = Variant.objects.get(work=work, number=variant_number)
                files = generator.generate_variant(variant, output_format)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Вариант {variant_number} сгенерирован: {files}'
                    )
                )
            except Variant.DoesNotExist:
                raise CommandError(f'Вариант {variant_number} не найден')
        else:
            # Генерируем все варианты
            variants = Variant.objects.filter(work=work).order_by('number')
            if not variants.exists():
                raise CommandError('У работы нет вариантов. Сначала сгенерируйте варианты.')
            
            all_files = []
            for variant in variants:
                files = generator.generate_variant(variant, output_format)
                all_files.extend(files)
                self.stdout.write(f'  ✅ Вариант {variant.number}: {files}')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'🎉 Готово! Сгенерировано {len(variants)} вариантов: {len(all_files)} файлов'
                )
            )
