"""Validation rules for task curriculum references."""


def validate_task_topic_selection(
    topic_id: str,
    subtopic_id: str | None = None,
    subtopic_topic_id: str | None = None,
) -> tuple[str, ...]:
    if not topic_id:
        return ('Тема обязательна для выбора',)
    if subtopic_id and str(subtopic_topic_id or '') != str(topic_id):
        return ('Выбранная подтема не принадлежит выбранной теме',)
    return ()
