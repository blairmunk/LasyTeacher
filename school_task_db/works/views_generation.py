"""Views для генерации документов через веб-интерфейс"""

import json
import logging
from pathlib import Path
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
import mimetypes

from .models import Work, Variant
from tasks.models import Task

logger = logging.getLogger(__name__)

@require_http_methods(["POST"])
def generate_work_ajax(request, work_id):
    """Ajax генерация документов для работы с поддержкой 4 типов ответов"""
    work = get_object_or_404(Work, id=work_id)
    
    try:
        # Базовые параметры
        generator_type = request.POST.get('generator_type', 'pdf')
        pdf_format = request.POST.get('format', 'A4')
        
        # НОВОЕ: Определяем тип контента
        answer_type = request.POST.get('answer_type', 'tasks_only')
        # Совместимость со старым параметром
        if request.POST.get('with_answers', '0') == '1' and answer_type == 'tasks_only':
            answer_type = 'with_answers'
        
        logger.info(f"🌐 Веб-генерация {generator_type} для работы {work.id}: {work.name}")
        logger.info(f"   Тип контента: {answer_type}")
        
        # Определяем что включать в документ
        content_config = {
            'include_answers': answer_type in ['with_answers', 'with_short_solutions', 'with_full_solutions'],
            'include_short_solutions': answer_type in ['with_short_solutions', 'with_full_solutions'],
            'include_full_solutions': answer_type == 'with_full_solutions',
            'answer_type': answer_type  # Для генераторов которые хотят знать точный тип
        }
        
        # Выбираем генератор и запускаем
        if generator_type == 'latex':
            files = generate_latex_work(work, content_config, pdf_format)
            file_type = 'LaTeX'
            
        elif generator_type == 'html':
            files = generate_html_work(work, content_config)
            file_type = 'HTML'
            
        elif generator_type == 'pdf':
            files = generate_pdf_work(work, content_config, pdf_format)
            file_type = 'PDF'
            
        else:
            return JsonResponse({
                'success': False, 
                'error': f'Неподдерживаемый тип генератора: {generator_type}'
            })
        
        # Подготавливаем информацию о файлах для frontend
        files_info = []
        for file_path in files:
            path = Path(file_path)
            if path.exists():
                file_size = path.stat().st_size / 1024  # KB
                files_info.append({
                    'name': path.name,
                    'size': f'{file_size:.1f} KB',
                    'download_url': reverse('works:download_generated_file', kwargs={
                        'file_type': generator_type,
                        'filename': path.name
                    })
                })
        
        # Красивое сообщение об успехе
        content_descriptions = {
            'tasks_only': 'только задания',
            'with_answers': 'с ответами',
            'with_short_solutions': 'с краткими решениями',
            'with_full_solutions': 'с полными решениями'
        }
        
        success_message = f'{file_type} документ создан ({content_descriptions[answer_type]})'
        
        return JsonResponse({
            'success': True,
            'message': success_message,
            'files': files_info,
            'total_files': len(files_info)
        })
        
    except Exception as e:
        logger.error(f"Ошибка веб-генерации {generator_type} для работы {work.id}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def generate_latex_work(work, content_config, pdf_format='A4'):
    """ОБНОВЛЕНО: LaTeX генератор с поддержкой 4 типов контента"""
    from latex_generator.generators.work_generator import WorkLatexGenerator
    
    generator = WorkLatexGenerator(output_dir='web_latex_output')
    
    # Передаем конфигурацию в генератор
    generator._content_config = content_config
    
    # Используем старый метод, но с новой логикой внутри
    if content_config['include_answers'] or content_config['include_short_solutions'] or content_config['include_full_solutions']:
        return generator.generate_with_answers(work)
    else:
        return generator.generate(work)

def generate_html_work(work, content_config):
    """ОБНОВЛЕНО: HTML генератор с поддержкой 4 типов контента"""
    from html_generator.generators.work_generator import WorkHtmlGenerator
    
    generator = WorkHtmlGenerator(output_dir='web_html_output')
    
    # Передаем конфигурацию в генератор
    generator._content_config = content_config
    
    if content_config['include_answers'] or content_config['include_short_solutions'] or content_config['include_full_solutions']:
        return generator.generate_with_answers(work)  
    else:
        return generator.generate(work)

def generate_pdf_work(work, content_config, pdf_format='A4'):
    """ОБНОВЛЕНО: PDF генератор с поддержкой 4 типов контента"""
    import tempfile
    from html_generator.generators.work_generator import WorkHtmlGenerator
    from pdf_generator.generators.html_to_pdf import HtmlToPdfGenerator
    
    # ШАГ 1: Генерируем HTML во временной папке
    with tempfile.TemporaryDirectory() as temp_dir:
        html_gen = WorkHtmlGenerator(output_dir=temp_dir)
        
        # Передаем конфигурацию в генератор
        html_gen._content_config = content_config
        
        if content_config['include_answers'] or content_config['include_short_solutions'] or content_config['include_full_solutions']:
            html_files = html_gen.generate_with_answers(work)
        else:
            html_files = html_gen.generate(work)
        
        # ШАГ 2: Конвертируем HTML→PDF
        pdf_gen = HtmlToPdfGenerator(format=pdf_format, wait_for_mathjax=True)
        
        pdf_files = []
        output_dir = Path('web_pdf_output')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for html_file in html_files:
            html_path = Path(html_file)
            pdf_name = html_path.stem + '.pdf'
            pdf_path = output_dir / pdf_name
            
            result = pdf_gen.generate_pdf(html_path, pdf_path)
            pdf_files.append(str(result))
    
    return pdf_files

@require_http_methods(["GET"])
def download_generated_file(request, file_type, filename):
    """Скачивание сгенерированного файла"""
    
    # Определяем директорию по типу файла
    type_to_dir = {
        'latex': 'web_latex_output',
        'html': 'web_html_output', 
        'pdf': 'web_pdf_output'
    }
    
    output_dir = type_to_dir.get(file_type)
    if not output_dir:
        raise Http404("Неподдерживаемый тип файла")
    
    file_path = Path(output_dir) / filename
    
    if not file_path.exists():
        raise Http404("Файл не найден")
    
    # Определяем MIME тип
    content_type, _ = mimetypes.guess_type(str(file_path))
    if not content_type:
        content_type = 'application/octet-stream'
    
    # Читаем и возвращаем файл
    try:
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
    except Exception as e:
        logger.error(f"Ошибка скачивания файла {file_path}: {e}")
        raise Http404("Ошибка чтения файла")

@require_http_methods(["GET"])
def generation_status_ajax(request):
    """Ajax проверка статуса генерации (для прогресс-баров в будущем)"""
    # Пока простая заглушка, можно расширить для отслеживания прогресса
    return JsonResponse({
        'status': 'ready',
        'message': 'Система готова к генерации'
    })

# Дополнительные views для вариантов
@require_http_methods(["POST"])
def generate_variant_ajax(request, variant_id):
    """Ajax генерация документов для конкретного варианта"""
    variant = get_object_or_404(Variant, id=variant_id)
    work = variant.work
    
    # Аналогичная логика, но для одного варианта
    # TODO: Реализовать генерацию одного варианта
    
    return JsonResponse({
        'success': True,
        'message': f'Вариант {variant.number} работы "{work.name}" будет добавлен в следующей версии',
        'files': []
    })
