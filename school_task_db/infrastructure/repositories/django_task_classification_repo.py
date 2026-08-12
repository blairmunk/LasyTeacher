"""Django query adapter for validating task classifications."""

from django.core.exceptions import ValidationError

from codifier.models import ContentEntry, Requirement
from core_logic.entities.task import SelectOption, TaskClassificationOptions
from core_logic.interfaces.task_classification_repo import (
    ITaskClassificationRepository,
)
from curriculum.models import Topic
from infrastructure.services.django_task_classification_queries import (
    task_classification_querysets,
)


class DjangoTaskClassificationRepository(ITaskClassificationRepository):
    def get_classification_options(self, topic_id):
        topic = self._get_topic(topic_id)
        if topic is None:
            return TaskClassificationOptions(
                content_entries=[],
                requirements=[],
            )

        content_entries, requirements = task_classification_querysets(
            topic=topic,
        )
        return TaskClassificationOptions(
            content_entries=self._get_options(content_entries),
            requirements=self._get_options(
                requirements,
                code_prefix='Тр. ',
            ),
        )

    def get_classification_errors(
        self,
        topic_id,
        content_entry_ids,
        requirement_ids,
    ):
        topic = self._get_topic(topic_id)
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
    def _get_topic(topic_id):
        try:
            return Topic.objects.filter(pk=topic_id).only('subject').first()
        except (ValueError, ValidationError):
            return None

    @staticmethod
    def _get_options(objects, code_prefix=''):
        return [
            SelectOption(
                id=str(item.pk),
                name=(
                    f'{item.codifier.short_name} · '
                    f'{code_prefix}{item.code} · {item.name}'
                ),
            )
            for item in objects
        ]

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
