"""Django implementation of the curriculum repository."""

from core_logic.entities.curriculum import (
    CourseDetailAssignment,
    CourseDetailCourse,
    CourseDetailWork,
    CourseDetailWorkGroup,
)
from core_logic.interfaces.curriculum_repo import ICurriculumRepository
from curriculum.models import Course, CourseAssignment, Topic
from works.models import Variant, WorkAnalogGroup


class DjangoCurriculumRepository(ICurriculumRepository):
    def get_course(self, course_id: str):
        course = Course.objects.filter(pk=course_id).first()
        if course is None:
            return None

        return CourseDetailCourse(
            pk=str(course.pk),
            name=course.name,
            subject=course.subject,
            grade_level=course.grade_level,
            academic_year=str(course.academic_year),
            is_active=course.is_active,
            description=course.description,
            start_date=course.start_date,
            end_date=course.end_date,
            hours_per_week=course.hours_per_week,
            total_hours=course.total_hours,
        )

    def get_course_assignments(self, course_id: str):
        assignments = CourseAssignment.objects.filter(
            course_id=course_id,
        ).select_related(
            'work',
        ).order_by('order')

        return [
            CourseDetailAssignment(
                order=assignment.order,
                work=CourseDetailWork(
                    pk=str(assignment.work.pk),
                    name=assignment.work.name,
                    work_type=assignment.work.work_type,
                    work_type_display=assignment.work.get_work_type_display(),
                ),
                weight=assignment.weight,
                planned_date=assignment.planned_date,
            )
            for assignment in assignments
        ]

    def get_work_analog_groups(self, work_id: str):
        work_groups = WorkAnalogGroup.objects.filter(
            work_id=work_id,
        ).select_related(
            'analog_group',
        )

        return [
            CourseDetailWorkGroup(
                group_name=work_group.analog_group.name,
                count=work_group.count,
            )
            for work_group in work_groups
        ]

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
