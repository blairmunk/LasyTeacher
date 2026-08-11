"""Django implementation of the task repository."""

from typing import List

from django.db.models import Count, Exists, OuterRef, Q

from core_logic.entities.task import (
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
from core_logic.interfaces.task_read_repo import ITaskReadRepository
from core_logic.interfaces.task_write_repo import ITaskWriteRepository
from core_logic.interfaces.task_math_status_cache import ITaskMathStatusCache
from infrastructure.services.task_image_presentation import (
    TaskImagePresentationService,
)
from infrastructure.services.task_math_status_cache import (
    task_math_status_cache,
)
from task_groups.models import TaskGroup
from tasks.models import Task, TaskImage


class DjangoTaskRepository(ITaskReadRepository, ITaskWriteRepository):
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

    def count_tasks(self) -> int:
        return Task.objects.count()

    def count_ungrouped_tasks(self) -> int:
        return Task.objects.filter(
            ~Exists(TaskGroup.objects.filter(task=OuterRef('pk')))
        ).count()

    def delete_task(self, task_id: str) -> int:
        tasks = Task.objects.filter(pk=task_id)
        deleted_count = tasks.count()
        tasks.delete()
        return deleted_count
