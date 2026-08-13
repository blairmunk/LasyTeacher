from unittest import TestCase

from core_logic.entities.report_refs import (
    ReportAnalogGroupRef,
    ReportCourseRef,
    ReportVariantRef,
    ReportWorkRef,
)
from core_logic.entities.task_db_health import (
    TaskCoverageFact,
    TaskDBHealthSource,
    TaskDistributionFact,
    TaskGroupSizeFact,
)
from core_logic.use_cases.get_task_db_health import GetTaskDBHealthUseCase


class FakeReportRepository:
    def __init__(self):
        self.called = False

    def get_task_db_health_source(self):
        self.called = True
        work = ReportWorkRef(
            pk='work-1',
            name='Работа',
            work_type='control',
            work_type_display='Контрольная',
            duration=45,
        )
        empty = ReportAnalogGroupRef(pk='group-1', name='Пустая')
        fragile = ReportAnalogGroupRef(pk='group-2', name='Хрупкая')
        return TaskDBHealthSource(
            total_tasks=2,
            total_works=1,
            total_variants=1,
            orphan_variants_count=1,
            orphan_variant_samples=(
                ReportVariantRef(
                    pk='variant-1',
                    short_uuid='V1',
                    number=1,
                    work_name_snapshot='Работа',
                ),
            ),
            group_sizes=(
                TaskGroupSizeFact(group=empty, task_count=0),
                TaskGroupSizeFact(group=fragile, task_count=1),
            ),
            coverage=(
                TaskCoverageFact(
                    work=work,
                    group=fragile,
                    needed=2,
                    available=1,
                ),
            ),
            ungrouped_tasks_count=1,
            works_no_variants_count=1,
            works_no_variant_samples=(work,),
            works_no_spec_count=1,
            works_no_spec_samples=(work,),
            difficulty_counts=(TaskDistributionFact(key=2, count=2),),
            type_counts=(
                TaskDistributionFact(
                    key='computational',
                    count=2,
                    label='Расчётная',
                ),
            ),
            most_used_tasks=(),
            unverified_tasks_count=1,
            no_source_tasks_count=2,
            no_grade_tasks_count=0,
            courses=(ReportCourseRef(pk='course-1', name='Физика'),),
        )


class GetTaskDBHealthUseCaseTests(TestCase):
    def test_execute_returns_repository_data(self):
        repo = FakeReportRepository()
        use_case = GetTaskDBHealthUseCase(report_repo=repo)

        data = use_case.execute()

        self.assertTrue(repo.called)
        self.assertEqual(data.stats.total_tasks, 2)
        self.assertEqual(data.stats.total_groups, 2)
        self.assertEqual(data.stats.total_works, 1)
        self.assertEqual(data.stats.total_variants, 1)
        self.assertEqual(data.empty_groups.count, 1)
        self.assertEqual(data.fragile_groups.count, 1)
        self.assertEqual(data.coverage_issues.items[0].deficit, 1)
        self.assertEqual(data.ungrouped_tasks.count, 1)
        self.assertEqual(data.ungrouped_tasks.pct, 50.0)
        self.assertEqual(data.difficulty_dist[0].pct, 100.0)
        self.assertEqual(data.type_dist[0].label, 'Расчётная')
        self.assertEqual(data.unverified_tasks.pct, 50.0)
        self.assertEqual(data.no_source_tasks.pct, 100.0)
        self.assertEqual(data.health.issues, 7)
        self.assertEqual(data.health.label, 'Есть замечания')
        self.assertEqual(data.active_report, 'db-health')
