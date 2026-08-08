"""Django read adapter for work list, form, and detail screens."""

from django.db.models import Count, Sum

from core_logic.entities.work import (
    WorkDetailAnalogGroup,
    WorkDetailContentBlock,
    WorkDetailSpecGroup,
    WorkDetailVariant,
    WorkDetailWork,
    WorkListItem,
)
from core_logic.interfaces.work_read_repo import IWorkReadRepository
from task_groups.models import AnalogGroup, TaskGroup
from works.models import Variant, Work, WorkAnalogGroup, WorkContentBlock


class DjangoWorkReadRepository(IWorkReadRepository):
    def get_list_works(self, filters=None):
        queryset = Work.objects.annotate(
            variant_count=Count('variant'),
        )
        if filters:
            if filters.q:
                queryset = queryset.filter(name__icontains=filters.q)
            if filters.work_type:
                queryset = queryset.filter(work_type=filters.work_type)
            if filters.hide_remedial:
                queryset = queryset.exclude(work_type='remedial')
            if filters.variant_status == 'with_variants':
                queryset = queryset.filter(variant_count__gt=0)
            elif filters.variant_status == 'without_variants':
                queryset = queryset.filter(variant_count=0)

        return [
            WorkListItem(
                pk=str(work.pk),
                name=work.name,
                duration=work.duration,
                created_at=work.created_at,
                variant_count=work.variant_count,
                work_type=work.work_type,
                work_type_display=work.get_work_type_display(),
                assessment_mode=work.assessment_mode,
            )
            for work in queryset.order_by('-created_at')
        ]

    def get_work_form_analog_group_options(self):
        return AnalogGroup.objects.all()

    def get_work_detail(self, work_id: str):
        work = Work.objects.filter(pk=work_id).first()
        if work is None:
            return None

        return WorkDetailWork(
            pk=str(work.pk),
            name=work.name,
            work_type=work.work_type,
            work_type_display=work.get_work_type_display(),
            duration=work.duration,
            max_score=work.max_score,
            variant_count=Variant.objects.filter(work_id=work_id).count(),
            created_at=work.created_at,
            updated_at=work.updated_at,
            assessment_mode=work.assessment_mode,
            event_count=work.event_set.count(),
        )

    def get_detail_variants(self, work_id: str):
        result = []
        variants = Variant.objects.filter(
            work_id=work_id,
        ).select_related(
            'assigned_student',
            'source_participation__student',
        ).annotate(
            task_count_value=Count('varianttask'),
            total_max_points_value=Sum('varianttask__max_points'),
        )
        for variant in variants:
            personal_student = variant.assigned_student
            if personal_student is None and variant.source_participation:
                personal_student = variant.source_participation.student
            result.append(
                WorkDetailVariant(
                    pk=str(variant.pk),
                    number=variant.number,
                    short_uuid=variant.get_short_uuid(),
                    task_count=variant.task_count_value,
                    total_max_points=variant.total_max_points_value or 0,
                    created_at=variant.created_at,
                    variant_type=variant.variant_type,
                    has_personal_student=bool(personal_student),
                    personal_student_name=(
                        personal_student.get_short_name()
                        if personal_student
                        else ''
                    ),
                )
            )
        return result

    def get_detail_analog_groups(self, work_id: str):
        return [
            self._build_work_detail_spec_group(work_group)
            for work_group in WorkAnalogGroup.objects.filter(
                work_id=work_id,
            ).select_related(
                'analog_group',
            ).order_by('order', 'pk')
        ]

    def get_detail_content_blocks(self, work_id: str):
        return [
            WorkDetailContentBlock(
                pk=str(block.pk),
                content_type=block.content_type,
                order=block.order,
                title=block.title,
                body=block.body,
                topic_ids=tuple(
                    str(topic.pk)
                    for topic in block.topics.all()
                ),
                include_subtopics=block.include_subtopics,
            )
            for block in WorkContentBlock.objects.filter(
                work_id=work_id,
            ).prefetch_related('topics').order_by('order', 'pk')
        ]

    def _build_work_detail_spec_group(self, work_group):
        return WorkDetailSpecGroup(
            order=work_group.order,
            analog_group=WorkDetailAnalogGroup(
                pk=str(work_group.analog_group.pk),
                name=work_group.analog_group.name,
                task_count=TaskGroup.objects.filter(
                    group=work_group.analog_group,
                ).count(),
            ),
            count=work_group.count,
            weight=work_group.weight,
            selection_id=str(work_group.pk),
            bank_role_filter=work_group.bank_role_filter,
            render_mode=work_group.render_mode,
            is_assessable=work_group.is_assessable,
            blank_cells_after=work_group.blank_cells_after,
            blank_cells_rows=work_group.blank_cells_rows,
            task_bank_roles=self._task_bank_roles(
                work_group.analog_group_id,
            ),
        )

    @staticmethod
    def _task_bank_roles(analog_group_id):
        return tuple(
            TaskGroup.objects.filter(
                group_id=analog_group_id,
            ).order_by('pk').values_list('bank_role', flat=True)
        )
