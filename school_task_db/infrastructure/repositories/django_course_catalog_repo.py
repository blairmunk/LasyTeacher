"""Django read adapter for course catalog and detail screens."""

from django.db.models import Count

from core_logic.entities.curriculum import (
    CourseDetailAssignment,
    CourseDetailCourse,
    CourseDetailWork,
    CourseDetailWorkGroup,
    CourseListItem,
)
from core_logic.interfaces.course_catalog_repo import ICourseCatalogRepository
from curriculum.models import Course, CourseAssignment
from works.models import Variant, WorkAnalogGroup


class DjangoCourseCatalogRepository(ICourseCatalogRepository):
    def get_courses(self, year=None):
        courses = Course.objects.select_related('year')
        if year:
            courses = courses.filter(year_id=year.pk)
        return [
            CourseListItem(
                pk=str(course.pk),
                name=course.name,
                subject=course.subject,
                grade_level=course.grade_level,
                academic_year=str(course.year or ''),
                is_active=course.is_active,
                description=course.description,
                start_date=course.start_date,
                end_date=course.end_date,
                hours_per_week=course.hours_per_week,
                assignments_count=course.assignments_count,
            )
            for course in courses.annotate(
                assignments_count=Count('courseassignment'),
            ).order_by('subject', 'grade_level', 'name')
        ]

    def get_course(self, course_id: str):
        course = Course.objects.select_related('year').filter(
            pk=course_id,
        ).first()
        if course is None:
            return None

        return CourseDetailCourse(
            pk=str(course.pk),
            name=course.name,
            subject=course.subject,
            grade_level=course.grade_level,
            academic_year=str(course.year or ''),
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
