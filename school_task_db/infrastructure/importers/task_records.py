"""Django task record import component."""

from tasks.models import Task


class TaskRecordImporter:
    def __init__(
        self,
        runtime,
        context,
        topic_importer,
        source_importer,
        classification_importer,
    ):
        self.runtime = runtime
        self.context = context
        self.topic_importer = topic_importer
        self.source_importer = source_importer
        self.classification_importer = classification_importer

    def import_tasks(self, tasks_data):
        self.runtime._write('📝 Импорт заданий...')
        for task_data in tasks_data:
            try:
                self._import_task(task_data)
            except Exception as error:
                preview = task_data.get('text', 'Unknown')[:30]
                self.runtime.log_error(
                    f"Ошибка импорта задания '{preview}': {error}",
                    error,
                )

    def _import_task(self, task_data):
        task_uuid = self.runtime.generate_uuid_if_missing(task_data, 'id')
        task = self.runtime.safe_get_by_uuid(Task, task_uuid)
        if task and not self.runtime.should_create_object(
            task,
            task_data,
            'tasks',
        ):
            if self.runtime.mode == 'update':
                self._update_task(task, task_data)
                self.classification_importer.apply(task, task_data)
                self.runtime.stats.record_updated('tasks', task.pk)
            self.context.add_task(task_uuid, task)
            return
        if task:
            return

        task = self._create_task(task_uuid, task_data)
        if task:
            self.classification_importer.apply(task, task_data)
            self.context.add_task(task_uuid, task)
            self.runtime.stats.record_created('tasks', task.pk)
            self.runtime.log_success(
                f'Создано задание: {task.get_short_uuid()}',
            )

    def _create_task(self, task_uuid, task_data):
        topic = self.topic_importer.resolve(task_data.get('topic'))
        if not topic:
            self.runtime.log_error(
                'Не удалось найти/создать тему для задания '
                f'{task_uuid[-8:]}',
            )
            return None
        subtopic = None
        if 'subtopic' in task_data:
            subtopic = self.topic_importer.resolve_subtopic(
                task_data['subtopic'],
                topic,
            )
        source = self.source_importer.resolve(task_data.get('source'))
        return Task.objects.create(
            id=task_uuid,
            text=task_data['text'],
            answer=task_data.get('answer', ''),
            short_solution=task_data.get('short_solution', ''),
            full_solution=task_data.get('full_solution', ''),
            hint=task_data.get('hint', ''),
            instruction=task_data.get('instruction', ''),
            topic=topic,
            subtopic=subtopic,
            task_type=task_data.get('task_type', 'theoretical'),
            difficulty=task_data.get('difficulty', 3),
            cognitive_level=task_data.get('cognitive_level', 'understand'),
            estimated_time=task_data.get('estimated_time'),
            source=source,
            source_detail=task_data.get('source_detail', ''),
            grade=task_data.get('grade'),
            year=task_data.get('year'),
            is_verified=task_data.get('is_verified', False),
            teacher_notes=task_data.get('teacher_notes', ''),
        )

    def _update_task(self, task, task_data):
        task.text = task_data.get('text', task.text)
        task.answer = task_data.get('answer', task.answer)
        task.short_solution = task_data.get(
            'short_solution',
            task.short_solution,
        )
        task.full_solution = task_data.get(
            'full_solution',
            task.full_solution,
        )
        task.hint = task_data.get('hint', task.hint)
        task.instruction = task_data.get('instruction', task.instruction)
        task.task_type = task_data.get('task_type', task.task_type)
        task.difficulty = task_data.get('difficulty', task.difficulty)
        task.cognitive_level = task_data.get(
            'cognitive_level',
            task.cognitive_level,
        )
        task.estimated_time = task_data.get(
            'estimated_time',
            task.estimated_time,
        )

        topic_data = task_data.get('topic')
        if topic_data:
            topic = self.topic_importer.resolve(topic_data)
            if topic:
                task.topic = topic
                if 'subtopic' in task_data:
                    task.subtopic = self.topic_importer.resolve_subtopic(
                        task_data['subtopic'],
                        topic,
                    )
        if 'source' in task_data:
            source = self.source_importer.resolve(task_data['source'])
            if source:
                task.source = source
        for field in (
            'source_detail',
            'grade',
            'year',
            'is_verified',
            'teacher_notes',
        ):
            if field in task_data:
                setattr(task, field, task_data[field])
        task.save()
        self.runtime.log_success(
            f'Обновлено задание: {task.get_short_uuid()}',
        )
