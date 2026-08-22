"""Pure task-bank dry-run analysis."""

from core_logic.entities.task_import import (
    TaskImportClassificationKey,
    TaskImportPreviewFacts,
    TaskImportPreviewLookup,
)
from core_logic.value_objects.task_import import (
    normalize_task_import_uuid,
    parse_task_group_import_reference,
)


class TaskImportPreviewService:
    CLASSIFICATION_FIELDS = (
        ('codifier_content_entries', 'content'),
        ('codifier_requirements', 'requirement'),
    )

    def build_lookup(self, data) -> TaskImportPreviewLookup:
        tasks = self._items(data, 'tasks')
        groups = self._items(data, 'analog_groups')
        topics = self._items(data, 'topics')
        return TaskImportPreviewLookup(
            task_ids=self._valid_ids(task.get('id') for task in tasks),
            group_ids=self._valid_ids([
                *(group.get('id') for group in groups),
                *(
                    self._reference_value(reference)
                    for task in tasks
                    for reference in task.get('groups', [])
                ),
            ]),
            topic_ids=self._valid_ids([
                *(topic.get('id') for topic in topics),
                *(self._reference_value(task.get('topic')) for task in tasks),
            ]),
            subtopic_ids=self._valid_ids([
                *(
                    subtopic.get('id')
                    for topic in topics
                    for subtopic in topic.get('subtopics', [])
                    if isinstance(subtopic, dict)
                ),
                *(
                    self._reference_value(task.get('subtopic'))
                    for task in tasks
                ),
            ]),
            classifications=tuple(sorted(set(
                key
                for task in tasks
                for key in self._classification_keys(task)
            ))),
        )

    def build(self, data, facts: TaskImportPreviewFacts):
        tasks = self._items(data, 'tasks')
        groups = self._items(data, 'analog_groups')
        topics = self._items(data, 'topics')
        task_counts = self._uuid_counts(
            (task.get('id') for task in tasks),
            facts.existing_task_ids,
        )
        group_counts = self._uuid_counts(
            (group.get('id') for group in groups),
            facts.existing_group_ids,
        )
        dependencies = self._dependencies(
            tasks,
            groups,
            topics,
            facts,
        )
        return {
            'file_counts': {
                'tasks': len(tasks),
                'groups': len(groups),
                'topics': len(topics),
                'sources': len(self._items(data, 'sources')),
                'images': len(self._items(data, 'task_images')),
            },
            'task_uuid_counts': task_counts,
            'group_uuid_counts': group_counts,
            'dependency_counts': dependencies,
        }

    def _dependencies(self, tasks, groups, topics, facts):
        declared_groups = set(self._valid_ids(
            group.get('id') for group in groups
        ))
        declared_topics = set(self._valid_ids(
            topic.get('id') for topic in topics
        ))
        declared_subtopics = {
            subtopic_id: topic_id
            for topic in topics
            if (topic_id := self._normalize_uuid(topic.get('id')))
            for subtopic in topic.get('subtopics', [])
            if isinstance(subtopic, dict)
            if (subtopic_id := self._normalize_uuid(subtopic.get('id')))
        }

        missing_topics = set()
        missing_subtopics = set()
        missing_groups = set()
        broken_group_references = 0
        missing_classifications = 0

        for task in tasks:
            topic_id = self._normalize_uuid(
                self._reference_value(task.get('topic')),
            )
            if (
                topic_id
                and topic_id not in declared_topics
                and topic_id not in facts.existing_topic_ids
            ):
                missing_topics.add(topic_id)

            subtopic_id = self._normalize_uuid(
                self._reference_value(task.get('subtopic')),
            )
            if subtopic_id:
                parent_id = (
                    declared_subtopics.get(subtopic_id)
                    or facts.subtopic_topic_ids.get(subtopic_id)
                )
                if parent_id != topic_id:
                    missing_subtopics.add(subtopic_id)

            for reference in task.get('groups', []):
                try:
                    group_id = parse_task_group_import_reference(
                        reference,
                    ).group_id
                except ValueError:
                    broken_group_references += 1
                    continue
                if (
                    group_id not in declared_groups
                    and group_id not in facts.existing_group_ids
                ):
                    missing_groups.add(group_id)
                    broken_group_references += 1

            missing_classifications += sum(
                key not in facts.existing_classifications
                for key in self._classification_keys(task)
            )

        return {
            'missing_topics': len(missing_topics),
            'missing_subtopics': len(missing_subtopics),
            'missing_groups': len(missing_groups),
            'broken_references': broken_group_references,
            'missing_classifications': missing_classifications,
        }

    def _classification_keys(self, task):
        for field_name, kind in self.CLASSIFICATION_FIELDS:
            for reference in task.get(field_name, []):
                if not isinstance(reference, dict):
                    continue
                try:
                    year = int(reference.get('year'))
                except (TypeError, ValueError):
                    continue
                yield TaskImportClassificationKey(
                    kind=kind,
                    subject=str(reference.get('subject', '')),
                    exam_type=str(reference.get('exam_type', '')),
                    year=year,
                    code=str(reference.get('code', '')),
                )

    @staticmethod
    def _uuid_counts(values, existing_ids):
        counts = {'existing': 0, 'new': 0, 'invalid': 0}
        for value in values:
            normalized = TaskImportPreviewService._normalize_uuid(value)
            if not normalized:
                counts['invalid'] += 1
            elif normalized in existing_ids:
                counts['existing'] += 1
            else:
                counts['new'] += 1
        return counts

    @staticmethod
    def _valid_ids(values):
        return tuple(sorted(set(filter(None, (
            TaskImportPreviewService._normalize_uuid(value)
            for value in values
        )))))

    @staticmethod
    def _normalize_uuid(value):
        try:
            return normalize_task_import_uuid(value)
        except ValueError:
            return ''

    @staticmethod
    def _reference_value(reference):
        if isinstance(reference, str):
            return reference
        if not isinstance(reference, dict):
            return ''
        return reference.get('id') or reference.get('uuid') or ''

    @staticmethod
    def _items(data, key):
        value = data.get(key, []) if isinstance(data, dict) else []
        if not isinstance(value, list):
            return []
        return [item for item in value if isinstance(item, dict)]
