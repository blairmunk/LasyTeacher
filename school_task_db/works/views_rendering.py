"""Views for document rendering through the web interface."""

import logging

from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods

from infrastructure.container import container
from core_logic.use_cases.get_rendered_document_file import (
    GetRenderedDocumentFileRequest,
)

logger = logging.getLogger(__name__)


def _json_response(spec):
    if spec.is_not_found:
        raise Http404(spec.not_found_message)
    return JsonResponse(spec.payload, status=spec.status_code)


@require_http_methods(["POST"])
def render_work_ajax(request, work_id):
    """Render a work document from its snapshot and print settings."""
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
        renderer_type = document_request.render_target.renderer_type

        logger.info("Web render %s for work %s", renderer_type, work_id)
        logger.info(
            "Print overrides: %s",
            document_request.print_overrides,
        )

        result = container.render_work_document_use_case().execute(
            document_request,
        )
        return _json_response(
            container.work_document_web_presenter.work_document_response(
                result,
                document_request.render_target,
                document_request.print_overrides,
            )
        )

    except Http404:
        raise
    except Exception as error:
        logger.error(
            "Ошибка веб-рендера %s для работы %s: %s",
            renderer_type,
            work_id,
            error,
            exc_info=True,
        )
        return _json_response(
            container
            .work_document_web_presenter
            .work_exception_response(error)
        )


@require_http_methods(["GET"])
def download_rendered_file(request, file_type, filename):
    """Download a rendered document file."""
    result = container.get_rendered_document_file_use_case().execute(
        GetRenderedDocumentFileRequest(
            file_type=file_type,
            filename=filename,
        ),
    )
    response = container.rendered_document_file_presenter.response(
        result,
        disposition='attachment',
    )
    if response is not None:
        return response
    raise Http404(
        container
        .rendered_document_file_presenter
        .download_error_message(result)
    )

@require_http_methods(["GET"])
def render_status_ajax(request):
    """Ajax status check for document rendering."""
    return JsonResponse(
        container.work_document_web_presenter.render_status_payload()
    )


@require_http_methods(["POST"])
def render_remedial_sheet_ajax(request, variant_id):
    """Ajax rendering for remedial sheet documents."""
    try:
        document_request = (
            container.work_form_adapter.render_remedial_sheet_request_from_post(
                request.POST,
                variant_id=str(variant_id),
            )
        )

        logger.info(f"Рендер remedial sheet для варианта {variant_id}")

        result = container.render_remedial_sheet_document_use_case().execute(
            document_request,
        )
        return _json_response(
            container.work_document_web_presenter.remedial_sheet_response(
                result,
            )
        )

    except Http404:
        raise
    except Exception as error:
        logger.error('Ошибка рендера remedial sheet: %s', error, exc_info=True)
        return _json_response(
            container
            .work_document_web_presenter
            .remedial_exception_response(error)
        )


@require_http_methods(["POST"])
def render_remedial_sheet_batch_ajax(request, work_id):
    """Ajax rendering for all remedial sheet documents in a work."""
    try:
        document_request = (
            container.work_form_adapter
            .render_remedial_sheet_batch_request_from_post(
                request.POST,
                work_id=str(work_id),
            )
        )
        logger.info(
            "Пакетный рендер remedial sheets для работы %s",
            work_id,
        )

        result = (
            container
            .render_remedial_sheet_batch_document_use_case()
            .execute(document_request)
        )
        return _json_response(
            container
            .work_document_web_presenter
            .remedial_sheet_batch_response(
                result,
            )
        )

    except Http404:
        raise
    except Exception as error:
        logger.error(
            "Ошибка пакетного рендера remedial sheets для работы %s: %s",
            work_id,
            error,
            exc_info=True,
        )
        return _json_response(
            container
            .work_document_web_presenter
            .remedial_batch_exception_response(error)
        )
