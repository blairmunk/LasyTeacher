"""Django task catalog adapter."""

from typing import List

from core_logic.entities.task import ReferenceElementOption, SelectOption
from core_logic.interfaces.task_reference_catalog_repo import (
    ITaskReferenceCatalogRepository,
)
from core_logic.interfaces.task_taxonomy_repo import ITaskTaxonomyRepository
from core_logic.services.reference_catalog import merge_reference_choices
from curriculum.models import SubTopic, Topic
from references.models import SubjectReference
from tasks.models import Source, Task


class DjangoTaskCatalogRepository(
    ITaskTaxonomyRepository,
    ITaskReferenceCatalogRepository,
):
    def get_subtopic_topic_id(self, subtopic_id: str):
        topic_id = SubTopic.objects.filter(pk=subtopic_id).values_list(
            'topic_id',
            flat=True,
        ).first()
        return str(topic_id) if topic_id else None

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
