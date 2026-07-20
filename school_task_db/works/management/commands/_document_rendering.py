from django.core.management.base import CommandError

from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_GENERATED,
    DOCUMENT_RENDER_STATUS_NOT_FOUND,
    DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER,
)
from core_logic.use_cases.render_work_document import RenderWorkDocumentRequest
from core_logic.value_objects.document_render_options import WorkDocumentRenderOptions


def render_work_document_with_container(
    render_container,
    work_id: str,
    renderer_type: str,
    page_format: str = 'A4',
    with_answers: bool = False,
):
    return render_container.render_work_document_use_case().execute(
        RenderWorkDocumentRequest(
            work_id=str(work_id),
            options=WorkDocumentRenderOptions(
                renderer_type=renderer_type,
                pdf_format=page_format,
                answer_type=(
                    'with_answers'
                    if with_answers
                    else 'tasks_only'
                ),
            ),
        )
    )


def raise_for_work_document_render_error(
    result,
    work_id: str,
    renderer_type: str,
):
    if result.status == DOCUMENT_RENDER_STATUS_NOT_FOUND:
        raise CommandError(f'Work {work_id} not found')
    if result.status == DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER:
        raise CommandError(f'Unsupported renderer: {renderer_type}')
    if result.status != DOCUMENT_RENDER_STATUS_GENERATED:
        raise CommandError(f'Document render failed: {result.status}')


def write_work_document_render_result(command, result, file_type_label=None):
    label = file_type_label or result.file_type
    command.stdout.write(
        command.style.SUCCESS(
            f'Created {label} document for {result.source_name}'
        )
    )
    for generated_file in result.files:
        command.stdout.write(
            f'  {generated_file.filename} '
            f'({generated_file.size_kb:.1f} KB)'
        )
