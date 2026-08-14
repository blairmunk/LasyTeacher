"""Django read adapter for variant list and detail screens."""

from django.core.files.storage import default_storage
from django.db.models import Count, Sum

from core_logic.entities.work import (
    VariantDetailImage,
    VariantDetailRef,
    VariantDetailStudentRef,
    VariantDetailTask,
    VariantDetailTaskRow,
    VariantDetailVariant,
    VariantListItem,
    VariantListStudentRef,
    VariantListWorkRef,
)
from core_logic.interfaces.variant_read_repo import IVariantReadRepository
from core_logic.value_objects.variant_display import (
    resolve_variant_display_name,
)
from core_logic.value_objects.task_content_snapshot import (
    task_content_snapshot_from_mapping,
)
from infrastructure.services.task_image_presentation import (
    TaskImagePresentationService,
)
from works.models import Variant, VariantTask


def _variant_display_name(variant):
    return resolve_variant_display_name(
        work_name=variant.work.name if variant.work else '',
        work_name_snapshot=variant.work_name_snapshot,
        variant_type=variant.variant_type,
        assigned_student_name=(
            variant.assigned_student.get_short_name()
            if variant.assigned_student
            else ''
        ),
    )


class DjangoVariantReadRepository(IVariantReadRepository):
    def get_list_variants(self):
        return tuple(
            VariantListItem(
                pk=str(variant.pk),
                number=variant.number,
                created_at=variant.created_at,
                task_count=variant.task_count,
                display_name=_variant_display_name(variant),
                variant_type=variant.variant_type,
                variant_type_display=variant.get_variant_type_display(),
                work=(
                    VariantListWorkRef(
                        pk=str(variant.work.pk),
                        name=variant.work.name,
                        duration=variant.work.duration,
                    )
                    if variant.work
                    else None
                ),
                assigned_student=(
                    VariantListStudentRef(
                        pk=str(variant.assigned_student.pk),
                        short_name=variant.assigned_student.get_short_name(),
                    )
                    if variant.assigned_student
                    else None
                ),
                has_source_work=bool(variant.source_work_id),
            )
            for variant in Variant.objects.select_related(
                'work',
                'assigned_student',
            ).annotate(
                task_count=Count('varianttask'),
            ).order_by('-created_at')
        )

    def get_variant_detail(self, variant_id: str):
        variant = Variant.objects.select_related(
            'work',
            'assigned_student',
            'source_work',
            'source_participation__student',
        ).filter(pk=variant_id).first()
        if variant is None:
            return None
        personal_student = variant.assigned_student
        if personal_student is None and variant.source_participation:
            personal_student = variant.source_participation.student

        return VariantDetailVariant(
            pk=str(variant.pk),
            number=variant.number,
            display_name=_variant_display_name(variant),
            short_uuid=variant.get_short_uuid(),
            medium_uuid=variant.get_medium_uuid(),
            variant_type=variant.variant_type,
            variant_type_display=variant.get_variant_type_display(),
            display_duration=variant.duration_snapshot,
            display_max_score=variant.max_score_snapshot,
            created_at=variant.created_at,
            work=(
                VariantDetailRef(
                    pk=str(variant.work.pk),
                    name=variant.work.name,
                    short_uuid=variant.work.get_short_uuid(),
                )
                if variant.work
                else None
            ),
            assigned_student=(
                VariantDetailStudentRef(
                    pk=str(personal_student.pk),
                    full_name=personal_student.get_full_name(),
                    short_name=personal_student.get_short_name(),
                )
                if personal_student
                else None
            ),
            source_work=(
                VariantDetailRef(
                    pk=str(variant.source_work.pk),
                    name=variant.source_work.name,
                    short_uuid=variant.source_work.get_short_uuid(),
                )
                if variant.source_work
                else None
            ),
        )

    def get_variant_detail_tasks(self, variant_id: str):
        variant_tasks = VariantTask.objects.filter(
            variant_id=variant_id,
        ).order_by('order')

        result = []
        for variant_task in variant_tasks:
            task = task_content_snapshot_from_mapping(
                variant_task.task_snapshot,
            )
            result.append(VariantDetailTaskRow(
                task=VariantDetailTask(
                    pk=task.task_id,
                    id=task.task_id,
                    topic=task.topic_name,
                    text=task.text,
                    answer=task.answer,
                    task_type_display=task.task_type_display,
                    difficulty=task.difficulty,
                    short_uuid=task.task_id[-4:].upper(),
                    images=tuple(
                        VariantDetailImage(
                            caption=image.caption,
                            position=image.position,
                            safe_url=self._snapshot_image_url(
                                image.file_name,
                            ),
                            css_class=TaskImagePresentationService.css_class(
                                image.position,
                            ),
                        )
                        for image in task.images
                    ),
                ),
                order=variant_task.order,
                max_points=variant_task.max_points,
                bank_role=variant_task.bank_role,
                render_mode=variant_task.render_mode,
                is_assessable=variant_task.is_assessable,
                blank_cells_after=variant_task.blank_cells_after,
                blank_cells_rows=variant_task.blank_cells_rows,
            ))
        return tuple(result)

    def get_variant_total_max_points(self, variant_id: str) -> int:
        aggregate = VariantTask.objects.filter(
            variant_id=variant_id,
        ).aggregate(total=Sum('max_points'))
        return aggregate['total'] or 0

    @staticmethod
    def _snapshot_image_url(file_name):
        if not file_name:
            return None
        try:
            return default_storage.url(file_name)
        except ValueError:
            return None
