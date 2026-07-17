from unittest import TestCase

from core_logic.entities.curriculum import (
    CourseDetailAssignment,
    CourseDetailCourse,
    CourseDetailWork,
    CourseDetailWorkGroup,
)
from core_logic.use_cases.get_course_detail import GetCourseDetailUseCase


class FakeCurriculumRepository:
    def __init__(self):
        self.course = CourseDetailCourse(
            pk='course-1',
            name='Физика 9',
            subject='Физика',
            grade_level=9,
        )
        self.work = CourseDetailWork(
            pk='work-1',
            name='Контрольная',
            work_type='test',
            work_type_display='Контрольная работа',
        )
        self.assignments = [CourseDetailAssignment(order=1, work=self.work, weight=1)]
        self.work_groups = [CourseDetailWorkGroup(count=2, group_name='Скорость')]

    def get_course(self, course_id):
        return self.course if course_id == self.course.pk else None

    def get_course_assignments(self, course_id):
        return self.assignments

    def get_work_analog_groups(self, work_id):
        return self.work_groups

    def count_work_variants(self, work_id):
        return 3


class GetCourseDetailUseCaseTests(TestCase):
    def test_execute_builds_course_detail_data(self):
        repo = FakeCurriculumRepository()
        use_case = GetCourseDetailUseCase(curriculum_repo=repo)

        data = use_case.execute('course-1')

        self.assertEqual(data.course, repo.course)
        self.assertEqual(data.assignments[0].work, repo.work)
        self.assertEqual(data.assignments[0].groups_count, 1)
        self.assertEqual(data.assignments[0].tasks_per_variant, 2)
        self.assertEqual(data.assignments[0].variants_count, 3)
        self.assertEqual(data.total_variants, 3)
        self.assertEqual(data.works_by_type, {'Контрольная работа': 1})
        self.assertEqual(data.groups_coverage, {'Скорость': 1})

    def test_execute_returns_empty_data_for_missing_course(self):
        repo = FakeCurriculumRepository()
        use_case = GetCourseDetailUseCase(curriculum_repo=repo)

        data = use_case.execute('missing-course')

        self.assertIsNone(data.course)
        self.assertEqual(data.assignments, [])
        self.assertEqual(data.total_variants, 0)
