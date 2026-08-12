"""Validate curriculum import definitions without persistence concerns."""

from core_logic.entities.curriculum_import import (
    CurriculumImportDefinition,
    CurriculumImportValidationError,
)


def validate_curriculum_import_definition(
    definition: CurriculumImportDefinition,
) -> None:
    if not definition.subject:
        raise CurriculumImportValidationError('Предмет обязателен.')
    if not definition.sections:
        raise CurriculumImportValidationError(
            'Нужно указать хотя бы один тематический раздел.',
        )
    if len(set(definition.sections)) != len(definition.sections):
        raise CurriculumImportValidationError(
            'Тематические разделы не должны повторяться.',
        )

    topic_names = set()
    subtopic_owners = {}
    for topic in definition.topics:
        if topic.section not in definition.sections:
            raise CurriculumImportValidationError(
                f'Раздел темы «{topic.name}» не объявлен: {topic.section}',
            )
        if topic.name in topic_names:
            raise CurriculumImportValidationError(
                f'Повторяется название темы: {topic.name}',
            )
        topic_names.add(topic.name)
        for subtopic in topic.subtopics:
            if subtopic.name in subtopic_owners:
                raise CurriculumImportValidationError(
                    f'Повторяется название подтемы: {subtopic.name}',
                )
            subtopic_owners[subtopic.name] = topic.name

    binding_keys = set()
    for binding in definition.bindings:
        key = (binding.codifier_short_name, binding.content_code)
        if key in binding_keys:
            raise CurriculumImportValidationError(
                'Повторяется привязка элемента кодификатора: '
                f'{binding.codifier_short_name} {binding.content_code}',
            )
        binding_keys.add(key)
        if binding.topic_name not in topic_names:
            raise CurriculumImportValidationError(
                f'Тема привязки не объявлена: {binding.topic_name}',
            )
        if not binding.subtopic_name:
            continue
        owner = subtopic_owners.get(binding.subtopic_name)
        if owner is None:
            raise CurriculumImportValidationError(
                f'Подтема привязки не объявлена: {binding.subtopic_name}',
            )
        if owner != binding.topic_name:
            raise CurriculumImportValidationError(
                f'Подтема «{binding.subtopic_name}» не относится к теме '
                f'«{binding.topic_name}».',
            )
