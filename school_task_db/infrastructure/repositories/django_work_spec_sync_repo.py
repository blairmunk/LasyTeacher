"""Django adapter for restoring work specifications from variants."""

from typing import Optional

from django.db import transaction

from core_logic.entities.work_spec_sync import (
    WorkSpecSyncItem,
    WorkSpecSyncSaveResult,
    WorkSpecSyncSource,
)
from core_logic.interfaces.work_spec_sync_repo import IWorkSpecSyncRepository
from task_groups.models import TaskGroup
from works.models import VariantTask, Work, WorkAnalogGroup


class DjangoWorkSpecSyncRepository(IWorkSpecSyncRepository):
    def get_work_spec_sync_source(
        self,
        work_id: str,
    ) -> Optional[WorkSpecSyncSource]:
        work = Work.objects.select_for_update().filter(pk=work_id).first()
        if work is None:
            return None
        task_rows = list(
            VariantTask.objects.filter(
                variant__work=work,
            ).order_by(
                'variant__number',
                'variant_id',
                'order',
            ).values_list(
                'variant_id',
                'task_id',
            )
        )
        group_ids_by_task_id = {}
        for task_id, group_id in (
            TaskGroup.objects.filter(
                task_id__in={task_id for _, task_id in task_rows},
            ).order_by('pk').values_list('task_id', 'group_id')
        ):
            group_ids_by_task_id.setdefault(task_id, []).append(group_id)

        group_ids_by_variant_id = {}
        for variant_id, task_id in task_rows:
            group_ids_by_variant_id.setdefault(variant_id, []).extend(
                group_ids_by_task_id.get(task_id, ()),
            )

        return WorkSpecSyncSource(
            variant_counter=work.variant_counter,
            variant_group_ids=tuple(
                tuple(str(group_id) for group_id in group_ids)
                for group_ids in group_ids_by_variant_id.values()
            ),
        )

    def save_work_spec_sync_plan(
        self,
        work_id: str,
        expected_variant_counter: int,
        plan: tuple[WorkSpecSyncItem, ...],
    ) -> WorkSpecSyncSaveResult:
        with transaction.atomic():
            work = Work.objects.select_for_update().filter(pk=work_id).first()
            if work is None:
                return WorkSpecSyncSaveResult(status='not_found')
            if work.variant_counter != expected_variant_counter:
                return WorkSpecSyncSaveResult(status='conflict')

            created_count = 0
            for item in plan:
                _, was_created = WorkAnalogGroup.objects.update_or_create(
                    work=work,
                    analog_group_id=item.analog_group_id,
                    defaults={
                        'count': item.count,
                        'order': item.order,
                    },
                )
                if was_created:
                    created_count += 1
            return WorkSpecSyncSaveResult(
                status='saved',
                created_count=created_count,
            )
