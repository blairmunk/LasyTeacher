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


class ImportPageView(View):
    """Главная страница импорта"""
    template_name = 'core/import.html'
    
    def get(self, request):
        context = {
            'recent_imports': ImportLog.objects.all()[:5],
        }
        return render(request, self.template_name, context)


class ImportHistoryView(ListView):
    """История всех импортов"""
    model = ImportLog
    template_name = 'core/import_history.html'
    context_object_name = 'imports'
    paginate_by = 20


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
    validation = _validate_structure(data)
    
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


def _validate_structure(data):
    """Проверка структуры JSON"""
    result = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'summary': {},
    }
    
    # Проверка корневых полей
    if not isinstance(data, dict):
        result['is_valid'] = False
        result['errors'].append('Корневой элемент должен быть объектом {}')
        return result
    
    if 'tasks' not in data:
        result['is_valid'] = False
        result['errors'].append('Отсутствует обязательное поле "tasks"')
        return result
    
    tasks = data['tasks']
    if not isinstance(tasks, list):
        result['is_valid'] = False
        result['errors'].append('"tasks" должен быть массивом')
        return result
    
    if len(tasks) == 0:
        result['warnings'].append('Массив "tasks" пуст')
    
    # Проверка верхнеуровневых данных
    groups_data = data.get('analog_groups', [])
    topics_data = data.get('topics', [])
    images_data = data.get('task_images', [])
    
    # Проверка каждого задания
    tasks_ok = 0
    tasks_errors = 0
    uuids_seen = set()
    
    for i, task in enumerate(tasks):
        task_errors = []
        
        if not isinstance(task, dict):
            task_errors.append(f'Задание #{i+1}: должно быть объектом')
        else:
            # UUID (поле 'id')
            task_uuid = task.get('id')
            if not task_uuid:
                task_errors.append(f'Задание #{i+1}: отсутствует id (UUID)')
            elif task_uuid in uuids_seen:
                task_errors.append(f'Задание #{i+1}: дублирующийся id {task_uuid}')
            else:
                # Валидация формата UUID
                try:
                    import uuid
                    uuid.UUID(task_uuid)
                    uuids_seen.add(task_uuid)
                except ValueError:
                    task_errors.append(f'Задание #{i+1}: некорректный UUID "{task_uuid}"')
            
            # Текст
            if not task.get('text'):
                task_errors.append(f'Задание #{i+1}: отсутствует text')
            
            # Предупреждения
            if not task.get('answer'):
                result['warnings'].append(f'Задание #{i+1}: нет ответа')
            if not task.get('topic'):
                result['warnings'].append(f'Задание #{i+1}: нет темы')
            if not task.get('groups') and not task.get('group_name'):
                result['warnings'].append(f'Задание #{i+1}: нет привязки к группе')
        
        if task_errors:
            result['errors'].extend(task_errors)
            tasks_errors += 1
        else:
            tasks_ok += 1
    
    # Проверка групп аналогов
    group_uuids = set()
    for i, group in enumerate(groups_data):
        if not isinstance(group, dict):
            result['errors'].append(f'Группа #{i+1}: должна быть объектом')
            continue
        if not group.get('id'):
            result['errors'].append(f'Группа #{i+1}: отсутствует id (UUID)')
        else:
            group_uuids.add(group['id'])
        if not group.get('name'):
            result['errors'].append(f'Группа #{i+1}: отсутствует name')
    
    # Проверка ссылок задач на группы
    for i, task in enumerate(tasks):
        if isinstance(task, dict):
            for group_uuid in task.get('groups', []):
                if group_uuid not in group_uuids:
                    result['warnings'].append(
                        f'Задание #{i+1}: ссылка на группу {group_uuid[-8:]}... '
                        f'не найдена в analog_groups (будет искать в БД)'
                    )
    
    if tasks_errors > 0:
        result['is_valid'] = False
    
    result['summary'] = {
        'tasks_total': len(tasks),
        'tasks_valid': tasks_ok,
        'tasks_errors': tasks_errors,
        'groups_total': len(groups_data),
        'topics_total': len(topics_data),
        'images_total': len(images_data),
    }
    
    return result


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
    from tasks.models import Task
    
    # Фильтры
    topic_id = request.GET.get('topic')
    subject = request.GET.get('subject')
    grade = request.GET.get('grade')
    
    tasks_qs = Task.objects.select_related(
        'topic', 'subtopic', 'source'
    ).prefetch_related('images', 'taskgroup_set__group')
    
    if topic_id:
        tasks_qs = tasks_qs.filter(topic_id=topic_id)
    if subject:
        tasks_qs = tasks_qs.filter(topic__subject=subject)
    if grade:
        tasks_qs = tasks_qs.filter(topic__grade_level=grade)
    
    # Собираем уникальные группы и темы
    all_groups = {}
    all_topics = {}
    tasks_data = []
    images_data = []
    
    for task in tasks_qs:
        # Данные задания
        task_dict = {
            'id': str(task.id),
            'text': task.text,
            'answer': task.answer or '',
            'short_solution': task.short_solution or '',
            'full_solution': task.full_solution or '',
            'hint': task.hint or '',
            'instruction': task.instruction or '',
            'difficulty': task.difficulty,
            'task_type': task.task_type,
            'cognitive_level': getattr(task, 'cognitive_level', ''),
            'content_element': getattr(task, 'content_element', ''),
            'requirement_element': getattr(task, 'requirement_element', ''),
            'estimated_time': getattr(task, 'estimated_time', None),
            # Новые поля
            'grade': task.grade,
            'year': task.year,
            'is_verified': task.is_verified,
            'teacher_notes': task.teacher_notes or '',
            'source_detail': task.source_detail or '',
            'source': None,
            'groups': [],
        }

        # Источник
        if task.source:
            task_dict['source'] = {
                'name': task.source.name,
                'short_name': task.source.short_name or '',
                'source_type': task.source.source_type,
                'author': task.source.author or '',
                'year': task.source.year,
            }

        
        # Тема
        if task.topic:
            task_dict['topic'] = {
                'name': task.topic.name,
                'subject': task.topic.subject,
                'grade_level': task.topic.grade_level,
                'section': getattr(task.topic, 'section', ''),
            }
            topic_key = f"{task.topic.subject}_{task.topic.grade_level}_{task.topic.name}"
            if topic_key not in all_topics:
                all_topics[topic_key] = {
                    'name': task.topic.name,
                    'subject': task.topic.subject,
                    'grade_level': task.topic.grade_level,
                    'section': getattr(task.topic, 'section', ''),
                    'description': getattr(task.topic, 'description', ''),
                }
        
        # Группы аналогов (через TaskGroup M2M)
        for task_group in task.taskgroup_set.all():
            group = task_group.group
            group_uuid = str(group.id)
            task_dict['groups'].append(group_uuid)
            
            if group_uuid not in all_groups:
                all_groups[group_uuid] = {
                    'id': group_uuid,
                    'name': group.name,
                    'description': getattr(group, 'description', ''),
                }
        
        # Изображения (base64)
        for img in task.images.all():
            if img.has_file:
                import base64
                try:
                    with img.image.open('rb') as f:
                        b64 = base64.b64encode(f.read()).decode('ascii')
                    images_data.append({
                        'id': str(img.id),
                        'task_id': str(task.id),
                        'filename': img.image.name.split('/')[-1],
                        'position': img.position or '',
                        'caption': img.caption or '',
                        'order': img.order,
                        'base64_data': b64,
                    })
                except Exception:
                    pass
        
        tasks_data.append(task_dict)
    
    # Собираем уникальные источники
    all_sources = {}
    for task in tasks_qs:
        if task.source and str(task.source.id) not in all_sources:
            all_sources[str(task.source.id)] = {
                'id': str(task.source.id),
                'name': task.source.name,
                'short_name': task.source.short_name or '',
                'source_type': task.source.source_type,
                'author': task.source.author or '',
                'year': task.source.year,
                'url': task.source.url or '',
                'isbn': task.source.isbn or '',
            }

    export_data = {
        'version': '1.1',
        'export_date': time.strftime('%Y-%m-%d'),
        'analog_groups': list(all_groups.values()),
        'topics': list(all_topics.values()),
        'sources': list(all_sources.values()),
        'tasks': tasks_data,
        'task_images': images_data,
    }
    
    content = json.dumps(export_data, ensure_ascii=False, indent=2)
    response = HttpResponse(content, content_type='application/json; charset=utf-8')
    response['Content-Disposition'] = (
        f'attachment; filename="export_{time.strftime("%Y%m%d_%H%M%S")}.json"'
    )
    return response
