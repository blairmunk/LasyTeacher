"""Build course detail screen data."""

from collections import Counter
from dataclasses import replace

from core_logic.entities.curriculum import CourseDetailData
from core_logic.interfaces.curriculum_repo import ICurriculumRepository


class GetCourseDetailUseCase:
    def __init__(self, curriculum_repo: ICurriculumRepository):
        self.curriculum_repo = curriculum_repo

    def execute(self, course_id: str) -> CourseDetailData:
        course = self.curriculum_repo.get_course(course_id)
        if course is None:
            return CourseDetailData()

        assignments = []
        total_variants = 0
        works_by_type = Counter()
        groups_coverage = Counter()

        for assignment in self.curriculum_repo.get_course_assignments(course_id):
            work_groups = self.curriculum_repo.get_work_analog_groups(
                assignment.work.pk,
            )
            variants_count = self.curriculum_repo.count_work_variants(
                assignment.work.pk,
            )

            assignment = replace(
                assignment,
                groups_count=len(work_groups),
                tasks_per_variant=sum(group.count for group in work_groups),
                variants_count=variants_count,
            )

            total_variants += variants_count
            works_by_type[assignment.work.work_type_display] += 1
            for work_group in work_groups:
                groups_coverage[work_group.group_name] += 1

            assignments.append(assignment)

        return CourseDetailData(
            course=course,
            assignments=assignments,
            total_variants=total_variants,
            works_by_type=dict(works_by_type),
            groups_coverage=dict(groups_coverage.most_common()),
        )
