"""Django read adapter for task-group catalog pages."""

from django.db.models import Avg, Count, OuterRef, Q, Subquery

from core_logic.entities.task import (
    AddTasksToGroupTask,
    SelectOption,
    TaskGroupDetailGroup,
    TaskGroupDetailTask,
    TaskGroupListFilters,
    TaskGroupListItem,
)
from core_logic.interfaces.task_group_catalog_repo import (
    ITaskGroupCatalogRepository,
)
from task_groups.models import AnalogGroup, TaskGroup
from tasks.models import Task


class DjangoTaskGroupCatalogRepository(ITaskGroupCatalogRepository):
    @staticmethod
    def _parse_int(value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def get_list_task_groups(self, filters: TaskGroupListFilters):
        queryset = AnalogGroup.objects.annotate(
            task_count=Count('taskgroup'),
            avg_difficulty=Avg('taskgroup__task__difficulty'),
        ).order_by('name')

        queryset = queryset.annotate(
            first_topic_id=Subquery(
                TaskGroup.objects.filter(group=OuterRef('pk')).values(
                    'task__topic',
                )[:1]
            ),
            first_subtopic_id=Subquery(
                TaskGroup.objects.filter(group=OuterRef('pk')).values(
                    'task__subtopic',
                )[:1]
            ),
            sample_task_text=Subquery(
                TaskGroup.objects.filter(group=OuterRef('pk')).values(
                    'task__text',
                )[:1]
            ),
        )

        if filters.search:
            queryset = queryset.filter(
                Q(name__icontains=filters.search)
                | Q(description__icontains=filters.search)
            )

        if filters.topic_id:
            task_ids = Task.objects.filter(
                topic_id=filters.topic_id,
            ).values_list('pk', flat=True)
            group_ids = TaskGroup.objects.filter(
                task_id__in=task_ids,
            ).values_list('group_id', flat=True).distinct()
            queryset = queryset.filter(pk__in=group_ids)

        if filters.subtopic_id:
            task_ids = Task.objects.filter(
                subtopic_id=filters.subtopic_id,
            ).values_list('pk', flat=True)
            group_ids = TaskGroup.objects.filter(
                task_id__in=task_ids,
            ).values_list('group_id', flat=True).distinct()
            queryset = queryset.filter(pk__in=group_ids)

        min_tasks = self._parse_int(filters.min_tasks)
        if min_tasks is not None:
            queryset = queryset.filter(task_count__gte=min_tasks)

        max_tasks = self._parse_int(filters.max_tasks)
        if max_tasks is not None:
            queryset = queryset.filter(task_count__lte=max_tasks)

        if filters.group_filter == 'empty':
            queryset = queryset.filter(task_count=0)
        elif filters.group_filter == 'nonempty':
            queryset = queryset.filter(task_count__gt=0)

        difficulty = self._parse_int(filters.difficulty)
        if difficulty is not None:
            task_ids = Task.objects.filter(
                difficulty=difficulty,
            ).values_list('pk', flat=True)
            group_ids = TaskGroup.objects.filter(
                task_id__in=task_ids,
            ).values_list('group_id', flat=True).distinct()
            queryset = queryset.filter(pk__in=group_ids)

        if filters.sort == 'tasks_desc':
            queryset = queryset.order_by('-task_count', 'name')
        elif filters.sort == 'tasks_asc':
            queryset = queryset.order_by('task_count', 'name')
        elif filters.sort == 'newest':
            queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('name')

        return tuple(
            TaskGroupListItem(
                pk=str(group.pk),
                name=group.name,
                description=group.description,
                task_count=group.task_count,
                avg_difficulty=group.avg_difficulty,
                sample_task_text=group.sample_task_text or '',
            )
            for group in queryset
        )

    def get_analog_group_detail(self, group_id: str):
        group = AnalogGroup.objects.filter(pk=group_id).first()
        if group is None:
            return None

        return TaskGroupDetailGroup(
            pk=str(group.pk),
            name=group.name,
            description=group.description,
        )

    def get_task_group_detail_tasks(self, group_id: str):
        memberships = TaskGroup.objects.filter(
            group_id=group_id,
        ).select_related(
            'task',
            'task__topic',
            'task__subtopic',
        ).prefetch_related('task__images')

        return tuple(
            TaskGroupDetailTask(
                pk=str(membership.task.pk),
                topic=str(membership.task.topic),
                text=membership.task.text,
                task_type_display=membership.task.get_task_type_display(),
                difficulty_display=membership.task.get_difficulty_display(),
                image_count=membership.task.images.count(),
                bank_role=membership.bank_role,
            )
            for membership in memberships
        )

    def get_available_tasks_for_analog_group(self, group_id: str, search: str):
        existing_task_ids = TaskGroup.objects.filter(
            group_id=group_id,
        ).values_list('task_id', flat=True)
        tasks = Task.objects.exclude(id__in=existing_task_ids).select_related(
            'topic',
            'subtopic',
        ).annotate(
            image_count=Count('images', distinct=True),
        ).order_by('-created_at')

        if search:
            tasks = tasks.filter(
                Q(text__icontains=search)
                | Q(topic__name__icontains=search)
            )

        return tuple(
            AddTasksToGroupTask(
                pk=str(task.pk),
                topic=str(task.topic),
                text=task.text,
                task_type_display=task.get_task_type_display(),
                difficulty_display=task.get_difficulty_display(),
                section=task.topic.section or '',
                created_at=task.created_at,
                image_count=task.image_count,
            )
            for task in tasks
        )

    def get_list_analog_groups(self):
        return tuple(
            SelectOption(id=str(group.pk), name=group.name)
            for group in AnalogGroup.objects.all().order_by('name')
        )

    def count_analog_groups(self) -> int:
        return AnalogGroup.objects.count()

    def count_empty_analog_groups(self) -> int:
        return AnalogGroup.objects.annotate(
            task_count=Count('taskgroup'),
        ).filter(task_count=0).count()

    def count_task_group_memberships(self) -> int:
        return TaskGroup.objects.count()
