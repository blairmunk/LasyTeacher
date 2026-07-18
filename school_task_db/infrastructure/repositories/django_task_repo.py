"""Django implementation of the task repository."""

import base64
from typing import List, Set

from django.db.models import Avg, Count, Exists, OuterRef, Q, Subquery

from core_logic.entities.task import (
    AddTasksToGroupTask,
    ReferenceElementOption,
    SelectOption,
    SourceListItem,
    TaskEntity,
    TaskExportFilters,
    TaskGroupDetailGroup,
    TaskGroupDetailTask,
    TaskGroupListItem,
    TaskGroupListFilters,
    TaskDetailGroup,
    TaskDetailImage,
    TaskDetailSource,
    TaskDetailTask,
    TaskListFilters,
    TaskListItem,
    TaskListSourceRef,
    TaskListSubtopicRef,
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
        queryset = Task.objects.select_related(
            'topic',
            'subtopic',
            'source',
        ).order_by('-created_at')
        queryset = queryset.annotate(
            group_count=Count('taskgroup', distinct=True),
            image_count=Count('images', distinct=True),
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

        return [
            TaskListItem(
                pk=str(task.pk),
                text=task.text,
                topic_name=task.topic.name,
                task_type_display=task.get_task_type_display(),
                difficulty_display=task.get_difficulty_display(),
                display_id=task.get_display_id(),
                created_at=task.created_at,
                subtopic=(
                    TaskListSubtopicRef(
                        pk=str(task.subtopic.pk),
                        name=task.subtopic.name,
                    )
                    if task.subtopic
                    else None
                ),
                source=(
                    TaskListSourceRef(
                        pk=str(task.source.pk),
                        name=task.source.name,
                        short_name=task.source.short_name,
                    )
                    if task.source
                    else None
                ),
                grade=task.grade,
                is_verified=task.is_verified,
                has_group=task.has_group,
                group_count=task.group_count,
                image_count=task.image_count,
            )
            for task in queryset
        ]

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
        sample_task_text = Subquery(
            TaskGroup.objects.filter(
                group=OuterRef('pk'),
            ).select_related('task').values('task__text')[:1]
        )
        queryset = queryset.annotate(
            first_topic_id=first_task_topic,
            first_subtopic_id=first_task_subtopic,
            sample_task_text=sample_task_text,
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
        task_groups = TaskGroup.objects.filter(
            group_id=group_id,
        ).select_related(
            'task',
            'task__topic',
            'task__subtopic',
        ).prefetch_related(
            'task__images',
        )

        return [
            TaskGroupDetailTask(
                pk=str(task_group.task.pk),
                topic=str(task_group.task.topic),
                text=task_group.task.text,
                task_type_display=task_group.task.get_task_type_display(),
                difficulty_display=task_group.task.get_difficulty_display(),
                image_count=task_group.task.images.count(),
            )
            for task_group in task_groups
        ]

    def get_analog_group(self, group_id: str):
        return AnalogGroup.objects.filter(pk=group_id).first()

    def get_available_tasks_for_analog_group(self, group_id: str, search: str):
        existing_task_ids = TaskGroup.objects.filter(
            group_id=group_id,
        ).values_list(
            'task_id',
            flat=True,
        )
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
                section=task.section or '',
                created_at=task.created_at,
                image_count=task.image_count,
            )
            for task in tasks
        ]

    def get_task(self, task_id: str):
        task = Task.objects.select_related(
            'topic',
            'subtopic',
            'source',
        ).prefetch_related('images').filter(pk=task_id).first()
        if task is None:
            return None

        source = None
        if task.source:
            source = TaskDetailSource(
                name=str(task.source),
                url=task.source.url,
            )

        return TaskDetailTask(
            pk=str(task.pk),
            topic=str(task.topic),
            section=task.section or '',
            text=task.text,
            answer=task.answer,
            task_type_display=task.get_task_type_display(),
            difficulty_display=task.get_difficulty_display(),
            short_uuid=task.get_short_uuid(),
            subtopic=str(task.subtopic) if task.subtopic else '',
            short_solution=task.short_solution,
            full_solution=task.full_solution,
            hint=task.hint,
            instruction=task.instruction,
            source=source,
            source_detail=task.source_detail,
            grade=task.grade,
            year=task.year,
            is_verified=task.is_verified,
            estimated_time=task.estimated_time,
            teacher_notes=task.teacher_notes,
            images=[
                TaskDetailImage(
                    caption=image.caption,
                    position=image.position,
                    safe_url=image.safe_url,
                    image_name=image.image.name if image.image else '',
                    css_class=image.get_css_class(),
                )
                for image in task.images.all()
            ],
            created_at=task.created_at,
        )

    def get_task_detail_groups(self, task_id: str):
        task_groups = TaskGroup.objects.filter(
            task_id=task_id,
        ).select_related('group')
        return [
            TaskDetailGroup(
                pk=str(task_group.group.pk),
                name=task_group.group.name,
            )
            for task_group in task_groups
        ]

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

    def build_task_export_payload(
        self,
        filters: TaskExportFilters,
        export_date: str,
    ) -> dict:
        tasks = list(self._get_export_tasks(filters))
        all_groups = {}
        all_topics = {}
        all_sources = {}
        tasks_data = []
        images_data = []

        for task in tasks:
            task_dict = self._build_export_task_dict(task)
            self._add_export_topic(task, all_topics, task_dict)
            self._add_export_source(task, all_sources, task_dict)
            self._add_export_groups(task, all_groups, task_dict)
            self._add_export_images(task, images_data)
            tasks_data.append(task_dict)

        return {
            'version': '1.1',
            'export_date': export_date,
            'analog_groups': list(all_groups.values()),
            'topics': list(all_topics.values()),
            'sources': list(all_sources.values()),
            'tasks': tasks_data,
            'task_images': images_data,
        }

    def get_source_list_sources(self):
        return [
            SourceListItem(
                pk=str(source.pk),
                name=source.name,
                short_name=source.short_name,
                source_type_display=source.get_source_type_display(),
                author=source.author,
                year=source.year,
                url=source.url,
                task_count=source.task_count,
            )
            for source in Source.objects.annotate(
                task_count=Count('task'),
            ).order_by('name')
        ]

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

    def update_analog_group(
        self,
        group_id: str,
        name: str,
        description: str = '',
    ) -> bool:
        updated_count = AnalogGroup.objects.filter(pk=group_id).update(
            name=name,
            description=description,
        )
        return updated_count > 0

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

    def _get_export_tasks(self, filters: TaskExportFilters):
        tasks = Task.objects.select_related(
            'topic',
            'subtopic',
            'source',
        ).prefetch_related(
            'images',
            'taskgroup_set__group',
        )

        if filters.topic_id:
            tasks = tasks.filter(topic_id=filters.topic_id)
        if filters.subject:
            tasks = tasks.filter(topic__subject=filters.subject)
        if filters.grade:
            tasks = tasks.filter(topic__grade_level=filters.grade)

        return tasks

    def _build_export_task_dict(self, task):
        return {
            'id': str(task.id),
            'text': task.text,
            'answer': task.answer or '',
            'short_solution': task.short_solution or '',
            'full_solution': task.full_solution or '',
            'hint': task.hint or '',
            'instruction': task.instruction or '',
            'difficulty': task.difficulty,
            'task_type': task.task_type,
            'cognitive_level': getattr(task, 'cognitive_level', ''),
            'content_element': getattr(task, 'content_element', ''),
            'requirement_element': getattr(task, 'requirement_element', ''),
            'estimated_time': getattr(task, 'estimated_time', None),
            'grade': task.grade,
            'year': task.year,
            'is_verified': task.is_verified,
            'teacher_notes': task.teacher_notes or '',
            'source_detail': task.source_detail or '',
            'source': None,
            'groups': [],
        }

    def _add_export_topic(self, task, all_topics, task_dict):
        if not task.topic:
            return

        task_dict['topic'] = {
            'name': task.topic.name,
            'subject': task.topic.subject,
            'grade_level': task.topic.grade_level,
            'section': getattr(task.topic, 'section', ''),
        }
        topic_key = f'{task.topic.subject}_{task.topic.grade_level}_{task.topic.name}'
        if topic_key not in all_topics:
            all_topics[topic_key] = {
                'name': task.topic.name,
                'subject': task.topic.subject,
                'grade_level': task.topic.grade_level,
                'section': getattr(task.topic, 'section', ''),
                'description': getattr(task.topic, 'description', ''),
            }

    def _add_export_source(self, task, all_sources, task_dict):
        if not task.source:
            return

        task_dict['source'] = {
            'name': task.source.name,
            'short_name': task.source.short_name or '',
            'source_type': task.source.source_type,
            'author': task.source.author or '',
            'year': task.source.year,
        }

        source_id = str(task.source.id)
        if source_id not in all_sources:
            all_sources[source_id] = {
                'id': source_id,
                'name': task.source.name,
                'short_name': task.source.short_name or '',
                'source_type': task.source.source_type,
                'author': task.source.author or '',
                'year': task.source.year,
                'url': task.source.url or '',
                'isbn': task.source.isbn or '',
            }

    def _add_export_groups(self, task, all_groups, task_dict):
        for task_group in task.taskgroup_set.all():
            group = task_group.group
            group_id = str(group.id)
            task_dict['groups'].append(group_id)

            if group_id not in all_groups:
                all_groups[group_id] = {
                    'id': group_id,
                    'name': group.name,
                    'description': getattr(group, 'description', ''),
                }

    def _add_export_images(self, task, images_data):
        for image in task.images.all():
            if not image.has_file:
                continue
            try:
                with image.image.open('rb') as image_file:
                    base64_data = base64.b64encode(image_file.read()).decode('ascii')
            except Exception:
                continue

            images_data.append({
                'id': str(image.id),
                'task_id': str(task.id),
                'filename': image.image.name.split('/')[-1],
                'position': image.position or '',
                'caption': image.caption or '',
                'order': image.order,
                'base64_data': base64_data,
            })
