"""Build immutable task snapshots at the Django persistence boundary."""

from codifier.models import ContentEntry
from core_logic.value_objects.task_content_snapshot import (
    TaskCodifierSnapshot,
    TaskContentSnapshot,
    TaskImageSnapshot,
)


def build_task_content_snapshots(tasks):
    """Return snapshots keyed by task id without leaking ORM rows to core."""
    tasks = list(tasks)
    legacy_entries_by_code = _legacy_content_entries_by_code(tasks)
    return {
        str(task.pk): _build_task_content_snapshot(
            task,
            _task_content_entries(
                task,
                legacy_entries_by_code.get(
                    task.content_element.strip(),
                    (),
                ),
            ),
        )
        for task in tasks
    }


def _build_task_content_snapshot(task, content_entries):
    content_snapshots = tuple(
        TaskCodifierSnapshot(
            codifier_id=str(entry.codifier_id),
            codifier_name=entry.codifier.name,
            codifier_short_name=entry.codifier.short_name,
            code=entry.code,
            name=entry.name,
        )
        for entry in content_entries
    )
    requirements = tuple(
        TaskCodifierSnapshot(
            codifier_id=str(requirement.codifier_id),
            codifier_name=requirement.codifier.name,
            codifier_short_name=requirement.codifier.short_name,
            code=requirement.code,
            name=requirement.name,
        )
        for requirement in task.codifier_requirements.all()
    )
    selected_entries = _select_content_entries(task, content_entries)
    return TaskContentSnapshot(
        task_id=str(task.pk),
        text=task.text,
        answer=task.answer,
        short_solution=task.short_solution,
        full_solution=task.full_solution,
        hint=task.hint,
        instruction=task.instruction,
        task_type=task.task_type,
        task_type_display=task.get_task_type_display(),
        difficulty=task.difficulty,
        difficulty_display=task.get_difficulty_display(),
        topic_id=str(task.topic_id),
        topic_name=task.topic.name,
        topic_section=task.topic.section,
        subject=task.topic.subject,
        subtopic_id=str(task.subtopic_id or ''),
        subtopic_name=task.subtopic.name if task.subtopic_id else '',
        source_id=str(task.source_id or ''),
        source_name=str(task.source) if task.source_id else '',
        source_detail=task.source_detail,
        content_element=task.content_element.strip(),
        requirement_element=task.requirement_element.strip(),
        codifier_content_entries=content_snapshots,
        codifier_requirements=requirements,
        content_element_descriptions=tuple(dict.fromkeys(
            f'{entry.codifier.short_name}: {entry.name}'
            for entry in selected_entries
        )),
        images=tuple(
            TaskImageSnapshot(
                image_id=str(image.pk),
                file_name=image.image.name,
                position=image.position,
                caption=image.caption,
                order=image.order,
            )
            for image in task.images.all()
        ),
    )


def _legacy_content_entries_by_code(tasks):
    codes = {
        task.content_element.strip()
        for task in tasks
        if task.content_element.strip()
    }
    result = {code: [] for code in codes}
    if not codes:
        return result
    for entry in ContentEntry.objects.filter(code__in=codes).select_related(
        'codifier',
        'topic',
        'subtopic',
    ):
        result[entry.code].append(entry)
    return result


def _select_content_entries(task, candidates):
    if not candidates:
        return ()
    requirement_codifier_ids = {
        requirement.codifier_id
        for requirement in task.codifier_requirements.all()
    }
    selected = [
        entry
        for entry in candidates
        if entry.codifier_id in requirement_codifier_ids
    ]
    if not selected and task.subtopic_id:
        selected = [
            entry for entry in candidates
            if entry.subtopic_id == task.subtopic_id
        ]
    if not selected:
        selected = [
            entry for entry in candidates
            if entry.topic_id == task.topic_id
        ]
    if not selected and len(candidates) == 1:
        return tuple(candidates)
    return tuple(selected)


def _task_content_entries(task, legacy_candidates):
    explicit_entries = tuple(task.codifier_content_entries.all())
    if explicit_entries:
        return explicit_entries
    return _select_content_entries(task, legacy_candidates)
