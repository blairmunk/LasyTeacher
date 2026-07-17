from django.test import SimpleTestCase

from core_logic.entities.curriculum import CourseListItem
from core_logic.use_cases.get_course_list import GetCourseListUseCase


class FakeCurriculumRepository:
    def __init__(self):
        self.courses = [
            CourseListItem(
                pk='course-1',
                name='Физика 9',
                subject='Физика',
                grade_level=9,
                assignments_count=2,
            )
        ]

    def get_courses(self):
        return self.courses


class GetCourseListUseCaseTests(SimpleTestCase):
    def test_execute_returns_course_list_data(self):
        repo = FakeCurriculumRepository()

        data = GetCourseListUseCase(curriculum_repo=repo).execute()

        self.assertEqual(data.courses, repo.courses)
        self.assertEqual(data.courses[0].assignments_count, 2)
