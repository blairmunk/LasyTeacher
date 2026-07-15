"""Django implementation of the work repository."""

from typing import List, Set

from django.db import transaction

from core_logic.entities.work import OrphanVariantRef, VariantDeleteInfo
from core_logic.interfaces.work_repo import (
    AttachVariantsToWorkParams,
    CreateVariantParams,
    CreateWorkParams,
    IWorkRepository,
)
from events.models import EventParticipation
from tasks.models import Task
from works.models import Variant, VariantTask, Work, WorkAnalogGroup


class DjangoWorkRepository(IWorkRepository):
    def get_list_works(self):
        return Work.objects.all()

    def get_list_variants(self):
        return Variant.objects.all()

    def get_work_form_analog_group_options(self):
        from task_groups.models import AnalogGroup

        return AnalogGroup.objects.all()

    def get_detail_variants(self, work_id: str):
        return Variant.objects.filter(work_id=work_id)

    def get_detail_analog_groups(self, work_id: str):
        return list(
            WorkAnalogGroup.objects.filter(
                work_id=work_id,
            ).select_related(
                'analog_group',
            ).order_by('order', 'pk')
        )

    def get_spec_preview(self, work_id: str):
        work = Work.objects.get(pk=work_id)
        return work.get_spec_preview()

    def get_variant_detail_tasks(self, variant_id: str):
        return VariantTask.objects.filter(
            variant_id=variant_id,
        ).select_related(
            'task',
            'task__topic',
            'task__subtopic',
        ).order_by('order')

    def get_variant_total_max_points(self, variant_id: str) -> int:
        variant = Variant.objects.get(pk=variant_id)
        return variant.total_max_points

    def get_orphan_variants(self):
        return Variant.objects.filter(work__isnull=True).order_by('-created_at')

    def count_orphan_variants(self) -> int:
        return Variant.objects.filter(work__isnull=True).count()

    def sync_analog_groups_from_variants(self, work_id: str) -> int:
        work = Work.objects.get(pk=work_id)
        return work.sync_analog_groups_from_variants()

    def generate_variants(self, work_id: str, count: int) -> int:
        work = Work.objects.get(pk=work_id)
        return len(work.generate_variants(count=count))

    def get_orphan_variant_refs(
        self,
        variant_ids: List[str],
    ) -> List[OrphanVariantRef]:
        return [
            OrphanVariantRef(
                pk=str(variant.pk),
                variant_type=variant.variant_type,
                total_max_points=variant.total_max_points,
            )
            for variant in Variant.objects.filter(
                pk__in=variant_ids,
                work__isnull=True,
            ).order_by('created_at')
        ]

    def attach_variants_to_work(self, params: AttachVariantsToWorkParams) -> int:
        with transaction.atomic():
            variants = list(
                Variant.objects.select_for_update().filter(
                    pk__in=params.variant_ids,
                    work__isnull=True,
                ).order_by('created_at')
            )
            variant_by_id = {str(variant.pk): variant for variant in variants}
            attached_count = 0
            for number, variant_id in enumerate(params.variant_ids, 1):
                variant = variant_by_id.get(variant_id)
                if not variant:
                    continue
                variant.work_id = params.work_id
                variant.number = number
                variant.work_name_snapshot = params.work_name_snapshot
                variant.max_score_snapshot = params.max_score_snapshot
                variant.save()
                attached_count += 1
        return attached_count

    def get_variant_delete_info(self, variant_id: str) -> VariantDeleteInfo:
        return VariantDeleteInfo(
            task_count=VariantTask.objects.filter(variant_id=variant_id).count(),
            participation_count=EventParticipation.objects.filter(
                variant_id=variant_id,
            ).count(),
        )

    def detach_variant_from_work(self, variant_id: str) -> str:
        variant = Variant.objects.get(pk=variant_id)
        variant_short_id = variant.get_short_uuid()
        variant.work = None
        variant.save()
        return variant_short_id

    def delete_variant(self, variant_id: str) -> str:
        variant = Variant.objects.get(pk=variant_id)
        work_id = str(variant.work_id or '')
        variant.delete()
        return work_id

    def bulk_delete_work_variants(self, work_id: str, variant_ids: List[str]) -> int:
        return Variant.objects.filter(
            pk__in=variant_ids,
            work_id=work_id,
        ).delete()[0]

    def count_work_variants(self, work_id: str) -> int:
        return Variant.objects.filter(work_id=work_id).count()

    def get_variant_task_ids(self, work_id: str) -> Set[str]:
        return {
            str(task_id)
            for task_id in VariantTask.objects.filter(
                variant__work_id=work_id
            ).values_list('task_id', flat=True)
        }

    def get_student_variant_task_ids(
        self,
        work_id: str,
        student_id: str,
        event_id: str,
    ) -> Set[str]:
        participation = EventParticipation.objects.filter(
            event_id=event_id,
            student_id=student_id,
            variant__work_id=work_id,
        ).select_related('variant').first()
        if not participation or not participation.variant_id:
            return set()

        return {
            str(task_id)
            for task_id in VariantTask.objects.filter(
                variant_id=participation.variant_id
            ).values_list('task_id', flat=True)
        }

    def create_work(self, params: CreateWorkParams) -> str:
        work = Work.objects.create(
            name=params.name,
            work_type=params.work_type,
            max_score=params.max_score,
            variant_counter=params.variant_counter,
        )
        return str(work.pk)

    def create_variant_with_tasks(self, params: CreateVariantParams) -> str:
        variant = Variant.objects.create(
            work_id=params.work_id,
            number=params.number,
            work_name_snapshot=params.work_name_snapshot,
            max_score_snapshot=params.max_score_snapshot,
            variant_type=params.variant_type,
            assigned_student_id=params.student_id,
            source_work_id=params.source_work_id,
        )

        task_map = {
            str(task.id): task
            for task in Task.objects.filter(id__in=params.task_ids)
        }
        for order, task_id in enumerate(params.task_ids, 1):
            task = task_map.get(task_id)
            if not task:
                continue
            points = task.difficulty or 1
            VariantTask.objects.create(
                variant=variant,
                task=task,
                order=order,
                weight=points,
                max_points=points,
            )

        return str(variant.pk)
