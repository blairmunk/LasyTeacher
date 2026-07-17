"""Django implementation of the core repository."""

from django.db.models import Q

from core.models import ImportLog
from core_logic.interfaces.core_repo import ICoreRepository
from events.models import Event
from students.models import Student
from task_groups.models import AnalogGroup
from tasks.models import Task
from works.models import Variant, Work


class DjangoCoreRepository(ICoreRepository):
    def count_tasks(self) -> int:
        return Task.objects.count()

    def count_works(self) -> int:
        return Work.objects.count()

    def count_variants(self) -> int:
        return Variant.objects.count()

    def count_orphan_variants(self) -> int:
        return Variant.objects.filter(work__isnull=True).count()

    def count_students(self) -> int:
        return Student.objects.count()

    def count_events(self) -> int:
        return Event.objects.count()

    def count_analog_groups(self) -> int:
        return AnalogGroup.objects.count()

    def get_recent_import_logs(self, limit: int):
        return ImportLog.objects.all()[:limit]

    def get_import_logs(self):
        return ImportLog.objects.all()

    def search_by_uuid(self, query: str):
        return {
            'tasks': self._search_model_by_uuid(
                Task,
                query,
                related_uuid_fields=['topic', 'subtopic'],
            ),
            'works': self._search_model_by_uuid(Work, query),
            'variants': self._search_model_by_uuid(
                Variant,
                query,
                related_uuid_fields=['work'],
            ),
            'groups': self._search_model_by_uuid(AnalogGroup, query),
        }

    def search_by_text(self, words):
        return {
            'tasks': self._search_tasks_by_text(words),
            'works': self._search_works_by_text(words),
            'variants': self._search_variants_by_text(words),
            'groups': self._search_groups_by_text(words),
        }

    def _search_model_by_uuid(self, model_class, query, related_uuid_fields=None):
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

    def _search_tasks_by_text(self, words):
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

    def _search_works_by_text(self, words):
        work_q = Q()
        for word in words:
            work_q &= Q(name__icontains=word)
        return Work.objects.filter(work_q)[:20]

    def _search_variants_by_text(self, words):
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
            return Variant.objects.filter(variant_q)[:20]
        if number_search:
            return Variant.objects.filter(number=number_search)[:20]
        return Variant.objects.none()

    def _search_groups_by_text(self, words):
        group_q = Q()
        for word in words:
            group_q &= Q(name__icontains=word)
        return AnalogGroup.objects.filter(group_q)[:20]
