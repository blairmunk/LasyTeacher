from unittest import TestCase

from core_logic.entities.report import TaskDBHealthData
from core_logic.use_cases.get_task_db_health import GetTaskDBHealthUseCase


class FakeReportRepository:
    def __init__(self):
        self.called = False

    def get_task_db_health(self):
        self.called = True
        return TaskDBHealthData(
            stats={'total_tasks': 1},
            orphan_variants={'count': 0, 'items': []},
            empty_groups={'count': 0, 'items': []},
            coverage_issues={'count': 0, 'items': []},
            difficulty_dist=[],
            ungrouped_tasks={'count': 0, 'pct': 0},
            fragile_groups={'count': 0, 'items': []},
            works_no_variants={'count': 0, 'items': []},
            works_no_spec={'count': 0, 'items': []},
            type_dist=[],
            most_used_tasks=[],
            group_sizes=[],
            unverified_tasks={'count': 0, 'pct': 0},
            no_source_tasks={'count': 0, 'pct': 0},
            no_grade_tasks={'count': 0, 'pct': 0},
            health={'issues': 0},
            courses=['course'],
        )


class GetTaskDBHealthUseCaseTests(TestCase):
    def test_execute_returns_repository_data(self):
        repo = FakeReportRepository()
        use_case = GetTaskDBHealthUseCase(report_repo=repo)

        data = use_case.execute()

        self.assertTrue(repo.called)
        self.assertEqual(data.stats, {'total_tasks': 1})
        self.assertEqual(data.active_report, 'db-health')
