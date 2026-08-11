"""Django read adapter for global application search."""

from django.db.models import Count, Q, Sum

from core_logic.entities.core import (
    SearchGroupResult,
    SearchTaskResult,
    SearchVariantResult,
    SearchWorkResult,
)
from core_logic.interfaces.global_search_repo import IGlobalSearchRepository
from core_logic.value_objects.variant_display import (
    resolve_variant_display_name,
)
from task_groups.models import AnalogGroup
from tasks.models import Task
from works.models import Variant, Work


class DjangoGlobalSearchRepository(IGlobalSearchRepository):
    def search_by_uuid(self, query: str):
        return {
            'tasks': self._task_results(
                self._search_model_by_uuid(
                    Task,
                    query,
                    related_uuid_fields=['topic', 'subtopic'],
                )
            ),
            'works': self._work_results(self._search_model_by_uuid(Work, query)),
            'variants': self._variant_results(
                self._search_model_by_uuid(
                    Variant,
                    query,
                    related_uuid_fields=['work'],
                )
            ),
            'groups': self._group_results(
                self._search_model_by_uuid(AnalogGroup, query),
            ),
        }

    def search_by_text(self, words):
        return {
            'tasks': self._task_results(self._search_tasks_by_text(words)),
            'works': self._work_results(self._search_works_by_text(words)),
            'variants': self._variant_results(self._search_variants_by_text(words)),
            'groups': self._group_results(self._search_groups_by_text(words)),
        }

    @staticmethod
    def _search_model_by_uuid(model_class, query, related_uuid_fields=None):
        clean = query.replace('#', '').replace('-', '').replace(' ', '').strip().lower()
        if len(clean) < 3:
            return model_class.objects.none()

        matching_ids = set()
        for obj_id in model_class.objects.values_list('id', flat=True).iterator():
            id_clean = str(obj_id).replace('-', '').lower()
            if clean in id_clean:
                matching_ids.add(obj_id)

        if related_uuid_fields:
            for field in related_uuid_fields:
                fk_field = f'{field}_id'
                try:
                    for obj_id, fk_id in model_class.objects.values_list(
                        'id',
                        fk_field,
                    ).iterator():
                        if fk_id:
                            fk_clean = str(fk_id).replace('-', '').lower()
                            if clean in fk_clean:
                                matching_ids.add(obj_id)
                except Exception:
                    pass

        if not matching_ids:
            return model_class.objects.none()
        return model_class.objects.filter(id__in=matching_ids)

    @staticmethod
    def _search_tasks_by_text(words):
        task_q = Q()
        for word in words:
            word_q = (
                Q(text__icontains=word)
                | Q(answer__icontains=word)
                | Q(topic__name__icontains=word)
                | Q(subtopic__name__icontains=word)
            )
            task_q &= word_q

        try:
            return Task.objects.filter(task_q).distinct().select_related(
                'topic',
                'subtopic',
            )[:30]
        except Exception:
            task_q_fb = Q()
            for word in words:
                task_q_fb &= (
                    Q(text__icontains=word)
                    | Q(answer__icontains=word)
                )
            return Task.objects.filter(task_q_fb).distinct()[:30]

    @staticmethod
    def _search_works_by_text(words):
        work_q = Q()
        for word in words:
            work_q &= Q(name__icontains=word)
        return Work.objects.filter(work_q)[:20]

    @staticmethod
    def _search_variants_by_text(words):
        variant_q = Q()
        number_search = None
        text_words = []
        for word in words:
            if word.isdigit():
                number_search = int(word)
            else:
                text_words.append(word)

        if text_words:
            for word in text_words:
                variant_q &= Q(work_name_snapshot__icontains=word)
            if number_search:
                variant_q &= Q(number=number_search)
            return Variant.objects.filter(variant_q).select_related(
                'work',
                'assigned_student',
            )[:20]
        if number_search:
            return Variant.objects.filter(
                number=number_search,
            ).select_related(
                'work',
                'assigned_student',
            )[:20]
        return Variant.objects.none()

    @staticmethod
    def _search_groups_by_text(words):
        group_q = Q()
        for word in words:
            group_q &= Q(name__icontains=word)
        return AnalogGroup.objects.filter(group_q)[:20]

    @staticmethod
    def _task_results(tasks):
        return [
            SearchTaskResult(
                pk=str(task.pk),
                topic=str(task.topic),
                text=task.text,
                short_uuid=task.get_short_uuid(),
            )
            for task in tasks
        ]

    @staticmethod
    def _work_results(works):
        return [
            SearchWorkResult(
                pk=str(work.pk),
                name=work.name,
                work_type_display=work.get_work_type_display(),
                duration=work.duration,
                short_uuid=work.get_short_uuid(),
            )
            for work in works
        ]

    @staticmethod
    def _variant_results(variants):
        variants = variants.select_related(
            'work',
            'assigned_student',
        ).annotate(
            task_count_value=Count('varianttask'),
            total_max_points_value=Sum('varianttask__max_points'),
        )
        return [
            SearchVariantResult(
                pk=str(variant.pk),
                display_name=resolve_variant_display_name(
                    work_name=(variant.work.name if variant.work else ''),
                    work_name_snapshot=variant.work_name_snapshot,
                    variant_type=variant.variant_type,
                    assigned_student_name=(
                        variant.assigned_student.get_short_name()
                        if variant.assigned_student
                        else ''
                    ),
                ),
                number=variant.number,
                task_count=variant.task_count_value,
                total_max_points=variant.total_max_points_value or 0,
                short_uuid=variant.get_short_uuid(),
                has_work=variant.work_id is not None,
            )
            for variant in variants
        ]

    @staticmethod
    def _group_results(groups):
        return [
            SearchGroupResult(
                pk=str(group.pk),
                name=group.name,
                task_count=group.taskgroup_set.count(),
                short_uuid=group.get_short_uuid(),
            )
            for group in groups
        ]
