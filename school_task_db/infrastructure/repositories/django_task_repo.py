"""Django implementation of the task repository."""

from typing import List, Set

from django.db.models import Avg, Count, Exists, OuterRef, Q, Subquery

from core_logic.entities.task import (
    ReferenceElementOption,
    SelectOption,
    TaskEntity,
    TaskGroupListFilters,
    TaskListFilters,
)
from core_logic.interfaces.task_repo import ITaskRepository
from curriculum.models import SubTopic, Topic
from task_groups.models import AnalogGroup, TaskGroup
from tasks.models import Source, Task
from tasks.utils import math_status_cache


class DjangoTaskRepository(ITaskRepository):
    def _parse_int(self, value):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def get_list_tasks(self, filters: TaskListFilters):
        queryset = Task.objects.select_related('topic', 'subtopic').order_by(
            '-created_at',
        )
        queryset = queryset.annotate(
            group_count=Count('taskgroup'),
            has_group=Exists(TaskGroup.objects.filter(task=OuterRef('pk'))),
        )

        if filters.search:
            queryset = queryset.filter(
                Q(text__icontains=filters.search)
                | Q(answer__icontains=filters.search)
                | Q(topic__name__icontains=filters.search)
            )

        if filters.topic_id:
            queryset = queryset.filter(topic_id=filters.topic_id)
        if filters.subtopic_id:
            queryset = queryset.filter(subtopic_id=filters.subtopic_id)
        if filters.task_type:
            queryset = queryset.filter(task_type=filters.task_type)
        if filters.difficulty:
            try:
                queryset = queryset.filter(difficulty=int(filters.difficulty))
            except (ValueError, TypeError):
                pass

        if filters.group_filter == 'no_group':
            queryset = queryset.filter(has_group=False)
        elif filters.group_filter == 'has_group':
            queryset = queryset.filter(has_group=True)

        if filters.analog_group_id:
            queryset = queryset.filter(taskgroup__group_id=filters.analog_group_id)

        if filters.math_filter == 'with_math':
            queryset = queryset.filter(
                id__in=math_status_cache.get_tasks_with_math_ids(),
            )
        elif filters.math_filter == 'with_errors':
            queryset = queryset.filter(
                id__in=math_status_cache.get_tasks_with_errors_ids(),
            )

        if filters.source_id == 'none':
            queryset = queryset.filter(source__isnull=True)
        elif filters.source_id:
            queryset = queryset.filter(source_id=filters.source_id)

        if filters.grade == 'none':
            queryset = queryset.filter(grade__isnull=True)
        elif filters.grade:
            try:
                queryset = queryset.filter(grade=int(filters.grade))
            except (ValueError, TypeError):
                pass

        if filters.verified == '1':
            queryset = queryset.filter(is_verified=True)
        elif filters.verified == '0':
            queryset = queryset.filter(is_verified=False)

        return queryset

    def get_list_task_groups(self, filters: TaskGroupListFilters):
        queryset = AnalogGroup.objects.annotate(
            task_count=Count('taskgroup'),
            avg_difficulty=Avg('taskgroup__task__difficulty'),
        ).order_by('name')

        first_task_topic = Subquery(
            TaskGroup.objects.filter(
                group=OuterRef('pk'),
            ).select_related('task').values('task__topic')[:1]
        )
        first_task_subtopic = Subquery(
            TaskGroup.objects.filter(
                group=OuterRef('pk'),
            ).select_related('task').values('task__subtopic')[:1]
        )
        queryset = queryset.annotate(
            first_topic_id=first_task_topic,
            first_subtopic_id=first_task_subtopic,
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
            return queryset.order_by('-task_count', 'name')
        if filters.sort == 'tasks_asc':
            return queryset.order_by('task_count', 'name')
        if filters.sort == 'newest':
            return queryset.order_by('-created_at')
        return queryset.order_by('name')

    def get_detail_tasks(self):
        return Task.objects.select_related(
            'topic',
            'subtopic',
        ).prefetch_related('images')

    def get_task_detail_groups(self, task_id: str):
        return TaskGroup.objects.filter(
            task_id=task_id,
        ).select_related('group')

    def get_list_topics(self):
        return Topic.objects.all().order_by('section', 'name')

    def get_list_analog_groups(self):
        return AnalogGroup.objects.all().order_by('name')

    def count_analog_groups(self) -> int:
        return AnalogGroup.objects.count()

    def count_empty_analog_groups(self) -> int:
        return AnalogGroup.objects.annotate(
            task_count=Count('taskgroup'),
        ).filter(task_count=0).count()

    def count_task_group_memberships(self) -> int:
        return TaskGroup.objects.count()

    def get_list_sources(self):
        return Source.objects.all()

    def get_source_list_sources(self):
        return Source.objects.annotate(
            task_count=Count('task'),
        ).order_by('name')

    def get_subtopics_for_topic(self, topic_id: str):
        if not topic_id:
            return SubTopic.objects.none()

        return SubTopic.objects.filter(topic_id=topic_id).order_by('order', 'name')

    def get_subtopic_options(self, topic_id: str) -> List[SelectOption]:
        if not topic_id:
            return []

        try:
            topic = Topic.objects.get(pk=topic_id)
        except (Topic.DoesNotExist, ValueError):
            return []

        return [
            SelectOption(id=str(subtopic.id), name=subtopic.name)
            for subtopic in topic.subtopics.all().order_by('order', 'name')
        ]

    def get_reference_element_options(
        self,
        subject: str,
        category: str,
    ) -> List[ReferenceElementOption]:
        try:
            from references.helpers import get_subject_reference_choices
        except ImportError:
            return []

        return [
            ReferenceElementOption(code=code, name=name)
            for code, name in get_subject_reference_choices(subject, category)
        ]

    def get_task_type_choices(self):
        try:
            from references.helpers import get_task_type_choices

            return get_task_type_choices()
        except ImportError:
            return [
                ('computational', 'Расчётная задача'),
                ('qualitative', 'Качественная задача'),
                ('theoretical', 'Теоретический вопрос'),
                ('test', 'Тест'),
            ]

    def count_tasks(self) -> int:
        return Task.objects.count()

    def count_ungrouped_tasks(self) -> int:
        return Task.objects.filter(
            ~Exists(TaskGroup.objects.filter(task=OuterRef('pk')))
        ).count()

    def get_math_cache_stats(self):
        return math_status_cache.get_cache_stats()

    def refresh_math_cache(self) -> dict:
        return math_status_cache.refresh_cache()

    def get_by_ids(self, task_ids: Set[str]) -> List[TaskEntity]:
        if not task_ids:
            return []

        tasks = Task.objects.filter(id__in=task_ids)
        task_map = {
            str(task.id): TaskEntity(
                id=str(task.id),
                text=task.text,
                difficulty=task.difficulty or 1,
                estimated_time=task.estimated_time,
            )
            for task in tasks
        }
        return [task_map[task_id] for task_id in task_ids if task_id in task_map]

    def get_group_ids_for_tasks(self, task_ids: Set[str]) -> Set[str]:
        if not task_ids:
            return set()

        return {
            str(group_id)
            for group_id in TaskGroup.objects.filter(
                task_id__in=task_ids
            ).values_list('group_id', flat=True)
        }

    def count_existing_task_ids(self, task_ids: Set[str]) -> int:
        if not task_ids:
            return 0

        return Task.objects.filter(pk__in=task_ids).count()

    def count_existing_group_ids(self, group_ids: Set[str]) -> int:
        if not group_ids:
            return 0

        return AnalogGroup.objects.filter(pk__in=group_ids).count()

    def analog_group_name_exists(self, name: str) -> bool:
        return AnalogGroup.objects.filter(name=name).exists()

    def create_analog_group(self, name: str, description: str = '') -> str:
        group = AnalogGroup.objects.create(name=name, description=description)
        return str(group.pk)

    def get_first_task_difficulty_for_group(self, group_id: str) -> int:
        task_group = TaskGroup.objects.filter(
            group_id=group_id,
        ).select_related('task').first()
        if task_group and task_group.task.difficulty:
            return task_group.task.difficulty
        return 1

    def get_analog_group_name(self, group_id: str):
        return AnalogGroup.objects.filter(pk=group_id).values_list(
            'name',
            flat=True,
        ).first()

    def add_tasks_to_group(self, group_id: str, task_ids: List[str]) -> int:
        created_count = 0
        for task in Task.objects.filter(pk__in=task_ids):
            _, created = TaskGroup.objects.get_or_create(
                task=task,
                group_id=group_id,
            )
            if created:
                created_count += 1
        return created_count

    def remove_task_from_group(self, group_id: str, task_id: str) -> int:
        return TaskGroup.objects.filter(
            group_id=group_id,
            task_id=task_id,
        ).delete()[0]

    def remove_tasks_from_all_groups(self, task_ids: List[str]) -> int:
        if not task_ids:
            return 0

        return TaskGroup.objects.filter(task_id__in=task_ids).delete()[0]

    def delete_task(self, task_id: str) -> int:
        tasks = Task.objects.filter(pk=task_id)
        deleted_count = tasks.count()
        tasks.delete()
        return deleted_count

    def delete_groups(self, group_ids: List[str]) -> int:
        if not group_ids:
            return 0

        groups = AnalogGroup.objects.filter(pk__in=group_ids)
        deleted_count = groups.count()
        groups.delete()
        return deleted_count

    def get_tasks_in_group(self, group_id: str) -> Set[str]:
        return {
            str(task_id)
            for task_id in TaskGroup.objects.filter(
                group_id=group_id
            ).values_list('task_id', flat=True)
        }

    def get_tasks_by_difficulty(
        self,
        task_ids: Set[str],
        max_difficulty: int,
    ) -> List[TaskEntity]:
        if not task_ids:
            return []

        tasks = Task.objects.filter(
            id__in=task_ids,
            difficulty__lte=max_difficulty,
        ).order_by('difficulty', 'id')

        return [
            TaskEntity(
                id=str(task.id),
                text=task.text,
                difficulty=task.difficulty or 1,
                estimated_time=task.estimated_time,
            )
            for task in tasks
        ]
