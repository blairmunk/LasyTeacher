"""Интегрированная команда: HTML + PDF генерация одной командой"""

from django.core.management.base import BaseCommand, CommandError
from django.apps import apps
from pathlib import Path
import logging

class Command(BaseCommand):
    help = 'Генерирует PDF документы через HTML→PDF pipeline'

    def add_arguments(self, parser):
        parser.add_argument('object_type', choices=['work'])
        parser.add_argument('object_id', type=int)
        parser.add_argument('--with-answers', action='store_true')
        parser.add_argument('--output-dir', default='pdf_output')
        parser.add_argument('--keep-html', action='store_true', help='Сохранить HTML файлы')
        parser.add_argument('--format', choices=['A4', 'A5', 'Letter'], default='A4')

    def handle(self, *args, **options):
        object_type = options['object_type']
        object_id = options['object_id']
        
        try:
            if object_type == 'work':
                Work = apps.get_model('works', 'Work')
                work = Work.objects.get(id=object_id)
                
                self.stdout.write(f"📄 Генерируем PDF для: [{work.get_short_uuid()}] {work.name}")
                
                # ШАГ 1: Генерируем HTML
                from html_generator.generators.work_generator import WorkHtmlGenerator
                html_gen = WorkHtmlGenerator(output_dir='temp_html_output')
                
                if options['with_answers']:
                    html_files = html_gen.generate_with_answers(work)
                else:
                    html_files = html_gen.generate(work)
                
                self.stdout.write(f"✅ HTML создан: {len(html_files)} файлов")
                
                # ШАГ 2: HTML → PDF
                from pdf_generator.generators.html_to_pdf import HtmlToPdfGenerator
                pdf_gen = HtmlToPdfGenerator(format=options['format'])
                
                pdf_files = []
                for html_file in html_files:
                    html_path = Path(html_file)
                    pdf_name = html_path.stem + '.pdf'
                    pdf_path = Path(options['output_dir']) / pdf_name
                    
                    self.stdout.write(f"🔄 Конвертируем: {html_path.name}")
                    result = pdf_gen.generate_pdf(html_path, pdf_path)
                    pdf_files.append(result)
                    
                    file_size = result.stat().st_size / 1024
                    self.stdout.write(f"  ✅ PDF: {result.name} ({file_size:.1f} KB)")
                
                # ШАГ 3: Очистка временных файлов
                if not options['keep_html']:
                    import shutil
                    shutil.rmtree('temp_html_output', ignore_errors=True)
                    self.stdout.write("🗑️ Временные HTML файлы удалены")
                
                # Итоговая статистика
                self.stdout.write("")
                self.stdout.write("🎉 PDF генерация завершена!")
                for pdf_file in pdf_files:
                    self.stdout.write(f"  📄 {pdf_file}")
                    
        except Exception as e:
            raise CommandError(f"Ошибка: {e}")
