"""Build course list screen data."""

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.curriculum import CourseListData
from core_logic.interfaces.course_catalog_repo import ICourseCatalogRepository


class GetCourseListUseCase:
    def __init__(self, curriculum_repo: ICourseCatalogRepository):
        self.curriculum_repo = curriculum_repo

    def execute(
        self,
        year: AcademicYearRef | None = None,
    ) -> CourseListData:
        return CourseListData(
            courses=tuple(self.curriculum_repo.get_courses(year=year)),
        )
