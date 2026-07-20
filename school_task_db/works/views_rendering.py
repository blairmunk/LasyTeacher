"""Views for document rendering through the web interface."""

import logging
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.http import require_http_methods

from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_EMPTY,
    DOCUMENT_RENDER_STATUS_NOT_FOUND,
    DOCUMENT_RENDER_STATUS_NOT_REMEDIAL,
    DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER,
    GENERATED_FILE_STATUS_NOT_FOUND,
    GENERATED_FILE_STATUS_UNSUPPORTED_TYPE,
)

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
        if result.status == DOCUMENT_RENDER_STATUS_NOT_FOUND:
            raise Http404("Работа не найдена")
        if result.status == DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER:
            return JsonResponse({
                'success': False, 
                'error': f'Неподдерживаемый тип рендера: {renderer_type}'
            })
        
        return JsonResponse(
            container.work_form_adapter.rendered_work_document_response_payload(
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
def download_rendered_file(request, file_type, filename):
    """Download a rendered document file."""
    from infrastructure.container import container

    result = container.get_rendered_document_file_use_case().execute(
        container.work_form_adapter.rendered_document_file_request(
            file_type,
            filename,
        ),
    )

    if result.status == GENERATED_FILE_STATUS_UNSUPPORTED_TYPE:
        raise Http404("Неподдерживаемый тип файла")
    if result.status == GENERATED_FILE_STATUS_NOT_FOUND:
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
    if result.status == DOCUMENT_RENDER_STATUS_NOT_FOUND:
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

        if result.status == DOCUMENT_RENDER_STATUS_NOT_FOUND:
            raise Http404("Вариант не найден")
        if result.status == DOCUMENT_RENDER_STATUS_NOT_REMEDIAL:
            return JsonResponse({
                'status': 'error',
                'message': 'Этот вариант не является работой над ошибками'
            }, status=400)
        if result.status == DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER:
            return JsonResponse({
                'status': 'error',
                'message': f'Неподдерживаемый тип рендера: {renderer_type}'
            }, status=400)
        if result.status == DOCUMENT_RENDER_STATUS_EMPTY:
            return JsonResponse({
                'status': 'error',
                'message': 'Файлы не были созданы'
            }, status=500)

        return JsonResponse(
            container.work_form_adapter.remedial_sheet_response_payload(result)
        )

    except Http404:
        raise
    except Exception as e:
        logger.error(f'Ошибка рендера remedial sheet: {e}', exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': f'Ошибка: {str(e)}'
        }, status=500)


@require_http_methods(["POST"])
def render_remedial_sheet_batch_ajax(request, work_id):
    """Ajax rendering for all remedial sheet documents in a work."""
    from infrastructure.container import container

    renderer_type = container.work_form_adapter.document_renderer_type_from_post(
        request.POST,
    )
    try:
        document_request = (
            container.work_form_adapter
            .render_remedial_sheet_batch_request_from_post(
                request.POST,
                work_id=str(work_id),
            )
        )
        renderer_type = document_request.options.renderer_type

        logger.info(
            "Пакетный рендер remedial sheets для работы %s",
            work_id,
        )

        result = (
            container
            .render_remedial_sheet_batch_document_use_case()
            .execute(document_request)
        )

        if result.status == DOCUMENT_RENDER_STATUS_NOT_FOUND:
            raise Http404("Работа не найдена")
        if result.status == DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER:
            return JsonResponse({
                'success': False,
                'error': f'Неподдерживаемый тип рендера: {renderer_type}',
            }, status=400)
        if result.status == DOCUMENT_RENDER_STATUS_EMPTY:
            return JsonResponse({
                'success': False,
                'error': 'В этой работе нет remedial-вариантов для печати.',
            }, status=400)
        if not result.success:
            return JsonResponse({
                'success': False,
                'error': 'Не удалось создать листы работы над ошибками.',
            }, status=500)

        return JsonResponse(
            container.work_form_adapter.remedial_sheet_batch_response_payload(
                result,
            )
        )

    except Http404:
        raise
    except Exception as e:
        logger.error(
            "Ошибка пакетного рендера remedial sheets для работы %s: %s",
            work_id,
            e,
            exc_info=True,
        )
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, status=500)
