"""Build course detail screen data."""

from collections import Counter

from core_logic.entities.curriculum import CourseDetailData
from core_logic.interfaces.curriculum_repo import ICurriculumRepository


class GetCourseDetailUseCase:
    def __init__(self, curriculum_repo: ICurriculumRepository):
        self.curriculum_repo = curriculum_repo

    def get_queryset(self):
        return self.curriculum_repo.get_detail_courses()

    def execute(self, course_id: str) -> CourseDetailData:
        assignments = []
        total_variants = 0
        works_by_type = Counter()
        groups_coverage = Counter()

        for assignment in self.curriculum_repo.get_course_assignments(course_id):
            work = assignment.work
            work_groups = self.curriculum_repo.get_work_analog_groups(str(work.pk))
            variants_count = self.curriculum_repo.count_work_variants(str(work.pk))

            assignment.groups_count = len(work_groups)
            assignment.tasks_per_variant = sum(group.count for group in work_groups)
            assignment.variants_count = variants_count

            total_variants += variants_count
            works_by_type[work.get_work_type_display()] += 1
            for work_group in work_groups:
                groups_coverage[work_group.analog_group.name] += 1

            assignments.append(assignment)

        return CourseDetailData(
            assignments=assignments,
            total_variants=total_variants,
            works_by_type=dict(works_by_type),
            groups_coverage=dict(groups_coverage.most_common()),
        )
