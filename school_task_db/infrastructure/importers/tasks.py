"""Transactional coordination of Django task-bank import components."""

from typing import Any, Dict

from django.db import transaction

from core_logic.entities.task_import import TaskImportRunSummary
from infrastructure.importers.runtime import (
    TaskImportRegistry,
    TaskImportRuntime,
)
from infrastructure.importers.task_classifications import (
    TaskClassificationImporter,
)
from infrastructure.importers.task_groups import TaskGroupImporter
from infrastructure.importers.task_images import TaskImageImporter
from infrastructure.importers.task_records import TaskRecordImporter
from infrastructure.importers.task_sources import TaskSourceImporter
from infrastructure.importers.task_topics import TaskTopicImporter


class TaskImporter:
    def __init__(
        self,
        *,
        mode: str = 'update',
        verbose: bool = False,
        create_missing: bool = True,
        output=None,
    ):
        self.runtime = TaskImportRuntime(
            mode=mode,
            verbose=verbose,
            create_missing=create_missing,
            output=output,
        )
        self.registry = TaskImportRegistry()
        self.image_importer = TaskImageImporter(self.runtime, self.registry)
        self.group_importer = TaskGroupImporter(self.runtime, self.registry)
        self.source_importer = TaskSourceImporter(self.runtime)
        self.classification_importer = TaskClassificationImporter(
            self.runtime,
        )
        self.topic_importer = TaskTopicImporter(self.runtime, self.registry)
        self.record_importer = TaskRecordImporter(
            self.runtime,
            self.registry,
            self.topic_importer,
            self.source_importer,
            self.classification_importer,
        )

    def import_tasks_from_json(
        self,
        json_data: Dict[str, Any],
    ) -> TaskImportRunSummary:
        self.runtime.validate_mode()
        with transaction.atomic():
            self.runtime.write('🚀 ИМПОРТ ЗАДАНИЙ:')
            if 'sources' in json_data:
                self.source_importer.import_sources(json_data['sources'])
            if 'analog_groups' in json_data:
                self.group_importer.import_groups(json_data['analog_groups'])
            if 'topics' in json_data and self.runtime.create_missing:
                self.topic_importer.import_topics(json_data['topics'])
            if 'tasks' in json_data:
                self.record_importer.import_tasks(json_data['tasks'])
            self.group_importer.create_task_relations(
                json_data.get('tasks', []),
            )
            if 'task_images' in json_data:
                self.image_importer.import_images(json_data['task_images'])

        return self._summary()

    def _summary(self) -> TaskImportRunSummary:
        stats = self.runtime.stats
        return TaskImportRunSummary(
            created_by_type=stats.created_by_type,
            updated_by_type=stats.updated_by_type,
            skipped_by_type=stats.skipped_by_type,
            errors=len(stats.errors),
            error_messages=tuple(issue.message for issue in stats.errors[:50]),
            context_counts=self.registry.counts(),
        )
