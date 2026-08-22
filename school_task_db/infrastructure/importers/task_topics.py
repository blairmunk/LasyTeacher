"""Django UUID-based topic and subtopic import resolution."""

from typing import Any

from core_logic.value_objects.task_import import (
    TASK_IMPORT_ACTION_UPDATE,
    TaskImportConflictError,
    normalize_task_import_uuid,
)
from curriculum.models import SubTopic, Topic


class TaskTopicImporter:
    def __init__(self, runtime, registry):
        self.runtime = runtime
        self.registry = registry

    def import_topics(self, topics_data):
        self.runtime.write('📚 Импорт тем...')
        for topic_data in topics_data:
            try:
                self._import_topic(topic_data)
            except TaskImportConflictError:
                raise
            except Exception as error:
                name = topic_data.get('name', 'Unknown')
                self.runtime.log_error(
                    f'Ошибка импорта темы {name}: {error}',
                    error,
                )

    def _import_topic(self, topic_data):
        topic_uuid = normalize_task_import_uuid(topic_data['id'])
        topic_data['id'] = topic_uuid
        topic = self.find(topic_data)
        action = self.runtime.object_action(
            topic,
            topic_data,
            'topics',
        )
        if topic:
            if action == TASK_IMPORT_ACTION_UPDATE:
                self._update_topic(topic, topic_data)
                self.runtime.stats.record_updated('topics', topic.pk)
        elif self.runtime.create_missing:
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
        self.registry.remember_topic(topic_uuid, topic)
        self._import_subtopics(topic, topic_data.get('subtopics', []))
        return topic

    def resolve(self, topic_data: Any):
        return self.find(topic_data)

    def find(self, topic_data: Any):
        topic_uuid = self.reference_id(topic_data)
        if not topic_uuid:
            return None
        return (
            self.registry.topic(topic_uuid)
            or self.runtime.get_by_uuid(Topic, topic_uuid)
        )

    def resolve_subtopic(self, subtopic_data: Any, topic: Topic):
        if not subtopic_data or not topic:
            return None
        subtopic_uuid = self.reference_id(subtopic_data)
        if not subtopic_uuid:
            return None
        subtopic = (
            self.registry.subtopic(subtopic_uuid)
            or self.runtime.get_by_uuid(SubTopic, subtopic_uuid)
        )
        if subtopic is None or subtopic.topic_id != topic.pk:
            return None
        return subtopic

    def _import_subtopics(self, topic, subtopics_data):
        for subtopic_data in subtopics_data:
            subtopic_uuid = normalize_task_import_uuid(subtopic_data['id'])
            subtopic_data['id'] = subtopic_uuid
            subtopic = self.runtime.get_by_uuid(
                SubTopic,
                subtopic_uuid,
            )
            if subtopic and subtopic.topic_id != topic.pk:
                raise ValueError(
                    f'Подтема {subtopic_uuid[-8:]} принадлежит другой теме',
                )
            action = self.runtime.object_action(
                subtopic,
                subtopic_data,
                'subtopics',
            )
            if subtopic:
                if action == TASK_IMPORT_ACTION_UPDATE:
                    self._update_subtopic(subtopic, subtopic_data)
                    self.runtime.stats.record_updated(
                        'subtopics',
                        subtopic.pk,
                    )
            elif self.runtime.create_missing:
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
                self.registry.remember_subtopic(subtopic_uuid, subtopic)

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
        value = reference.get('id') or reference.get('uuid')
        if not value:
            return ''
        try:
            return normalize_task_import_uuid(value)
        except ValueError:
            return ''
