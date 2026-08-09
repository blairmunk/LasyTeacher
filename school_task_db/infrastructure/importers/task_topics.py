"""Django topic and subtopic import reference resolution."""

from typing import Any

from curriculum.models import SubTopic, Topic


class TaskTopicImporter:
    def __init__(self, runtime, context):
        self.runtime = runtime
        self.context = context

    def import_topics(self, topics_data):
        self.runtime._write('📚 Импорт тем...')
        for topic_data in topics_data:
            try:
                topic = self.resolve(topic_data)
                if topic:
                    key = f'{topic.subject}_{topic.grade_level}_{topic.name}'
                    self.context.add_topic(key, topic)
            except Exception as error:
                name = topic_data.get('name', 'Unknown')
                self.runtime.log_error(
                    f'Ошибка импорта темы {name}: {error}',
                    error,
                )

    def resolve(self, topic_data: Any):
        topic = self.find(topic_data)
        if topic:
            return topic
        if not self.runtime.create_missing or not isinstance(topic_data, dict):
            return None
        try:
            topic = Topic.objects.create(
                name=topic_data['name'],
                subject=topic_data.get('subject', 'Не указан'),
                grade_level=topic_data.get('grade_level'),
                section=topic_data.get('section', ''),
                description=topic_data.get('description', ''),
                order=topic_data.get('order', 1),
            )
            self.runtime.stats.record_created('topics', topic.pk)
            self.runtime.log_success(f'Создана тема: {topic.name}')
            return topic
        except Exception as error:
            self.runtime.log_error(f'Ошибка создания темы: {error}', error)
            return None

    @staticmethod
    def find(topic_data: Any):
        if not topic_data:
            return None
        if isinstance(topic_data, str):
            return Topic.objects.filter(name=topic_data).first()
        if not isinstance(topic_data, dict):
            return None

        filters = {
            field: topic_data[field]
            for field in ('name', 'subject', 'grade_level')
            if field in topic_data
        }
        if not filters:
            return None
        return Topic.objects.filter(**filters).first()

    def resolve_subtopic(self, subtopic_data: Any, topic: Topic):
        if not subtopic_data or not topic:
            return None
        name = (
            subtopic_data
            if isinstance(subtopic_data, str)
            else subtopic_data.get('name')
        )
        if not name:
            return None

        subtopic = SubTopic.objects.filter(topic=topic, name=name).first()
        if subtopic or not self.runtime.create_missing:
            return subtopic
        try:
            details = subtopic_data if isinstance(subtopic_data, dict) else {}
            subtopic = SubTopic.objects.create(
                topic=topic,
                name=name,
                description=details.get('description', ''),
                order=details.get('order', 1),
            )
            self.runtime.log_success(f'Создана подтема: {name}')
            return subtopic
        except Exception as error:
            self.runtime.log_error(
                f'Ошибка создания подтемы: {error}',
                error,
            )
            return None
