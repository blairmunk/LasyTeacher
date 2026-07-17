"""Django implementation of the curriculum repository."""

from core_logic.interfaces.curriculum_repo import ICurriculumRepository
from curriculum.models import Course, CourseAssignment, Topic
from works.models import Variant, WorkAnalogGroup


class DjangoCurriculumRepository(ICurriculumRepository):
    def get_course(self, course_id: str):
        return Course.objects.filter(pk=course_id).first()

    def get_course_assignments(self, course_id: str):
        return CourseAssignment.objects.filter(
            course_id=course_id,
        ).select_related(
            'work',
        ).order_by('order')

    def get_work_analog_groups(self, work_id: str):
        return list(
            WorkAnalogGroup.objects.filter(
                work_id=work_id,
            ).select_related(
                'analog_group',
            )
        )

    def count_work_variants(self, work_id: str) -> int:
        return Variant.objects.filter(work_id=work_id).count()

    def get_topic_subtopics(self, topic_id: str) -> list:
        topic = Topic.objects.filter(pk=topic_id).first()
        if not topic:
            return []
        return [
            {
                'id': str(subtopic.pk),
                'name': subtopic.name,
                'description': subtopic.description,
            }
            for subtopic in topic.subtopics.all().order_by('order')
        ]
