"""Django implementation of the analog task group repository."""

from typing import List, Set

from django.db.models import Avg, Count, OuterRef, Q, Subquery

from core_logic.entities.task import (
    AddTasksToGroupTask,
    SelectOption,
    TaskGroupDetailGroup,
    TaskGroupDetailTask,
    TaskGroupListFilters,
    TaskGroupListItem,
)
from core_logic.interfaces.task_group_repo import ITaskGroupRepository
from core_logic.value_objects.task_print_settings import TASK_BANK_ROLE_CONTROL
from task_groups.models import AnalogGroup, TaskGroup
from tasks.models import Task


class DjangoTaskGroupRepository(ITaskGroupRepository):
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

        return [
            TaskGroupListItem(
                pk=str(group.pk),
                name=group.name,
                description=group.description,
                task_count=group.task_count,
                avg_difficulty=group.avg_difficulty,
                sample_task_text=group.sample_task_text or '',
            )
            for group in queryset
        ]

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

        return [
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
        ]

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

        return [
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
        ]

    def get_list_analog_groups(self):
        return [
            SelectOption(id=str(group.pk), name=group.name)
            for group in AnalogGroup.objects.all().order_by('name')
        ]

    def count_analog_groups(self) -> int:
        return AnalogGroup.objects.count()

    def count_empty_analog_groups(self) -> int:
        return AnalogGroup.objects.annotate(
            task_count=Count('taskgroup'),
        ).filter(task_count=0).count()

    def count_task_group_memberships(self) -> int:
        return TaskGroup.objects.count()

    def analog_group_name_exists(self, name: str) -> bool:
        return AnalogGroup.objects.filter(name=name).exists()

    def create_analog_group(self, name: str, description: str = '') -> str:
        group = AnalogGroup.objects.create(name=name, description=description)
        return str(group.pk)

    def update_analog_group(
        self,
        group_id: str,
        name: str,
        description: str = '',
    ) -> bool:
        return AnalogGroup.objects.filter(pk=group_id).update(
            name=name,
            description=description,
        ) > 0

    def get_analog_group_name(self, group_id: str):
        return AnalogGroup.objects.filter(pk=group_id).values_list(
            'name',
            flat=True,
        ).first()

    def add_tasks_to_group(
        self,
        group_id: str,
        task_ids: List[str],
        bank_role: str = TASK_BANK_ROLE_CONTROL,
    ) -> int:
        created_count = 0
        for task in Task.objects.filter(pk__in=task_ids):
            _, created = TaskGroup.objects.get_or_create(
                task=task,
                group_id=group_id,
                defaults={'bank_role': bank_role},
            )
            if created:
                created_count += 1
        return created_count

    def update_task_group_roles(self, group_id: str, task_roles: dict) -> int:
        updated_count = 0
        for task_id, bank_role in task_roles.items():
            updated_count += TaskGroup.objects.filter(
                group_id=group_id,
                task_id=task_id,
            ).update(bank_role=bank_role)
        return updated_count

    def remove_task_from_group(self, group_id: str, task_id: str) -> int:
        return TaskGroup.objects.filter(
            group_id=group_id,
            task_id=task_id,
        ).delete()[0]

    def remove_tasks_from_all_groups(self, task_ids: List[str]) -> int:
        if not task_ids:
            return 0
        return TaskGroup.objects.filter(task_id__in=task_ids).delete()[0]

    def delete_groups(self, group_ids: List[str]) -> int:
        if not group_ids:
            return 0

        groups = AnalogGroup.objects.filter(pk__in=group_ids)
        deleted_count = groups.count()
        groups.delete()
        return deleted_count

    def get_group_ids_for_tasks(self, task_ids: Set[str]) -> Set[str]:
        if not task_ids:
            return set()
        return {
            str(group_id)
            for group_id in TaskGroup.objects.filter(
                task_id__in=task_ids,
            ).values_list('group_id', flat=True)
        }

    def count_existing_group_ids(self, group_ids: Set[str]) -> int:
        if not group_ids:
            return 0
        return AnalogGroup.objects.filter(pk__in=group_ids).count()

    def get_first_task_difficulty_for_group(self, group_id: str) -> int:
        membership = TaskGroup.objects.filter(
            group_id=group_id,
        ).select_related('task').first()
        if membership and membership.task.difficulty:
            return membership.task.difficulty
        return 1

    def get_tasks_in_group(self, group_id: str) -> Set[str]:
        return {
            str(task_id)
            for task_id in TaskGroup.objects.filter(
                group_id=group_id,
            ).values_list('task_id', flat=True)
        }
