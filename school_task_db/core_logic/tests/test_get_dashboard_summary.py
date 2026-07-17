from unittest import TestCase

from core_logic.use_cases.get_dashboard_summary import GetDashboardSummaryUseCase


class FakeCoreRepository:
    def count_tasks(self):
        return 1

    def count_works(self):
        return 2

    def count_variants(self):
        return 3

    def count_orphan_variants(self):
        return 4

    def count_students(self):
        return 5

    def count_events(self):
        return 6

    def count_analog_groups(self):
        return 7


class GetDashboardSummaryUseCaseTests(TestCase):
    def test_execute_builds_dashboard_summary(self):
        use_case = GetDashboardSummaryUseCase(core_repo=FakeCoreRepository())

        data = use_case.execute()

        self.assertEqual(data.tasks_count, 1)
        self.assertEqual(data.works_count, 2)
        self.assertEqual(data.variants_count, 3)
        self.assertEqual(data.orphan_variants_count, 4)
        self.assertEqual(data.students_count, 5)
        self.assertEqual(data.events_count, 6)
        self.assertEqual(data.groups_count, 7)
