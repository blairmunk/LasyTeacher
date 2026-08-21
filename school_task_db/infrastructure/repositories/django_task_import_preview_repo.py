"""Batch Django lookups for task import dry-run analysis."""

from codifier.models import ContentEntry, Requirement
from core_logic.entities.task_import import (
    TaskImportClassificationKey,
    TaskImportPreviewFacts,
    TaskImportPreviewLookup,
)
from core_logic.interfaces.task_import import ITaskImportPreviewRepository
from curriculum.models import SubTopic, Topic
from task_groups.models import AnalogGroup
from tasks.models import Task


class DjangoTaskImportPreviewRepository(ITaskImportPreviewRepository):
    CLASSIFICATION_MODELS = {
        'content': ContentEntry,
        'requirement': Requirement,
    }

    def get_facts(
        self,
        lookup: TaskImportPreviewLookup,
    ) -> TaskImportPreviewFacts:
        return TaskImportPreviewFacts(
            existing_task_ids=self._existing_ids(Task, lookup.task_ids),
            existing_group_ids=self._existing_ids(
                AnalogGroup,
                lookup.group_ids,
            ),
            existing_topic_ids=self._existing_ids(Topic, lookup.topic_ids),
            subtopic_topic_ids={
                str(subtopic_id): str(topic_id)
                for subtopic_id, topic_id in SubTopic.objects.filter(
                    pk__in=lookup.subtopic_ids,
                ).values_list('pk', 'topic_id')
            },
            existing_classifications=self._existing_classifications(
                lookup.classifications,
            ),
        )

    @staticmethod
    def _existing_ids(model, object_ids):
        if not object_ids:
            return frozenset()
        return frozenset(
            str(object_id)
            for object_id in model.objects.filter(
                pk__in=object_ids,
            ).values_list('pk', flat=True)
        )

    def _existing_classifications(self, requested):
        existing = set()
        for kind, model in self.CLASSIFICATION_MODELS.items():
            keys = {key for key in requested if key.kind == kind}
            if not keys:
                continue
            rows = model.objects.filter(
                codifier__subject__in={key.subject for key in keys},
                codifier__exam_type__in={key.exam_type for key in keys},
                codifier__year__in={key.year for key in keys},
                code__in={key.code for key in keys},
            ).values_list(
                'codifier__subject',
                'codifier__exam_type',
                'codifier__year',
                'code',
            )
            existing.update(
                key
                for row in rows
                if (key := TaskImportClassificationKey(kind, *row)) in keys
            )
        return frozenset(existing)
