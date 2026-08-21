"""Pure assembly of the portable task-bank export format."""

from core_logic.value_objects.task_transfer_format import (
    TASK_TRANSFER_FORMAT_VERSION,
)


class TaskExportService:
    def build(
        self,
        tasks,
        export_date,
        *,
        include_groups=True,
        include_topics=True,
    ):
        groups = {}
        topics = {}
        sources = {}
        task_rows = []
        images = []

        for task in tasks:
            task_rows.append(self._task_row(task))
            if include_topics and task.topic:
                topic = topics.setdefault(task.topic.pk, {
                    'id': task.topic.pk,
                    'name': task.topic.name,
                    'subject': task.topic.subject,
                    'grade_level': task.topic.grade_level,
                    'section': task.topic.section,
                    'description': task.topic.description,
                    'subtopics': {},
                })
                if task.subtopic:
                    topic['subtopics'].setdefault(task.subtopic.pk, {
                        'id': task.subtopic.pk,
                        'name': task.subtopic.name,
                        'description': task.subtopic.description,
                        'order': task.subtopic.order,
                    })
            if task.source:
                sources.setdefault(task.source.pk, {
                    'id': task.source.pk,
                    'name': task.source.name,
                    'short_name': task.source.short_name,
                    'source_type': task.source.source_type,
                    'author': task.source.author,
                    'year': task.source.year,
                    'url': task.source.url,
                    'isbn': task.source.isbn,
                })
            if include_groups:
                for group in task.groups:
                    groups.setdefault(group.pk, {
                        'id': group.pk,
                        'name': group.name,
                        'description': group.description,
                        'difficulty': group.difficulty,
                    })
            images.extend(self._image_row(image) for image in task.images)

        payload = {
            'version': TASK_TRANSFER_FORMAT_VERSION,
            'export_date': export_date,
            'sources': list(sources.values()),
            'tasks': task_rows,
            'task_images': images,
        }
        if include_groups:
            payload['analog_groups'] = list(groups.values())
        if include_topics:
            payload['topics'] = [
                {
                    **topic,
                    'subtopics': list(topic['subtopics'].values()),
                }
                for topic in topics.values()
            ]
        return payload

    @staticmethod
    def _task_row(task):
        row = {
            'id': task.pk,
            'text': task.text,
            'answer': task.answer,
            'short_solution': task.short_solution,
            'full_solution': task.full_solution,
            'hint': task.hint,
            'instruction': task.instruction,
            'difficulty': task.difficulty,
            'task_type': task.task_type,
            'cognitive_level': task.cognitive_level,
            'codifier_content_entries': [
                TaskExportService._classification_row(item)
                for item in task.content_entries
            ],
            'codifier_requirements': [
                TaskExportService._classification_row(item)
                for item in task.requirements
            ],
            'estimated_time': task.estimated_time,
            'grade': task.grade,
            'year': task.year,
            'is_verified': task.is_verified,
            'teacher_notes': task.teacher_notes,
            'source_detail': task.source_detail,
            'source': None,
            'groups': [
                {
                    'id': group.pk,
                    'bank_role': group.bank_role,
                }
                for group in task.groups
            ],
        }
        if task.topic:
            row['topic'] = {'id': task.topic.pk}
        if task.subtopic:
            row['subtopic'] = {'id': task.subtopic.pk}
        if task.source:
            row['source'] = {
                'id': task.source.pk,
                'name': task.source.name,
                'short_name': task.source.short_name,
                'source_type': task.source.source_type,
                'author': task.source.author,
                'year': task.source.year,
            }
        return row

    @staticmethod
    def _classification_row(item):
        return {
            'subject': item.subject,
            'exam_type': item.exam_type,
            'year': item.year,
            'code': item.code,
            'name': item.name,
            'codifier_name': item.codifier_name,
        }

    @staticmethod
    def _image_row(image):
        return {
            'id': image.pk,
            'task_id': image.task_id,
            'filename': image.filename,
            'position': image.position,
            'caption': image.caption,
            'order': image.order,
            'base64_data': image.base64_data,
        }
