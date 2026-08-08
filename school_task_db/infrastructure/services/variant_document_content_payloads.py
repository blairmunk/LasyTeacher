"""Renderer payloads built from an immutable variant content snapshot."""

from core_logic.value_objects.variant_content_snapshot import (
    build_variant_content_snapshot_from_sources,
)
from core_logic.value_objects.variant_print_plan import (
    VARIANT_PRINT_BLOCK_BLANK_CELLS,
    VARIANT_PRINT_BLOCK_TASK,
    build_variant_print_overrides_from_options,
    build_variant_print_plan_from_snapshot,
)
from infrastructure.services.blank_cells_payload import (
    build_blank_cells_payload,
)
from infrastructure.services.task_document_payloads import (
    build_variant_task_payload,
    format_text_payload,
)


def build_variant_document_content_payload(
    *,
    variant_id,
    variant_tasks,
    content_blocks=(),
    options=None,
    task_payload_formatter=None,
    request=None,
):
    """Build task and ordered print-block payloads for one variant."""
    variant_tasks = list(variant_tasks)
    content_snapshot = build_variant_content_snapshot_from_sources(
        variant_id=str(variant_id),
        variant_tasks=variant_tasks,
        content_blocks=content_blocks,
    )
    print_plan = build_variant_print_plan_from_snapshot(
        content_snapshot,
        overrides=build_variant_print_overrides_from_options(options),
    )
    task_payloads = [
        build_variant_task_payload(
            variant_task,
            task_payload_formatter=task_payload_formatter,
            request=request,
        )
        for variant_task in variant_tasks
    ]
    task_payloads_by_variant_task_id = {
        task_payload['variant_task_id']: task_payload
        for task_payload in task_payloads
    }
    return {
        'print_blocks': _variant_print_blocks_payload(
            print_plan,
            task_payloads_by_variant_task_id,
            task_payload_formatter=task_payload_formatter,
            request=request,
        ),
        'tasks': task_payloads,
    }


def _variant_print_blocks_payload(
    print_plan,
    task_payloads_by_variant_task_id,
    task_payload_formatter=None,
    request=None,
):
    print_blocks = []
    for block in print_plan.blocks:
        block_payload = {
            'block_type': block.block_type,
            'variant_task_id': block.variant_task_id,
            'task_id': block.task_id,
            'source_selection_id': block.source_selection_id,
            'snapshot_id': block.snapshot_id,
            'source_content_id': block.source_content_id,
            'order': block.order,
            'content_order': block.content_order,
            'content_role': block.content_role,
            'title': block.title,
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
        elif block.block_type in ('theory', 'text'):
            block_payload['content'] = _format_static_content(
                block.block_type,
                block.content,
                task_payload_formatter=task_payload_formatter,
                request=request,
            )
        print_blocks.append(block_payload)
    return print_blocks


def _format_static_content(
    content_type,
    content,
    task_payload_formatter=None,
    request=None,
):
    content = dict(content)
    if content_type == 'text':
        content['body'] = format_text_payload(
            content.get('body', ''),
            task_payload_formatter,
            request=request,
        )
        return content
    content['topics'] = [
        {
            **topic,
            'content': format_text_payload(
                topic.get('content', ''),
                task_payload_formatter,
                request=request,
            ),
            'subtopics': [
                {
                    **subtopic,
                    'content': format_text_payload(
                        subtopic.get('content', ''),
                        task_payload_formatter,
                        request=request,
                    ),
                }
                for subtopic in topic.get('subtopics', ())
            ],
        }
        for topic in content.get('topics', ())
    ]
    return content
