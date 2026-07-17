"""Build course list screen data."""

from core_logic.entities.curriculum import CourseListData
from core_logic.interfaces.curriculum_repo import ICurriculumRepository


class GetCourseListUseCase:
    def __init__(self, curriculum_repo: ICurriculumRepository):
        self.curriculum_repo = curriculum_repo

    def execute(self) -> CourseListData:
        return CourseListData(courses=self.curriculum_repo.get_courses())
