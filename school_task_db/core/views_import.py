# core/views_import.py

import json
import time
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.generic import ListView
from django.views.decorators.http import require_POST

from .importers.tasks import TaskImporter
from .models import ImportLog
from core_logic.entities.task import TaskExportFilters
from core_logic.use_cases.export_tasks import ExportTasksRequest
from core_logic.use_cases.get_import_views import ImportPageRequest
from core_logic.use_cases.validate_task_import_json import (
    ValidateTaskImportJsonRequest,
)
from infrastructure.container import container


class ImportPageView(View):
    """Главная страница импорта"""
    template_name = 'core/import.html'
    
    def get(self, request):
        data = container.get_import_page_use_case().execute(
            ImportPageRequest(recent_limit=5),
        )
        context = {
            'recent_imports': data.recent_imports,
        }
        return render(request, self.template_name, context)


class ImportHistoryView(ListView):
    """История всех импортов"""
    model = ImportLog
    template_name = 'core/import_history.html'
    context_object_name = 'imports'
    paginate_by = 20

    def get_queryset(self):
        return container.get_import_history_use_case().execute().imports


def validate_json_ajax(request):
    """Ajax: валидация загруженного JSON без импорта"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)
    
    uploaded_file = request.FILES.get('json_file')
    if not uploaded_file:
        return JsonResponse({'error': 'Файл не выбран'}, status=400)
    
    # Проверка размера (макс 50MB)
    if uploaded_file.size > 50 * 1024 * 1024:
        return JsonResponse({
            'error': f'Файл слишком большой: {uploaded_file.size // 1024 // 1024}MB (макс: 50MB)'
        }, status=400)
    
    # Парсинг JSON
    try:
        raw_content = uploaded_file.read().decode('utf-8')
        data = json.loads(raw_content)
    except UnicodeDecodeError:
        return JsonResponse({'error': 'Файл не в кодировке UTF-8'}, status=400)
    except json.JSONDecodeError as e:
        return JsonResponse({
            'error': f'Невалидный JSON: {e.msg} (строка {e.lineno}, позиция {e.colno})'
        }, status=400)
    
    # Структурная валидация
    validation = (
        container.validate_task_import_json_use_case()
        .execute(ValidateTaskImportJsonRequest(data=data))
        .to_dict()
    )
    
    # Dry-run через существующий импортёр
    preview = None
    if validation['is_valid']:
        try:
            importer = TaskImporter(
                mode='update',
                dry_run=True,
                verbose=False,
                create_missing=True,
            )
            importer.validate_mode()
            context = importer.import_tasks_from_json(data)
            
            # Извлекаем статистику из контекста
            context_stats = {}
            if hasattr(context, 'get_stats_summary'):
                context_stats = context.get_stats_summary()
            
            preview = {
                'total_created': getattr(importer.stats, 'created', 0),
                'total_updated': getattr(importer.stats, 'updated', 0),
                'context': context_stats,
                'tasks_in_context': len(getattr(context, 'imported_tasks', {})),
                'groups_in_context': len(getattr(context, 'imported_groups', {})),
                'topics_in_context': len(getattr(context, 'imported_topics', {})),
            }
        except Exception as e:
            validation['warnings'].append(f'Ошибка dry-run: {str(e)}')
    
    return JsonResponse({
        'filename': uploaded_file.name,
        'file_size': uploaded_file.size,
        'validation': validation,
        'preview': preview,
    })

@require_POST
def execute_import_ajax(request):
    """Ajax: выполнение импорта"""
    uploaded_file = request.FILES.get('json_file')
    if not uploaded_file:
        return JsonResponse({'error': 'Файл не выбран'}, status=400)
    
    mode = request.POST.get('mode', 'update')
    dry_run = request.POST.get('dry_run') == 'true'
    create_missing = request.POST.get('create_missing', 'true') == 'true'
    
    # Парсинг
    try:
        data = json.loads(uploaded_file.read().decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return JsonResponse({'error': f'Ошибка чтения JSON: {str(e)}'}, status=400)
    
    # Создаём лог
    log = ImportLog.objects.create(
        filename=uploaded_file.name,
        mode=mode,
        dry_run=dry_run,
        file_size=uploaded_file.size,
        status=ImportLog.Status.IMPORTING,
    )
    
    # Импорт
    start_time = time.time()
    try:
        importer = TaskImporter(
            mode=mode,
            dry_run=dry_run,
            verbose=True,
            create_missing=create_missing,
        )
        importer.validate_mode()
        context = importer.import_tasks_from_json(data)
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Извлекаем статистику из importer.stats и context
        stats_created = getattr(importer.stats, 'created', 0)
        stats_updated = getattr(importer.stats, 'updated', 0)
        stats_skipped = getattr(importer.stats, 'skipped', 0)
        stats_errors_list = getattr(importer.stats, 'errors', [])
        
        # errors может быть int или list в зависимости от реализации BaseImporter
        if isinstance(stats_errors_list, list):
            errors_count = len(stats_errors_list)
            error_messages = [str(e) for e in stats_errors_list[:50]]
        elif isinstance(stats_errors_list, int):
            errors_count = stats_errors_list
            error_messages = []
        else:
            errors_count = 0
            error_messages = []
        
        # Считаем по контексту
        tasks_in_context = len(getattr(context, 'imported_tasks', {}))
        groups_in_context = len(getattr(context, 'imported_groups', {}))
        topics_in_context = len(getattr(context, 'imported_topics', {}))
        
        # Получаем context stats
        context_stats = {}
        if hasattr(context, 'get_stats_summary'):
            context_stats = context.get_stats_summary()
        
        # Заполняем лог
        log.tasks_created = stats_created
        log.tasks_updated = stats_updated
        log.tasks_skipped = stats_skipped
        log.groups_created = groups_in_context
        log.topics_created = topics_in_context
        log.errors_count = errors_count
        log.details = {
            'importer_stats': {
                'created': stats_created,
                'updated': stats_updated,
                'skipped': stats_skipped,
            },
            'context_stats': context_stats,
            'context_counts': {
                'tasks': tasks_in_context,
                'groups': groups_in_context,
                'topics': topics_in_context,
            },
        }
        log.error_messages = error_messages
        log.duration_ms = duration_ms
        log.status = (
            ImportLog.Status.SUCCESS if errors_count == 0
            else ImportLog.Status.PARTIAL
        )
        log.save()
        
        return JsonResponse({
            'status': 'success',
            'dry_run': dry_run,
            'log_id': str(log.id),
            'duration_ms': duration_ms,
            'stats': {
                'created': stats_created,
                'updated': stats_updated,
                'skipped': stats_skipped,
                'errors': errors_count,
                'context': context_stats,
                'context_counts': {
                    'tasks': tasks_in_context,
                    'groups': groups_in_context,
                    'topics': topics_in_context,
                },
            },
            'message': _build_summary_message(log),
        })
        
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        log.status = ImportLog.Status.FAILED
        log.error_messages = [str(e)]
        log.duration_ms = duration_ms
        log.save()
        
        return JsonResponse({
            'status': 'error',
            'log_id': str(log.id),
            'error': str(e),
        }, status=500)


def _build_summary_message(log):
    """Формирует человекочитаемый отчёт"""
    prefix = "🔍 ПРЕВЬЮ (dry-run)" if log.dry_run else "✅ ИМПОРТ ЗАВЕРШЁН"
    lines = [
        prefix,
        f"Файл: {log.filename} ({log.file_size_human})",
        f"Режим: {log.get_mode_display()}",
        f"Время: {log.duration_human}",
        "",
        "📊 Результаты:",
        f"  Создано: {log.tasks_created}",
        f"  Обновлено: {log.tasks_updated}",
        f"  Пропущено: {log.tasks_skipped}",
        "",
        "📦 В контексте:",
        f"  Групп аналогов: {log.groups_created}",
        f"  Тем: {log.topics_created}",
    ]
    if log.errors_count > 0:
        lines.append(f"\n❌ Ошибок: {log.errors_count}")
        for err in (log.error_messages or [])[:5]:
            lines.append(f"  • {err}")
    return "\n".join(lines)


def download_sample_json(request):
    """Скачать пример JSON-файла в формате, который ожидает TaskImporter"""
    sample = {
        "version": "1.1",
        "description": "Пример файла для импорта заданий (v1.1 — с источниками и метаданными)",

        "sources": [
            {
                "name": "Перышкин А.В. Физика. 8 класс",
                "short_name": "Перышкин-8",
                "source_type": "textbook",
                "author": "Перышкин А.В.",
                "year": 2020
            }
        ],

        "analog_groups": [
            {
                "id": "770e8400-e29b-41d4-a716-446655440001",
                "name": "Линейные уравнения — базовый",
                "description": "Простые линейные уравнения вида ax + b = c"
            },
            {
                "id": "770e8400-e29b-41d4-a716-446655440002",
                "name": "Сложение дробей",
                "description": "Сложение обыкновенных дробей с разными знаменателями"
            }
        ],

        "topics": [
            {
                "name": "Линейные уравнения",
                "subject": "Математика",
                "grade_level": 7,
                "section": "Алгебра",
                "description": "Решение линейных уравнений"
            }
        ],

        "tasks": [
            {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "text": "Решите уравнение: $2x + 5 = 15$",
                "answer": "$x = 5$",
                "short_solution": "$2x = 10$, $x = 5$",
                "full_solution": "Перенесём 5 в правую часть:\n$$2x = 15 - 5 = 10$$\nРазделим на 2: $x = 5$",
                "hint": "Перенесите число в правую часть",
                "difficulty": 1,
                "task_type": "task",
                "cognitive_level": "apply",
                "grade": 7,
                "year": 2024,
                "is_verified": True,
                "teacher_notes": "Базовое задание, дети справляются хорошо",
                "source": {
                    "name": "Перышкин А.В. Физика. 8 класс",
                    "short_name": "Перышкин-8"
                },
                "source_detail": "Стр. 45, №12",
                "topic": {
                    "name": "Линейные уравнения",
                    "subject": "Математика",
                    "grade_level": 7
                },
                "groups": [
                    "770e8400-e29b-41d4-a716-446655440001"
                ]
            },
            {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "text": "Найдите значение выражения: $\\frac{3}{4} + \\frac{1}{6}$",
                "answer": "$\\frac{11}{12}$",
                "short_solution": "$\\frac{9}{12} + \\frac{2}{12} = \\frac{11}{12}$",
                "difficulty": 1,
                "task_type": "task",
                "cognitive_level": "apply",
                "grade": 6,
                "is_verified": False,
                "topic": {
                    "name": "Обыкновенные дроби",
                    "subject": "Математика",
                    "grade_level": 6
                },
                "groups": [
                    "770e8400-e29b-41d4-a716-446655440002"
                ]
            }
        ],

        "task_images": []
    }
    
    content = json.dumps(sample, ensure_ascii=False, indent=2)
    response = HttpResponse(content, content_type='application/json; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="sample_import.json"'
    return response


def export_tasks_ajax(request):
    """Экспорт заданий в JSON в формате, совместимом с TaskImporter"""
    export_date = time.strftime('%Y-%m-%d')
    export_data = container.export_tasks_use_case().execute(
        ExportTasksRequest(
            filters=TaskExportFilters(
                topic_id=request.GET.get('topic', ''),
                subject=request.GET.get('subject', ''),
                grade=request.GET.get('grade', ''),
            ),
            export_date=export_date,
        ),
    ).payload
    
    content = json.dumps(export_data, ensure_ascii=False, indent=2)
    response = HttpResponse(content, content_type='application/json; charset=utf-8')
    response['Content-Disposition'] = (
        f'attachment; filename="export_{time.strftime("%Y%m%d_%H%M%S")}.json"'
    )
    return response
