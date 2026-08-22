"""Build immutable task snapshots at the Django persistence boundary."""
from core_logic.value_objects.task_content_snapshot import (
    TaskCodifierSnapshot,
    TaskContentSnapshot,
    TaskImageSnapshot,
)


def build_task_content_snapshots(tasks):
    """Return snapshots keyed by task id without leaking ORM rows to core."""
    return {
        str(task.pk): _build_task_content_snapshot(task)
        for task in tasks
    }


def _build_task_content_snapshot(task):
    content_entries = tuple(task.codifier_content_entries.all())
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
    explicit_requirements = tuple(task.codifier_requirements.all())
    requirements = tuple(
        TaskCodifierSnapshot(
            codifier_id=str(requirement.codifier_id),
            codifier_name=requirement.codifier.name,
            codifier_short_name=requirement.codifier.short_name,
            code=requirement.code,
            name=requirement.name,
        )
        for requirement in explicit_requirements
    )
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
        content_element='',
        requirement_element='',
        codifier_content_entries=content_snapshots,
        codifier_requirements=requirements,
        content_element_descriptions=tuple(dict.fromkeys(
            f'{entry.codifier.short_name}: {entry.name}'
            for entry in content_entries
        )),
        images=tuple(
            TaskImageSnapshot(
                image_id=str(image.pk),
                asset_id=str(image.asset_id or ''),
                # Physical paths are retained only when reading old snapshots.
                file_name='',
                position=image.position,
                caption=image.caption,
                order=image.order,
            )
            for image in task.images.all()
        ),
    )
