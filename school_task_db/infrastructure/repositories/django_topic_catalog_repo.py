"""Django read adapter for curriculum topics and subtopics."""

from django.db.models import Count

from core_logic.entities.curriculum import (
    TopicDetailSubtopic,
    TopicDetailTopic,
    TopicListItem,
    TopicSubtopicOption,
)
from core_logic.interfaces.topic_catalog_repo import ITopicCatalogRepository
from curriculum.models import Topic


class DjangoTopicCatalogRepository(ITopicCatalogRepository):
    def get_topics(self):
        return [
            TopicListItem(
                pk=str(topic.pk),
                name=topic.name,
                subject=topic.subject,
                section=topic.section,
                grade_level=topic.grade_level,
                order=topic.order,
                difficulty_level=topic.difficulty_level,
                difficulty_level_display=topic.get_difficulty_level_display(),
                description=topic.description,
                subtopics_count=topic.subtopics_count,
            )
            for topic in Topic.objects.annotate(
                subtopics_count=Count('subtopics'),
            ).order_by('subject', 'grade_level', 'section', 'order')
        ]

    def get_topic(self, topic_id: str):
        topic = Topic.objects.filter(pk=topic_id).first()
        if topic is None:
            return None

        return TopicDetailTopic(
            pk=str(topic.pk),
            name=topic.name,
            subject=topic.subject,
            section=topic.section,
            grade_level=topic.grade_level,
            order=topic.order,
            difficulty_level=topic.difficulty_level,
            difficulty_level_display=topic.get_difficulty_level_display(),
            description=topic.description,
        )

    def get_topic_detail_subtopics(self, topic_id: str):
        topic = Topic.objects.filter(pk=topic_id).first()
        if topic is None:
            return []
        return [
            TopicDetailSubtopic(
                pk=str(subtopic.pk),
                name=subtopic.name,
                description=subtopic.description,
                order=subtopic.order,
            )
            for subtopic in topic.subtopics.all().order_by('order')
        ]

    def get_topic_subtopics(self, topic_id: str):
        topic = Topic.objects.filter(pk=topic_id).first()
        if not topic:
            return ()
        return tuple(
            TopicSubtopicOption(
                id=str(subtopic.pk),
                name=subtopic.name,
                description=subtopic.description,
            )
            for subtopic in topic.subtopics.all().order_by('order')
        )
