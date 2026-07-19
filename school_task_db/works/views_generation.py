"""Views для генерации документов через веб-интерфейс"""

import logging
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

@require_http_methods(["POST"])
def render_work_ajax(request, work_id):
    """Ajax rendering for work documents with hints/instructions support."""
    from infrastructure.container import container

    renderer_type = container.work_form_adapter.document_renderer_type_from_post(
        request.POST,
    )
    try:
        document_request = (
            container.work_form_adapter.render_work_document_request_from_post(
                request.POST,
                work_id=str(work_id),
            )
        )
        options = document_request.options
        renderer_type = options.renderer_type

        logger.info(f"🌐 Веб-рендер {renderer_type} для работы {work_id}")
        logger.info(f"   Тип контента: {options.answer_type}")
        logger.info(
            "   Дополнительно: hints=%s, instructions=%s",
            options.include_hints,
            options.include_instructions,
        )

        result = container.render_work_document_use_case().execute(
            document_request,
        )
        if result.status == 'not_found':
            raise Http404("Работа не найдена")
        if result.status == 'unsupported_generator':
            return JsonResponse({
                'success': False, 
                'error': f'Неподдерживаемый тип рендера: {renderer_type}'
            })
        
        return JsonResponse(
            container.work_form_adapter.generated_work_document_response_payload(
                result,
                options,
            )
        )
        
    except Http404:
        raise
    except Exception as e:
        logger.error(f"Ошибка веб-рендера {renderer_type} для работы {work_id}: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_http_methods(["GET"])
def download_generated_file(request, file_type, filename):
    """Скачивание сгенерированного файла"""
    from infrastructure.container import container

    result = container.get_generated_document_file_use_case().execute(
        container.work_form_adapter.generated_document_file_request(
            file_type,
            filename,
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
def render_status_ajax(request):
    """Ajax status check for document rendering."""
    return JsonResponse({
        'status': 'ready',
        'message': 'Система готова к рендерингу'
    })

# Дополнительные views для вариантов
@require_http_methods(["POST"])
def render_variant_ajax(request, variant_id):
    """Ajax rendering placeholder for a specific variant."""
    from infrastructure.container import container
    
    result = container.get_variant_generation_placeholder_use_case().execute(
        str(variant_id),
    )
    if result.status == 'not_found':
        raise Http404("Вариант не найден")
    
    return JsonResponse({
        'success': True,
        'message': result.message,
        'files': []
    })

@require_http_methods(["POST"])
def render_remedial_sheet_ajax(request, variant_id):
    """Ajax rendering for remedial sheet documents."""
    from infrastructure.container import container

    try:
        document_request = (
            container.work_form_adapter.render_remedial_sheet_request_from_post(
                request.POST,
                variant_id=str(variant_id),
            )
        )
        options = document_request.options
        renderer_type = options.renderer_type

        logger.info(f"Рендер remedial sheet для варианта {variant_id}")

        result = container.render_remedial_sheet_document_use_case().execute(
            document_request,
        )

        if result.status == 'not_found':
            raise Http404("Вариант не найден")
        if result.status == 'not_remedial':
            return JsonResponse({
                'status': 'error',
                'message': 'Этот вариант не является работой над ошибками'
            }, status=400)
        if result.status == 'unsupported_generator':
            return JsonResponse({
                'status': 'error',
                'message': f'Неподдерживаемый тип рендера: {renderer_type}'
            }, status=400)
        if result.status == 'empty':
            return JsonResponse({
                'status': 'error',
                'message': 'Файлы не были сгенерированы'
            }, status=500)

        return JsonResponse(
            container.work_form_adapter.remedial_sheet_response_payload(result)
        )

    except Http404:
        raise
    except Exception as e:
        logger.error(f'Ошибка генерации remedial sheet: {e}', exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'Ошибка: {str(e)}'
        }, status=500)


# Backward-compatible names while routes/templates migrate from generate to render.
generate_work_ajax = render_work_ajax
generate_variant_ajax = render_variant_ajax
generate_remedial_sheet_ajax = render_remedial_sheet_ajax
generation_status_ajax = render_status_ajax
