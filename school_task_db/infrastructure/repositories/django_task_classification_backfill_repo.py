"""Django adapter for legacy task classification backfills."""

from django.db.models import Q

from codifier.models import ContentEntry, Requirement
from core_logic.entities.task_classification_backfill import (
    BackfillContentEntryRef,
    BackfillRequirementRef,
    BackfillTaskRef,
    TaskClassificationBackfillSnapshot,
)
from core_logic.interfaces.task_classification_backfill_repo import (
    ITaskClassificationBackfillRepository,
)
from tasks.models import Task


class DjangoTaskClassificationBackfillRepository(
    ITaskClassificationBackfillRepository,
):
    def get_backfill_snapshot(self):
        tasks = Task.objects.filter(
            Q(content_element__gt='') | Q(requirement_element__gt=''),
        ).prefetch_related(
            'codifier_content_entries__codifier',
            'codifier_requirements__codifier',
        )
        return TaskClassificationBackfillSnapshot(
            tasks=tuple(self._task_ref(task) for task in tasks),
            content_entries=tuple(
                BackfillContentEntryRef(
                    pk=str(entry.pk),
                    codifier_id=str(entry.codifier_id),
                    code=entry.code,
                    topic_id=str(entry.topic_id or ''),
                    subtopic_id=str(entry.subtopic_id or ''),
                )
                for entry in ContentEntry.objects.all()
            ),
            requirements=tuple(
                BackfillRequirementRef(
                    pk=str(requirement.pk),
                    codifier_id=str(requirement.codifier_id),
                    code=requirement.code,
                )
                for requirement in Requirement.objects.all()
            ),
        )

    def apply_backfill_plan(self, plan):
        for mutation in plan.mutations:
            if mutation.relation_type == 'content':
                ContentEntry.objects.get(pk=mutation.target_id).tasks.add(
                    mutation.task_id,
                )
            else:
                Requirement.objects.get(pk=mutation.target_id).tasks.add(
                    mutation.task_id,
                )

    @staticmethod
    def _task_ref(task):
        content_entries = tuple(task.codifier_content_entries.all())
        requirements = tuple(task.codifier_requirements.all())
        return BackfillTaskRef(
            pk=str(task.pk),
            topic_id=str(task.topic_id),
            subtopic_id=str(task.subtopic_id or ''),
            legacy_content_code=task.content_element.strip(),
            legacy_requirement_code=task.requirement_element.strip(),
            content_entry_ids=tuple(str(item.pk) for item in content_entries),
            content_codifier_ids=tuple(
                str(item.codifier_id) for item in content_entries
            ),
            requirement_ids=tuple(str(item.pk) for item in requirements),
            requirement_codifier_ids=tuple(
                str(item.codifier_id) for item in requirements
            ),
        )
