"""Django implementation of the task repository."""

import base64
from typing import List, Set

from django.db.models import Count, Exists, OuterRef, Q

from core_logic.entities.task import (
    ReferenceElementOption,
    SelectOption,
    TaskEntity,
    TaskExportFilters,
    TaskExportGroupRef,
    TaskExportImageSource,
    TaskExportSourceRef,
    TaskExportTaskSource,
    TaskExportTopicRef,
    TaskDetailGroup,
    TaskDetailImage,
    TaskDetailSource,
    TaskDetailTask,
    TaskImageSaveParams,
    TaskImagesSaveResult,
    TaskListFilters,
    TaskListItem,
    TaskListSourceRef,
    TaskListSubtopicRef,
    TaskSaveParams,
    TaskSaveResult,
)
from core_logic.interfaces.task_repo import ITaskRepository
from core_logic.interfaces.task_math_status_cache import ITaskMathStatusCache
from core_logic.services.reference_catalog import merge_reference_choices
from curriculum.models import SubTopic, Topic
from infrastructure.services.task_image_presentation import (
    TaskImagePresentationService,
)
from infrastructure.services.task_math_status_cache import (
    task_math_status_cache,
)
from task_groups.models import AnalogGroup, TaskGroup
from references.models import SubjectReference
from tasks.models import Source, Task, TaskImage


class DjangoTaskRepository(ITaskRepository):
    def __init__(
        self,
        math_status_cache: ITaskMathStatusCache = task_math_status_cache,
    ):
        self.math_status_cache = math_status_cache

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
                id__in=self.math_status_cache.get_tasks_with_math_ids(),
            )
        elif filters.math_filter == 'with_errors':
            queryset = queryset.filter(
                id__in=self.math_status_cache.get_tasks_with_errors_ids(),
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
            section=task.topic.section or '',
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
                    safe_url=TaskImagePresentationService.safe_url(
                        image.image,
                    ),
                    image_name=image.image.name if image.image else '',
                    css_class=TaskImagePresentationService.css_class(
                        image.position,
                    ),
                )
                for image in task.images.all()
            ],
            created_at=task.created_at,
        )

    def create_task(self, params: TaskSaveParams) -> TaskSaveResult:
        task = Task.objects.create(**self._task_values(params))
        return TaskSaveResult(status='created', task_id=str(task.pk))

    def update_task(self, params: TaskSaveParams) -> TaskSaveResult:
        task = Task.objects.filter(pk=params.task_id).first()
        if task is None:
            return TaskSaveResult(status='not_found')

        for field, value in self._task_values(params).items():
            setattr(task, field, value)
        task.save()
        return TaskSaveResult(status='updated', task_id=str(task.pk))

    def get_subtopic_topic_id(self, subtopic_id: str):
        topic_id = SubTopic.objects.filter(pk=subtopic_id).values_list(
            'topic_id',
            flat=True,
        ).first()
        return str(topic_id) if topic_id else None

    def save_task_images(
        self,
        task_id: str,
        images: List[TaskImageSaveParams],
    ) -> TaskImagesSaveResult:
        if not Task.objects.filter(pk=task_id).exists():
            return TaskImagesSaveResult(status='not_found')

        created_images = 0
        deleted_images = 0
        for image_params in images:
            if image_params.image_id:
                task_image = TaskImage.objects.filter(
                    pk=image_params.image_id,
                    task_id=task_id,
                ).first()
                if task_image is None:
                    continue
                if image_params.delete:
                    task_image.delete()
                    deleted_images += 1
                    continue

                if image_params.image:
                    task_image.image = image_params.image
                task_image.position = image_params.position
                task_image.caption = image_params.caption
                task_image.order = image_params.order
                task_image.save()
                continue

            if image_params.delete or not image_params.image:
                continue
            TaskImage.objects.create(
                task_id=task_id,
                image=image_params.image,
                position=image_params.position,
                caption=image_params.caption,
                order=image_params.order,
            )
            created_images += 1

        return TaskImagesSaveResult(
            status='saved',
            created_images=created_images,
            deleted_images=deleted_images,
        )

    def _task_values(self, params: TaskSaveParams):
        return {
            'text': params.text,
            'answer': params.answer,
            'topic_id': params.topic_id,
            'subtopic_id': params.subtopic_id,
            'task_type': params.task_type,
            'difficulty': params.difficulty,
            'cognitive_level': params.cognitive_level,
            'content_element': params.content_element,
            'requirement_element': params.requirement_element,
            'short_solution': params.short_solution,
            'full_solution': params.full_solution,
            'hint': params.hint,
            'instruction': params.instruction,
            'estimated_time': params.estimated_time,
            'source_id': params.source_id,
            'source_detail': params.source_detail,
            'grade': params.grade,
            'year': params.year,
            'is_verified': params.is_verified,
            'teacher_notes': params.teacher_notes,
        }

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
        return [
            SelectOption(id=str(topic.pk), name=topic.name)
            for topic in Topic.objects.all().order_by('section', 'name')
        ]

    def get_list_sources(self):
        return [
            SelectOption(id=str(source.pk), name=str(source))
            for source in Source.objects.all().order_by('name')
        ]

    def get_task_export_sources(
        self,
        filters: TaskExportFilters,
    ):
        return [
            self._task_export_source(task)
            for task in self._get_export_tasks(filters)
        ]

    def get_subtopics_for_topic(self, topic_id: str):
        if not topic_id:
            return []

        return [
            SelectOption(id=str(subtopic.pk), name=subtopic.name)
            for subtopic in SubTopic.objects.filter(
                topic_id=topic_id,
            ).order_by('order', 'name')
        ]

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
        catalogs = (
            reference.get_choices()
            for reference in SubjectReference.objects.filter(
                subject=subject,
                category=category,
                is_active=True,
            ).order_by('grade_level', 'created_at')
        )
        return [
            ReferenceElementOption(code=code, name=name)
            for code, name in merge_reference_choices(catalogs)
        ]

    def get_task_type_choices(self):
        return list(Task.TASK_TYPES)

    def count_tasks(self) -> int:
        return Task.objects.count()

    def count_ungrouped_tasks(self) -> int:
        return Task.objects.filter(
            ~Exists(TaskGroup.objects.filter(task=OuterRef('pk')))
        ).count()

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

    def get_first_task_difficulty_for_group(self, group_id: str) -> int:
        task_group = TaskGroup.objects.filter(
            group_id=group_id,
        ).select_related('task').first()
        if task_group and task_group.task.difficulty:
            return task_group.task.difficulty
        return 1

    def delete_task(self, task_id: str) -> int:
        tasks = Task.objects.filter(pk=task_id)
        deleted_count = tasks.count()
        tasks.delete()
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
        if filters.limit:
            tasks = tasks[:filters.limit]

        return tasks

    def _task_export_source(self, task):
        return TaskExportTaskSource(
            pk=str(task.pk),
            text=task.text,
            answer=task.answer or '',
            short_solution=task.short_solution or '',
            full_solution=task.full_solution or '',
            hint=task.hint or '',
            instruction=task.instruction or '',
            difficulty=task.difficulty,
            task_type=task.task_type,
            cognitive_level=getattr(task, 'cognitive_level', ''),
            content_element=getattr(task, 'content_element', ''),
            requirement_element=getattr(task, 'requirement_element', ''),
            estimated_time=getattr(task, 'estimated_time', None),
            grade=task.grade,
            year=task.year,
            is_verified=task.is_verified,
            teacher_notes=task.teacher_notes or '',
            source_detail=task.source_detail or '',
            topic=(
                TaskExportTopicRef(
                    name=task.topic.name,
                    subject=task.topic.subject,
                    grade_level=task.topic.grade_level,
                    section=getattr(task.topic, 'section', ''),
                    description=getattr(task.topic, 'description', ''),
                )
                if task.topic
                else None
            ),
            source=(
                TaskExportSourceRef(
                    pk=str(task.source.pk),
                    name=task.source.name,
                    short_name=task.source.short_name or '',
                    source_type=task.source.source_type,
                    author=task.source.author or '',
                    year=task.source.year,
                    url=task.source.url or '',
                    isbn=task.source.isbn or '',
                )
                if task.source
                else None
            ),
            groups=tuple(
                TaskExportGroupRef(
                    pk=str(membership.group.pk),
                    name=membership.group.name,
                    description=getattr(membership.group, 'description', ''),
                    difficulty=membership.group.difficulty,
                    bank_role=membership.bank_role,
                )
                for membership in task.taskgroup_set.all()
            ),
            images=self._task_export_images(task),
        )

    @staticmethod
    def _task_export_images(task):
        result = []
        for image in task.images.all():
            if not TaskImagePresentationService.has_file(image.image):
                continue
            try:
                with image.image.open('rb') as image_file:
                    base64_data = base64.b64encode(image_file.read()).decode('ascii')
            except Exception:
                continue
            result.append(TaskExportImageSource(
                pk=str(image.pk),
                task_id=str(task.pk),
                filename=image.image.name.split('/')[-1],
                position=image.position or '',
                caption=image.caption or '',
                order=image.order,
                base64_data=base64_data,
            ))
        return tuple(result)
