"""Renderer payload preparation for task-like document rows."""

from core_logic.value_objects.task_print_settings import (
    DEFAULT_BLANK_CELLS_COLUMNS,
    DEFAULT_BLANK_CELLS_ROW_HEIGHT,
)
from core_logic.value_objects.task_content_snapshot import (
    task_content_snapshot_payload,
)
from core_logic.value_objects.variant_content_snapshot import (
    variant_task_content_decisions,
)
from infrastructure.services.blank_cells_payload import (
    build_blank_cells_payload,
)


def build_variant_task_payload(
    variant_task,
    task_payload_formatter=None,
    request=None,
):
    payload = {
        **_variant_task_content_payload(variant_task),
        **variant_task_content_decisions(variant_task),
        'variant_task_id': str(variant_task.pk),
        'order': variant_task.order,
        'max_points': variant_task.max_points,
    }
    if payload['blank_cells_after']:
        payload['blank_cells'] = build_blank_cells_payload(
            {
                'rows': payload['blank_cells_rows'],
                'columns': getattr(
                    variant_task,
                    'blank_cells_columns',
                    DEFAULT_BLANK_CELLS_COLUMNS,
                ),
                'row_height': getattr(
                    variant_task,
                    'blank_cells_row_height',
                    DEFAULT_BLANK_CELLS_ROW_HEIGHT,
                ),
            }
        )
    return format_task_payload(
        payload,
        task_payload_formatter,
        request=request,
    )


def _variant_task_content_payload(variant_task):
    task_snapshot = getattr(variant_task, 'task_snapshot', None)
    if task_snapshot is not None:
        return task_content_snapshot_payload(task_snapshot)
    return build_task_payload(variant_task.task)


def build_original_task_payload(
    task_row,
    task_payload_formatter=None,
    request=None,
):
    payload = {
        **build_task_payload(task_row.task),
        'order': task_row.order,
        'points': task_row.points,
        'max_points': task_row.max_points,
        'pct': task_row.pct,
        'status': task_row.status,
        'group_name': task_row.group_name,
    }
    return format_task_payload(
        payload,
        task_payload_formatter,
        request=request,
    )


def build_task_payload(task):
    return {
        'id': str(task.pk),
        'text': task.text,
        'answer': task.answer,
        'short_solution': task.short_solution,
        'full_solution': task.full_solution,
        'hint': task.hint,
        'instruction': task.instruction,
        'task_type': task.task_type,
        'difficulty': task.difficulty,
        'topic': _related_name(task.topic),
        'subtopic': _related_name(task.subtopic),
        'source': str(task.source) if task.source else '',
        'source_detail': task.source_detail,
    }


def format_task_payload(payload, task_payload_formatter=None, request=None):
    if task_payload_formatter is None:
        return payload
    return task_payload_formatter.format_task_payload(
        payload,
        request=request,
    )


def format_text_payload(text, task_payload_formatter=None, request=None):
    if task_payload_formatter is None:
        return text
    return task_payload_formatter.format_task_payload(
        {'text': text},
        request=request,
    )['text']


def _related_name(value):
    if not value:
        return ''
    if isinstance(value, str):
        return value
    return value.name
