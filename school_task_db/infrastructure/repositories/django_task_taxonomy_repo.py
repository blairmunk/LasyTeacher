"""Django read adapter for task taxonomy options."""

from typing import List

from core_logic.entities.task import SelectOption
from core_logic.interfaces.task_taxonomy_repo import ITaskTaxonomyRepository
from curriculum.models import SubTopic, Topic
from tasks.models import Source, Task


class DjangoTaskTaxonomyRepository(ITaskTaxonomyRepository):
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

    def get_task_type_choices(self):
        return list(Task.TASK_TYPES)
