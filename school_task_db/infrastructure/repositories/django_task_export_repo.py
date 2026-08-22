"""Django task export source adapter."""

from core_logic.entities.task import (
    TaskExportFilters,
    TaskExportClassificationRef,
    TaskExportGroupRef,
    TaskExportImageSource,
    TaskExportSourceRef,
    TaskExportSubtopicRef,
    TaskExportTaskSource,
    TaskExportTopicRef,
)
from core_logic.interfaces.task_export_repo import ITaskExportRepository
from core_logic.services.task_image_transfer_codec import (
    TaskImageTransferCodec,
)
from infrastructure.services.task_image_presentation import (
    TaskImagePresentationService,
)
from tasks.models import Task


class DjangoTaskExportRepository(ITaskExportRepository):
    def __init__(self, transfer_codec=None):
        self.transfer_codec = transfer_codec or TaskImageTransferCodec()

    def get_task_export_sources(self, filters: TaskExportFilters):
        return tuple(
            self._task_export_source(task)
            for task in self._get_export_tasks(filters)
        )

    @staticmethod
    def _get_export_tasks(filters: TaskExportFilters):
        tasks = Task.objects.select_related(
            'topic',
            'subtopic',
            'source',
        ).prefetch_related(
            'images__asset',
            'taskgroup_set__group',
            'codifier_content_entries__codifier',
            'codifier_requirements__codifier',
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
            estimated_time=getattr(task, 'estimated_time', None),
            grade=task.grade,
            year=task.year,
            is_verified=task.is_verified,
            teacher_notes=task.teacher_notes or '',
            source_detail=task.source_detail or '',
            topic=(
                TaskExportTopicRef(
                    pk=str(task.topic.pk),
                    name=task.topic.name,
                    subject=task.topic.subject,
                    grade_level=task.topic.grade_level,
                    section=getattr(task.topic, 'section', ''),
                    description=getattr(task.topic, 'description', ''),
                )
                if task.topic
                else None
            ),
            subtopic=(
                TaskExportSubtopicRef(
                    pk=str(task.subtopic.pk),
                    name=task.subtopic.name,
                    description=task.subtopic.description or '',
                    order=task.subtopic.order,
                )
                if task.subtopic
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
            content_entries=tuple(
                self._classification_ref(entry)
                for entry in task.codifier_content_entries.all()
            ),
            requirements=tuple(
                self._classification_ref(requirement)
                for requirement in task.codifier_requirements.all()
            ),
        )

    @staticmethod
    def _classification_ref(item):
        return TaskExportClassificationRef(
            subject=item.codifier.subject,
            exam_type=item.codifier.exam_type,
            year=item.codifier.year,
            code=item.code,
            name=item.name,
            codifier_name=item.codifier.short_name,
        )

    def _task_export_images(self, task):
        result = []
        for image in task.images.all():
            image_file = image.image
            if not TaskImagePresentationService.has_file(image_file):
                continue
            try:
                with image_file.open('rb') as opened_file:
                    encoded = self.transfer_codec.encode(opened_file.read())
            except Exception:
                continue
            result.append(TaskExportImageSource(
                pk=str(image.pk),
                task_id=str(task.pk),
                filename=(
                    image.asset.original_filename
                    if image.asset_id
                    else image_file.name.split('/')[-1]
                ),
                position=image.position or '',
                caption=image.caption or '',
                order=image.order,
                base64_data=encoded,
            ))
        return tuple(result)
