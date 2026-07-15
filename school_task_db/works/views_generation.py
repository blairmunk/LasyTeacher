"""Views для генерации документов через веб-интерфейс"""

import logging
from django.http import JsonResponse, HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.urls import reverse

from core_logic.value_objects.content_config import (
    build_remedial_sheet_generation_options,
    build_work_generation_options,
)
from core_logic.use_cases.get_generated_document_file import (
    GetGeneratedDocumentFileRequest,
)
from core_logic.use_cases.generate_remedial_sheet_document import (
    GenerateRemedialSheetDocumentRequest,
)
from core_logic.use_cases.generate_work_document import GenerateWorkDocumentRequest

from .models import Work, Variant

logger = logging.getLogger(__name__)

@require_http_methods(["POST"])
def generate_work_ajax(request, work_id):
    """Ajax генерация документов с поддержкой hints/instructions"""
    from infrastructure.container import container

    work = get_object_or_404(Work, id=work_id)
    
    try:
        options = build_work_generation_options(request.POST)
        generator_type = options.generator_type

        logger.info(f"🌐 Веб-генерация {generator_type} для работы {work.id}: {work.name}")
        logger.info(f"   Тип контента: {options.answer_type}")
        logger.info(
            "   Дополнительно: hints=%s, instructions=%s",
            options.include_hints,
            options.include_instructions,
        )

        result = container.generate_work_document_use_case().execute(
            GenerateWorkDocumentRequest(work_id=str(work.pk), options=options),
        )
        if result.status == 'unsupported_generator':
            return JsonResponse({
                'success': False, 
                'error': f'Неподдерживаемый тип генератора: {generator_type}'
            })
        
        # Подготавливаем информацию о файлах для frontend
        files_info = []
        for file_info in result.files:
            files_info.append({
                'name': file_info.filename,
                'size': f'{file_info.size_kb:.1f} KB',
                'download_url': reverse('works:download_generated_file', kwargs={
                    'file_type': result.file_type,
                    'filename': file_info.filename,
                })
            })
        
        success_message = (
            f'{options.file_type_label} документ создан '
            f'({options.content_description})'
        )
        
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

@require_http_methods(["GET"])
def download_generated_file(request, file_type, filename):
    """Скачивание сгенерированного файла"""
    from infrastructure.container import container

    result = container.get_generated_document_file_use_case().execute(
        GetGeneratedDocumentFileRequest(
            file_type=file_type,
            filename=filename,
        ),
    )

    if result.status == 'unsupported_type':
        raise Http404("Неподдерживаемый тип файла")
    if result.status == 'not_found':
        raise Http404("Файл не найден")
    if not result.file:
        raise Http404("Ошибка чтения файла")

    response = HttpResponse(
        result.file.content,
        content_type=result.file.content_type,
    )
    response['Content-Disposition'] = (
        f'attachment; filename="{result.file.filename}"'
    )
    return response

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

@require_http_methods(["POST"])
def generate_remedial_sheet_ajax(request, variant_id):
    """Ajax генерация рабочего листа «Работа над ошибками»"""
    from infrastructure.container import container

    variant = get_object_or_404(Variant, id=variant_id)

    if variant.variant_type != 'remedial':
        return JsonResponse({
            'status': 'error',
            'message': 'Этот вариант не является работой над ошибками'
        }, status=400)

    try:
        options = build_remedial_sheet_generation_options(request.POST)
        generator_type = options.generator_type

        logger.info(f"Генерация remedial sheet для варианта {variant.id}")

        result = container.generate_remedial_sheet_document_use_case().execute(
            GenerateRemedialSheetDocumentRequest(
                variant_id=str(variant.pk),
                options=options,
            ),
        )

        if not result.files:
            return JsonResponse({
                'status': 'error',
                'message': 'Файлы не были сгенерированы'
            }, status=500)

        download_urls = []
        for file_info in result.files:
            url = reverse('works:download_generated_file', kwargs={
                'file_type': result.file_type,
                'filename': file_info.filename
            })
            download_urls.append({'filename': file_info.filename, 'url': url})

        return JsonResponse({
            'status': 'success',
            'files': download_urls,
            'message': f'Рабочий лист сгенерирован ({generator_type.upper()})'
        })

    except Exception as e:
        logger.error(f'Ошибка генерации remedial sheet: {e}', exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'Ошибка: {str(e)}'
        }, status=500)
