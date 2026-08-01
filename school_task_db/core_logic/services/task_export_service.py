"""Pure assembly of the portable task-bank export format."""


class TaskExportService:
    def build(self, tasks, export_date):
        groups = {}
        topics = {}
        sources = {}
        task_rows = []
        images = []

        for task in tasks:
            task_rows.append(self._task_row(task))
            if task.topic:
                key = (
                    task.topic.subject,
                    task.topic.grade_level,
                    task.topic.name,
                )
                topics.setdefault(key, {
                    'name': task.topic.name,
                    'subject': task.topic.subject,
                    'grade_level': task.topic.grade_level,
                    'section': task.topic.section,
                    'description': task.topic.description,
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
            for group in task.groups:
                groups.setdefault(group.pk, {
                    'id': group.pk,
                    'name': group.name,
                    'description': group.description,
                })
            images.extend(self._image_row(image) for image in task.images)

        return {
            'version': '1.1',
            'export_date': export_date,
            'analog_groups': list(groups.values()),
            'topics': list(topics.values()),
            'sources': list(sources.values()),
            'tasks': task_rows,
            'task_images': images,
        }

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
            'content_element': task.content_element,
            'requirement_element': task.requirement_element,
            'estimated_time': task.estimated_time,
            'grade': task.grade,
            'year': task.year,
            'is_verified': task.is_verified,
            'teacher_notes': task.teacher_notes,
            'source_detail': task.source_detail,
            'source': None,
            'groups': [group.pk for group in task.groups],
        }
        if task.topic:
            row['topic'] = {
                'name': task.topic.name,
                'subject': task.topic.subject,
                'grade_level': task.topic.grade_level,
                'section': task.topic.section,
            }
        if task.source:
            row['source'] = {
                'name': task.source.name,
                'short_name': task.source.short_name,
                'source_type': task.source.source_type,
                'author': task.source.author,
                'year': task.source.year,
            }
        return row

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
