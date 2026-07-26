"""Django-backed renderer payloads for one immutable work variant."""

from core_logic.value_objects.task_print_settings import (
    DEFAULT_BLANK_CELLS_COLUMNS,
    DEFAULT_BLANK_CELLS_ROW_HEIGHT,
    DEFAULT_BLANK_CELLS_ROWS,
    TASK_BANK_ROLE_CONTROL,
    TASK_RENDER_MODE_TASK_ONLY,
)
from core_logic.value_objects.variant_content_snapshot import (
    VariantContentItem,
    build_variant_content_snapshot,
)
from core_logic.value_objects.variant_print_plan import (
    VARIANT_PRINT_BLOCK_BLANK_CELLS,
    VARIANT_PRINT_BLOCK_TASK,
    build_variant_print_profile_from_options,
    build_variant_print_plan_from_snapshot,
)
from infrastructure.services.blank_cells_payload import (
    build_blank_cells_payload,
)


class DjangoVariantDocumentPayloadBuilder:
    def __init__(self, task_payload_formatter=None):
        self.task_payload_formatter = task_payload_formatter

    def build(self, variant, request=None):
        variant_tasks = list(
            variant.varianttask_set
            .select_related(
                'task',
                'task__topic',
                'task__subtopic',
                'task__source',
            )
            .order_by('order', 'pk')
        )
        content_snapshot = build_variant_content_snapshot(
            variant_id=str(variant.pk),
            items=[
                _variant_content_item(variant_task)
                for variant_task in variant_tasks
            ],
        )
        print_profile = build_variant_print_profile_from_options(
            request.section.options if request else {},
        )
        print_plan = build_variant_print_plan_from_snapshot(
            content_snapshot,
            profile=print_profile,
        )
        task_payloads = [
            build_variant_task_payload(
                variant_task,
                task_payload_formatter=self.task_payload_formatter,
                request=request,
            )
            for variant_task in variant_tasks
        ]
        task_payloads_by_variant_task_id = {
            task_payload['variant_task_id']: task_payload
            for task_payload in task_payloads
        }
        return {
            'id': str(variant.pk),
            'number': variant.number,
            'title': f'Вариант {variant.number}',
            'max_score': variant.display_max_score,
            'duration': variant.display_duration,
            'print_blocks': _variant_print_blocks_payload(
                print_plan,
                task_payloads_by_variant_task_id,
            ),
            'tasks': task_payloads,
        }


def build_variant_task_payload(
    variant_task,
    task_payload_formatter=None,
    request=None,
):
    task = variant_task.task
    payload = {
        **build_task_payload(task),
        **_variant_task_print_settings(variant_task),
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


def _variant_content_item(variant_task):
    print_settings = _variant_task_print_settings(variant_task)
    return VariantContentItem(
        variant_task_id=str(variant_task.pk),
        task_id=str(variant_task.task_id),
        order=variant_task.order,
        max_points=variant_task.max_points,
        bank_role=print_settings['bank_role'],
        render_mode=print_settings['render_mode'],
        is_assessable=print_settings['is_assessable'],
        blank_cells_after=print_settings['blank_cells_after'],
        blank_cells_rows=print_settings['blank_cells_rows'],
    )


def _variant_print_blocks_payload(
    print_plan,
    task_payloads_by_variant_task_id,
):
    print_blocks = []
    for block in print_plan.blocks:
        block_payload = {
            'block_type': block.block_type,
            'variant_task_id': block.variant_task_id,
            'task_id': block.task_id,
            'order': block.order,
            'content_role': block.content_role,
            'source_render_mode': block.source_render_mode,
            'render_mode': block.render_mode,
            'options': dict(block.options),
        }
        if block.block_type == VARIANT_PRINT_BLOCK_TASK:
            task_payload = task_payloads_by_variant_task_id.get(
                block.variant_task_id,
            )
            if task_payload:
                block_payload['task'] = {
                    **task_payload,
                    **dict(block.options),
                }
        elif block.block_type == VARIANT_PRINT_BLOCK_BLANK_CELLS:
            block_payload['blank_cells'] = build_blank_cells_payload(
                block.options,
            )
        print_blocks.append(block_payload)
    return print_blocks


def _variant_task_print_settings(variant_task):
    return {
        'bank_role': getattr(
            variant_task,
            'bank_role',
            TASK_BANK_ROLE_CONTROL,
        ),
        'render_mode': getattr(
            variant_task,
            'render_mode',
            TASK_RENDER_MODE_TASK_ONLY,
        ),
        'is_assessable': getattr(variant_task, 'is_assessable', True),
        'blank_cells_after': getattr(variant_task, 'blank_cells_after', False),
        'blank_cells_rows': getattr(
            variant_task,
            'blank_cells_rows',
            DEFAULT_BLANK_CELLS_ROWS,
        ),
    }
