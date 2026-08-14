"""Renderer payloads built from an immutable variant content snapshot."""

from core_logic.value_objects.document_recipes import (
    ANSWER_KEY_SECTION,
    ANSWERS_SECTION,
    FULL_SOLUTIONS_SECTION,
    SHORT_SOLUTIONS_SECTION,
    TASK_LIST_SECTION,
    TRAINING_TASKS_SECTION,
)
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
from infrastructure.services.document_build_cache import (
    document_payload_cache,
)
from infrastructure.services.task_document_payloads import (
    build_variant_task_payload,
    format_text_payload,
)


ORDERED_VARIANT_CONTENT_SECTIONS = frozenset((
    TASK_LIST_SECTION,
    TRAINING_TASKS_SECTION,
))
VARIANT_TASK_COLLECTION_SECTIONS = frozenset((
    ANSWER_KEY_SECTION,
    ANSWERS_SECTION,
    SHORT_SOLUTIONS_SECTION,
    FULL_SOLUTIONS_SECTION,
))
WORK_VARIANT_CONTENT_SECTIONS = frozenset((
    TASK_LIST_SECTION,
    *VARIANT_TASK_COLLECTION_SECTIONS,
))
REMEDIAL_VARIANT_CONTENT_SECTIONS = frozenset((
    TRAINING_TASKS_SECTION,
    ANSWERS_SECTION,
    SHORT_SOLUTIONS_SECTION,
    FULL_SOLUTIONS_SECTION,
))


class UnsupportedVariantContentSection(ValueError):
    pass


def build_variant_section_content_payload(
    *,
    variant_id,
    variant_tasks,
    content_blocks=(),
    task_payload_formatter=None,
    request,
):
    """Build the payload shape declared by a variant-backed section."""
    section_type = request.section.section_type
    if section_type in ORDERED_VARIANT_CONTENT_SECTIONS:
        return build_variant_ordered_content_payload(
            variant_id=variant_id,
            variant_tasks=variant_tasks,
            content_blocks=content_blocks,
            options=request.section.options,
            task_payload_formatter=task_payload_formatter,
            request=request,
        )
    if section_type in VARIANT_TASK_COLLECTION_SECTIONS:
        return build_variant_task_collection_payload(
            variant_tasks=variant_tasks,
            task_payload_formatter=task_payload_formatter,
            request=request,
        )
    raise UnsupportedVariantContentSection(section_type)


def build_variant_ordered_content_payload(
    *,
    variant_id,
    variant_tasks,
    content_blocks=(),
    options=None,
    task_payload_formatter=None,
    request=None,
):
    """Build ordered print blocks for a task/content section."""
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
    task_payloads = _variant_task_payloads(
        variant_tasks,
        task_payload_formatter=task_payload_formatter,
        request=request,
    )
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
    }


def build_variant_task_collection_payload(
    *,
    variant_tasks,
    task_payload_formatter=None,
    request=None,
):
    """Build the flat task collection used by answer/solution sections."""
    return {
        'tasks': _variant_task_payloads(
            variant_tasks,
            task_payload_formatter=task_payload_formatter,
            request=request,
        ),
    }


def _variant_task_payloads(
    variant_tasks,
    task_payload_formatter=None,
    request=None,
):
    cache = (
        document_payload_cache(request, namespace='variant_task_payloads')
        if request is not None
        else None
    )
    payloads = []
    for variant_task in variant_tasks:
        cache_key = _variant_task_payload_cache_key(variant_task, request)
        if cache is not None and cache_key in cache:
            payload = cache[cache_key]
        else:
            payload = build_variant_task_payload(
                variant_task,
                task_payload_formatter=task_payload_formatter,
                request=request,
            )
            if cache is not None:
                cache[cache_key] = payload
        payloads.append(payload)
    return payloads


def _variant_task_payload_cache_key(variant_task, request):
    render_target = request.render_target if request is not None else None
    return (
        str(variant_task.pk),
        render_target.renderer_type if render_target else '',
        render_target.page_format if render_target else '',
    )


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
                page_format=(
                    request.render_target.page_format
                    if (
                        request is not None
                        and request.render_target is not None
                    )
                    else 'A4'
                ),
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
