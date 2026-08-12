"""Django query adapter for validating task classifications."""

from django.core.exceptions import ValidationError

from codifier.models import ContentEntry, Requirement
from core_logic.interfaces.task_classification_repo import (
    ITaskClassificationRepository,
)
from curriculum.models import Topic


class DjangoTaskClassificationRepository(ITaskClassificationRepository):
    def get_classification_errors(
        self,
        topic_id,
        content_entry_ids,
        requirement_ids,
    ):
        topic = Topic.objects.filter(pk=topic_id).only('subject').first()
        if topic is None:
            return ('Тема задания не найдена',)

        errors = []
        if not self._all_match_subject(
            ContentEntry,
            content_entry_ids,
            topic.subject,
        ):
            errors.append(
                'Выбраны несуществующие элементы содержания '
                'или элементы другого предмета',
            )
        if not self._all_match_subject(
            Requirement,
            requirement_ids,
            topic.subject,
        ):
            errors.append(
                'Выбраны несуществующие требования '
                'или требования другого предмета',
            )
        return tuple(errors)

    @staticmethod
    def _all_match_subject(model, object_ids, subject):
        if not object_ids:
            return True
        try:
            matching_ids = {
                str(object_id)
                for object_id in model.objects.filter(
                    pk__in=object_ids,
                    codifier__subject=subject,
                ).values_list('pk', flat=True)
            }
        except (ValueError, ValidationError):
            return False
        return matching_ids == set(object_ids)
