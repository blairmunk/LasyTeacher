"""Django command adapter for task fields."""

from core_logic.entities.task import TaskSaveParams, TaskSaveResult
from core_logic.interfaces.task_command_repo import ITaskCommandRepository
from tasks.models import Task


class DjangoTaskCommandRepository(ITaskCommandRepository):
    def create_task(self, params: TaskSaveParams) -> TaskSaveResult:
        task = Task.objects.create(**self._task_values(params))
        return TaskSaveResult(status='created', task_id=str(task.pk))

    def update_task(self, params: TaskSaveParams) -> TaskSaveResult:
        task = Task.objects.filter(pk=params.task_id).first()
        if task is None:
            return TaskSaveResult(status='not_found')

        for field, value in self._task_values(params).items():
            setattr(task, field, value)
        task.save()
        return TaskSaveResult(status='updated', task_id=str(task.pk))

    @staticmethod
    def _task_values(params: TaskSaveParams):
        return {
            'text': params.text,
            'answer': params.answer,
            'topic_id': params.topic_id,
            'subtopic_id': params.subtopic_id,
            'task_type': params.task_type,
            'difficulty': params.difficulty,
            'cognitive_level': params.cognitive_level,
            'content_element': params.content_element,
            'requirement_element': params.requirement_element,
            'short_solution': params.short_solution,
            'full_solution': params.full_solution,
            'hint': params.hint,
            'instruction': params.instruction,
            'estimated_time': params.estimated_time,
            'source_id': params.source_id,
            'source_detail': params.source_detail,
            'grade': params.grade,
            'year': params.year,
            'is_verified': params.is_verified,
            'teacher_notes': params.teacher_notes,
        }
