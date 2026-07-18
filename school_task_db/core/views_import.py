# core/views_import.py

import json
import time
from django.core.paginator import Paginator
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.decorators.http import require_POST

from core_logic.use_cases.get_import_views import ImportPageRequest
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


class ImportHistoryView(View):
    """История всех импортов"""
    template_name = 'core/import_history.html'
    paginate_by = 20

    def get(self, request):
        imports = container.get_import_history_use_case().execute().imports
        paginator = Paginator(imports, self.paginate_by)
        page_obj = paginator.get_page(request.GET.get('page'))

        return render(request, self.template_name, {
            'imports': page_obj.object_list,
            'page_obj': page_obj,
            'is_paginated': page_obj.has_other_pages(),
        })


def validate_json_ajax(request):
    """Ajax: валидация загруженного JSON без импорта"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)
    
    uploaded_file = request.FILES.get('json_file')
    if not uploaded_file:
        return JsonResponse({'error': 'Файл не выбран'}, status=400)
    
    prepared_file = _prepare_import_file(uploaded_file)
    if not prepared_file.success:
        return JsonResponse({'error': prepared_file.error}, status=400)

    data = prepared_file.data
    
    # Структурная валидация
    validation = (
        container.validate_task_import_json_use_case()
        .execute(
            container.core_form_adapter.validate_task_import_json_request_from_data(
                data,
            )
        )
        .to_dict()
    )
    
    # Dry-run через существующий импортёр
    preview = None
    if validation['is_valid']:
        preview_result = container.preview_task_import_use_case().execute(
            container.core_form_adapter.task_import_preview_request_from_data(data),
        )
        preview = preview_result.preview
        if not preview_result.success:
            validation['warnings'].append(preview_result.warning)
    
    return JsonResponse({
        'filename': prepared_file.filename,
        'file_size': prepared_file.file_size,
        'validation': validation,
        'preview': preview,
    })

@require_POST
def execute_import_ajax(request):
    """Ajax: выполнение импорта"""
    uploaded_file = request.FILES.get('json_file')
    if not uploaded_file:
        return JsonResponse({'error': 'Файл не выбран'}, status=400)

    prepared_submission = (
        container.prepare_task_import_execution_submission_use_case().execute(
            container.core_form_adapter.task_import_execution_submission_from_upload(
                uploaded_file,
                request.POST,
            )
        )
    )
    if not prepared_submission.success:
        return JsonResponse({'error': prepared_submission.error}, status=400)

    result = container.execute_task_import_use_case().execute(
        prepared_submission.import_request,
    )
    return JsonResponse(
        result.to_response_data(),
        status=200 if result.success else 500,
    )


def _prepare_import_file(uploaded_file):
    return container.prepare_task_import_file_use_case().execute(
        container.core_form_adapter.task_import_file_request_from_upload(
            uploaded_file,
        ),
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
        container.core_form_adapter.export_tasks_request_from_query(
            request.GET,
            export_date=export_date,
        ),
    ).payload
    
    content = json.dumps(export_data, ensure_ascii=False, indent=2)
    response = HttpResponse(content, content_type='application/json; charset=utf-8')
    response['Content-Disposition'] = (
        f'attachment; filename="export_{time.strftime("%Y%m%d_%H%M%S")}.json"'
    )
    return response
