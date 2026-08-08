"""Django read adapter for task database diagnostics."""

from django.db.models import Count

from core_logic.entities.report import (
    ReportAnalogGroupRef,
    ReportCourseRef,
    ReportTaskUsageRef,
    ReportVariantRef,
    ReportWorkRef,
    TaskCoverageFact,
    TaskDBHealthSource,
    TaskDistributionFact,
    TaskGroupSizeFact,
)
from core_logic.interfaces.report_repo import ITaskDBHealthRepository
from curriculum.models import Course
from task_groups.models import AnalogGroup, TaskGroup
from tasks.models import Task
from works.models import Variant, Work, WorkAnalogGroup


class DjangoTaskDBHealthRepository(ITaskDBHealthRepository):
    def get_task_db_health_source(self):
        total_tasks = Task.objects.count()
        group_records = list(
            AnalogGroup.objects.annotate(
                task_count=Count('taskgroup'),
            ).order_by('name'),
        )
        total_works = Work.objects.count()
        total_variants = Variant.objects.count()
        orphan_variants = Variant.objects.filter(work__isnull=True)
        tasks_in_groups = set(TaskGroup.objects.values_list('task_id', flat=True))
        ungrouped_count = Task.objects.exclude(id__in=tasks_in_groups).count()
        works_no_variants = Work.objects.annotate(
            variant_count=Count('variant'),
        ).filter(variant_count=0)
        works_no_spec = Work.objects.annotate(
            spec_count=Count('workanaloggroup'),
        ).filter(spec_count=0)

        type_labels = dict(getattr(Task, 'TASK_TYPE_CHOICES', ()))
        return TaskDBHealthSource(
            total_tasks=total_tasks,
            total_works=total_works,
            total_variants=total_variants,
            orphan_variants_count=orphan_variants.count(),
            orphan_variant_samples=[
                self._variant_ref(variant)
                for variant in orphan_variants.order_by('-created_at')[:10]
            ],
            group_sizes=[
                TaskGroupSizeFact(
                    group=self._analog_group_ref(group),
                    task_count=group.task_count,
                )
                for group in group_records
            ],
            coverage=[
                TaskCoverageFact(
                    work=self._work_ref(work_group.work),
                    group=self._analog_group_ref(work_group.analog_group),
                    needed=work_group.count,
                    available=work_group.available,
                )
                for work_group in WorkAnalogGroup.objects.select_related(
                    'work',
                    'analog_group',
                ).annotate(available=Count('analog_group__taskgroup'))
            ],
            ungrouped_tasks_count=ungrouped_count,
            works_no_variants_count=works_no_variants.count(),
            works_no_variant_samples=[
                self._work_ref(work)
                for work in works_no_variants[:10]
            ],
            works_no_spec_count=works_no_spec.count(),
            works_no_spec_samples=[
                self._work_ref(work)
                for work in works_no_spec[:10]
            ],
            difficulty_counts=[
                TaskDistributionFact(
                    key=item['difficulty'],
                    count=item['count'],
                )
                for item in Task.objects.values('difficulty').annotate(
                    count=Count('id'),
                ).order_by('difficulty')
            ],
            type_counts=[
                TaskDistributionFact(
                    key=item['task_type'],
                    count=item['count'],
                    label=type_labels.get(
                        item['task_type'],
                        item['task_type'] or '—',
                    ),
                )
                for item in Task.objects.values('task_type').annotate(
                    count=Count('id'),
                ).order_by('-count')
            ],
            most_used_tasks=[
                self._task_usage_ref(task)
                for task in Task.objects.annotate(
                    variant_count=Count('varianttask'),
                ).filter(variant_count__gt=0).order_by('-variant_count')[:10]
            ],
            unverified_tasks_count=Task.objects.filter(
                is_verified=False,
            ).count(),
            no_source_tasks_count=Task.objects.filter(
                source__isnull=True,
            ).count(),
            no_grade_tasks_count=Task.objects.filter(
                grade__isnull=True,
            ).count(),
            courses=[
                ReportCourseRef(pk=str(course.pk), name=course.name)
                for course in Course.objects.filter(is_active=True).order_by(
                    'grade_level',
                    'name',
                )
            ],
        )

    @staticmethod
    def _work_ref(work):
        return ReportWorkRef(
            pk=str(work.pk),
            name=work.name,
            work_type=work.work_type,
            work_type_display=work.get_work_type_display(),
            duration=work.duration,
            variant_count=work.variant_set.count(),
        )

    @staticmethod
    def _variant_ref(variant):
        return ReportVariantRef(
            pk=str(variant.pk),
            short_uuid=variant.get_short_uuid(),
            number=variant.number,
            work_name_snapshot=variant.work_name_snapshot,
        )

    @staticmethod
    def _analog_group_ref(group):
        return ReportAnalogGroupRef(pk=str(group.pk), name=group.name)

    @staticmethod
    def _task_usage_ref(task):
        return ReportTaskUsageRef(
            pk=str(task.pk),
            short_uuid=task.get_short_uuid(),
            text=task.text,
            variant_count=task.variant_count,
        )
