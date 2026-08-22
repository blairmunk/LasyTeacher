"""Django persistence session for one task-bank import."""

from core_logic.entities.task_import import TaskImportRunSummary
from core_logic.interfaces.task_import import (
    ITaskImportWriteSession,
    ITaskImportWriteSessionFactory,
)
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


class DjangoTaskImportWriteSession(ITaskImportWriteSession):
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
        self.source_importer = TaskSourceImporter(
            self.runtime,
            self.registry,
        )
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

    def import_sources(self, records):
        self.source_importer.import_sources(records)

    def import_groups(self, records):
        self.group_importer.import_groups(records)

    def import_topics(self, records):
        self.topic_importer.import_topics(records)

    def import_tasks(self, records):
        self.record_importer.import_tasks(records)

    def import_task_group_relations(self, records):
        self.group_importer.create_task_relations(records)

    def import_images(self, records):
        self.image_importer.import_images(records)

    def summary(self) -> TaskImportRunSummary:
        stats = self.runtime.stats
        return TaskImportRunSummary(
            created_by_type=stats.created_by_type,
            updated_by_type=stats.updated_by_type,
            skipped_by_type=stats.skipped_by_type,
            errors=len(stats.errors),
            error_messages=tuple(issue.message for issue in stats.errors[:50]),
            warnings=len(stats.warnings),
            warning_messages=tuple(
                issue.message for issue in stats.warnings[:50]
            ),
            context_counts=self.registry.counts(),
        )


class DjangoTaskImportWriteSessionFactory(ITaskImportWriteSessionFactory):
    def __init__(self, *, verbose: bool = True, output=None):
        self.verbose = verbose
        self.output = output or (lambda _message: None)

    def create(self, *, mode: str, create_missing: bool):
        return DjangoTaskImportWriteSession(
            mode=mode,
            verbose=self.verbose,
            create_missing=create_missing,
            output=self.output,
        )
