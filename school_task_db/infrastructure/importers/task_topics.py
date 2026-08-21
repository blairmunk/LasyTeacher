"""Django UUID-based topic and subtopic import resolution."""

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
                self._import_topic(topic_data)
            except Exception as error:
                name = topic_data.get('name', 'Unknown')
                self.runtime.log_error(
                    f'Ошибка импорта темы {name}: {error}',
                    error,
                )

    def _import_topic(self, topic_data):
        topic_uuid = str(topic_data['id'])
        topic = self.find(topic_data)
        if topic and not self.runtime.should_create_object(
            topic,
            topic_data,
            'topics',
        ):
            if self.runtime.mode == 'update':
                self._update_topic(topic, topic_data)
                self.runtime.stats.record_updated('topics', topic.pk)
        elif not topic and self.runtime.create_missing:
            topic = Topic.objects.create(
                id=topic_uuid,
                name=topic_data['name'],
                subject=topic_data['subject'],
                grade_level=topic_data['grade_level'],
                section=topic_data.get('section', ''),
                description=topic_data.get('description', ''),
                order=topic_data.get('order', 1),
                difficulty_level=topic_data.get('difficulty_level', 1),
            )
            self.runtime.stats.record_created('topics', topic.pk)
            self.runtime.log_success(f'Создана тема: {topic.name}')
        if topic is None:
            return None
        self.context.add_topic(topic_uuid, topic)
        self._import_subtopics(topic, topic_data.get('subtopics', []))
        return topic

    def resolve(self, topic_data: Any):
        return self.find(topic_data)

    def find(self, topic_data: Any):
        topic_uuid = self.reference_id(topic_data)
        if not topic_uuid:
            return None
        return (
            self.context.imported_topics.get(topic_uuid)
            or self.runtime.safe_get_by_uuid(Topic, topic_uuid)
        )

    def resolve_subtopic(self, subtopic_data: Any, topic: Topic):
        if not subtopic_data or not topic:
            return None
        subtopic_uuid = self.reference_id(subtopic_data)
        if not subtopic_uuid:
            return None
        subtopic = (
            self.context.imported_subtopics.get(subtopic_uuid)
            or self.runtime.safe_get_by_uuid(SubTopic, subtopic_uuid)
        )
        if subtopic is None or subtopic.topic_id != topic.pk:
            return None
        return subtopic

    def _import_subtopics(self, topic, subtopics_data):
        for subtopic_data in subtopics_data:
            subtopic_uuid = str(subtopic_data['id'])
            subtopic = self.runtime.safe_get_by_uuid(
                SubTopic,
                subtopic_uuid,
            )
            if subtopic and subtopic.topic_id != topic.pk:
                raise ValueError(
                    f'Подтема {subtopic_uuid[-8:]} принадлежит другой теме',
                )
            if subtopic and not self.runtime.should_create_object(
                subtopic,
                subtopic_data,
                'subtopics',
            ):
                if self.runtime.mode == 'update':
                    self._update_subtopic(subtopic, subtopic_data)
                    self.runtime.stats.record_updated(
                        'subtopics',
                        subtopic.pk,
                    )
            elif not subtopic and self.runtime.create_missing:
                subtopic = SubTopic.objects.create(
                    id=subtopic_uuid,
                    topic=topic,
                    name=subtopic_data['name'],
                    description=subtopic_data.get('description', ''),
                    order=subtopic_data.get('order', 1),
                )
                self.runtime.stats.record_created('subtopics', subtopic.pk)
                self.runtime.log_success(
                    f'Создана подтема: {subtopic.name}',
                )
            if subtopic:
                self.context.add_subtopic(subtopic_uuid, subtopic)

    @staticmethod
    def _update_topic(topic, topic_data):
        update_fields = []
        for field_name in (
            'name',
            'subject',
            'grade_level',
            'section',
            'description',
            'order',
            'difficulty_level',
        ):
            if field_name in topic_data:
                setattr(topic, field_name, topic_data[field_name])
                update_fields.append(field_name)
        if update_fields:
            topic.save(update_fields=update_fields)

    @staticmethod
    def _update_subtopic(subtopic, subtopic_data):
        update_fields = []
        for field_name in ('name', 'description', 'order'):
            if field_name in subtopic_data:
                setattr(subtopic, field_name, subtopic_data[field_name])
                update_fields.append(field_name)
        if update_fields:
            subtopic.save(update_fields=update_fields)

    @staticmethod
    def reference_id(reference):
        if not isinstance(reference, dict):
            return ''
        return str(reference.get('id') or reference.get('uuid') or '')
