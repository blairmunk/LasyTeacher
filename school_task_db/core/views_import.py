# core/views_import.py

import json
import time
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.generic import ListView
from django.views.decorators.http import require_POST

from core_logic.entities.task import TaskExportFilters
from core_logic.entities.task_import import (
    TaskImportPreviewRequest,
    TaskImportRequest,
)
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
        preview_result = container.preview_task_import_use_case().execute(
            TaskImportPreviewRequest(data=data),
        )
        preview = preview_result.preview
        if not preview_result.success:
            validation['warnings'].append(preview_result.warning)
    
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
    
    result = container.execute_task_import_use_case().execute(
        TaskImportRequest(
            data=data,
            filename=uploaded_file.name,
            mode=mode,
            dry_run=dry_run,
            create_missing=create_missing,
            file_size=uploaded_file.size,
        ),
    )
    return JsonResponse(
        result.to_response_data(),
        status=200 if result.success else 500,
    )


def download_sample_json(request):
    """Скачать пример JSON-файла в формате, который ожидает TaskImporter"""
    sample = container.get_task_import_sample_use_case().execute()
    content = json.dumps(sample.payload, ensure_ascii=False, indent=2)
    response = HttpResponse(content, content_type='application/json; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{sample.filename}"'
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
