import os
import subprocess
from pathlib import Path
from django.template.loader import render_to_string
from django.conf import settings
from works.latex.utils import sanitize_latex, prepare_images

class LaTeXGenerator:
    """Генератор LaTeX документов для работ"""
    
    def __init__(self, work, output_dir):
        self.work = work
        self.output_dir = Path(output_dir)
        self.templates_dir = Path(__file__).parent / 'templates'
    
    def generate_all_variants(self, variants, output_format='pdf', with_answers=False):
        """Генерирует ОДИН LaTeX/PDF файл со ВСЕМИ вариантами"""
        
        # Подготовка данных для всех вариантов
        all_variants_data = []
        for variant in variants:
            variant_data = self._prepare_variant_context(variant)
            all_variants_data.append(variant_data)
        
        # Контекст для шаблона
        context = {
            'work': self.work,
            'work_name': sanitize_latex(self.work.name),
            'variants': all_variants_data,
            'total_variants': len(all_variants_data),
            'with_answers': with_answers,
        }
        
        # Генерация LaTeX
        latex_content = render_to_string('latex/work_all_variants.tex', context)
        
        # Сохранение LaTeX файла
        latex_filename = f"{sanitize_filename(self.work.name)}_all_variants.tex"
        latex_file = self.output_dir / latex_filename
        
        with open(latex_file, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        files = [str(latex_file)]
        
        # Генерация PDF если нужно
        if output_format == 'pdf':
            pdf_file = self._compile_latex_to_pdf(latex_file)
            if pdf_file:
                files.append(str(pdf_file))
        
        return files
    
    def _prepare_variant_context(self, variant):
        """Подготавливает контекст для одного варианта"""
        tasks = variant.tasks.all().order_by('id')  # Детерминированный порядок
        
        # Подготавливаем задания с изображениями
        prepared_tasks = []
        for i, task in enumerate(tasks, 1):
            task_data = {
                'number': i,
                'task': task,
                'text': sanitize_latex(task.text),
                'answer': sanitize_latex(task.answer),
                'images': []
            }
            
            # Подготавливаем изображения
            for image in task.images.all().order_by('order'):
                image_data = prepare_images(image, self.output_dir)
                if image_data:
                    task_data['images'].append(image_data)
            
            prepared_tasks.append(task_data)
        
        return {
            'variant': variant,
            'tasks': prepared_tasks,
            'total_tasks': len(prepared_tasks),
        }
    
    def _compile_latex_to_pdf(self, latex_file):
        """Компилирует LaTeX в PDF"""
        try:
            # Меняем рабочую директорию для pdflatex
            old_cwd = os.getcwd()
            os.chdir(self.output_dir)
            
            # Запускаем pdflatex дважды (для правильных ссылок)
            for i in range(2):
                result = subprocess.run([
                    'pdflatex', 
                    '-interaction=nonstopmode',
                    '-halt-on-error',
                    latex_file.name
                ], capture_output=True, text=True, encoding='utf-8')
                
                if result.returncode != 0:
                    print(f"❌ Ошибка компиляции LaTeX (проход {i+1}): {result.stderr}")
                    os.chdir(old_cwd)
                    return None
            
            os.chdir(old_cwd)
            
            pdf_file = latex_file.with_suffix('.pdf')
            return pdf_file if pdf_file.exists() else None
                
        except FileNotFoundError:
            print("❌ pdflatex не найден. Установите TeX Live или MikTeX")
            return None
        except Exception as e:
            print(f"❌ Ошибка при компиляции: {e}")
            return None

def sanitize_filename(filename):
    """Очищает имя файла от недопустимых символов"""
    import re
    # Убираем недопустимые символы
    clean = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Убираем лишние пробелы
    clean = re.sub(r'\s+', '_', clean)
    return clean
