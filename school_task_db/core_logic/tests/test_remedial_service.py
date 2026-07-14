from unittest import TestCase

from core_logic.entities.student import TaskResult
from core_logic.entities.task import TaskEntity
from core_logic.services.remedial_service import (
    RemedialConfig,
    RemedialService,
)


class FakeStudentRepository:
    def __init__(self, results=None):
        self.results = results or []

    def get_task_results_for_event(self, student_id, event_id):
        return self.results


class FakeTaskRepository:
    def __init__(self):
        self.task_groups = {
            't1': {'g1'},
            't2': {'g2'},
            't10': {'g1'},
            't11': {'g1'},
            't20': {'g2'},
        }
        self.group_tasks = {
            'g1': {'t1', 't10', 't11'},
            'g2': {'t2', 't20'},
        }
        self.tasks = {
            't10': TaskEntity(id='t10', difficulty=3),
            't11': TaskEntity(id='t11', difficulty=6),
            't20': TaskEntity(id='t20', difficulty=4),
        }

    def get_group_ids_for_tasks(self, task_ids):
        group_ids = set()
        for task_id in task_ids:
            group_ids.update(self.task_groups.get(task_id, set()))
        return group_ids

    def get_tasks_in_group(self, group_id):
        return set(self.group_tasks[group_id])

    def get_tasks_by_difficulty(self, task_ids, max_difficulty):
        tasks = [
            self.tasks[task_id]
            for task_id in task_ids
            if task_id in self.tasks
            and self.tasks[task_id].difficulty <= max_difficulty
        ]
        return sorted(tasks, key=lambda task: (task.difficulty, task.id))


class FakeWorkRepository:
    def get_variant_task_ids(self, work_id):
        return {'t1', 't2'}

    def get_student_variant_task_ids(self, work_id, student_id, event_id):
        return {'t1', 't2'}


class RemedialServiceTests(TestCase):
    def service(self, results=None):
        return RemedialService(
            student_repo=FakeStudentRepository(results),
            task_repo=FakeTaskRepository(),
            work_repo=FakeWorkRepository(),
            config=RemedialConfig(max_tasks_per_group=1, max_total_tasks=5),
        )

    def test_find_weak_tasks_matches_current_binary_and_graded_rules(self):
        service = self.service()

        weak = service.find_weak_tasks([
            TaskResult(task_id='zero_of_two', points=0, max_points=2),
            TaskResult(task_id='one_of_two', points=1, max_points=2),
            TaskResult(task_id='one_of_five', points=1, max_points=5),
            TaskResult(task_id='three_of_five', points=3, max_points=5),
        ])

        self.assertEqual(weak, {'zero_of_two', 'one_of_five'})

    def test_target_difficulty_matches_current_mark_score_rules(self):
        service = self.service()

        self.assertEqual(service.target_difficulty(None), 3)
        self.assertEqual(service.target_difficulty(2), 3)
        self.assertEqual(service.target_difficulty(3), 4)
        self.assertEqual(service.target_difficulty(4), 6)
        self.assertEqual(service.target_difficulty(5), 6)

    def test_select_tasks_uses_weak_groups_and_excludes_student_variant_tasks(self):
        service = self.service([
            TaskResult(task_id='t1', points=0, max_points=2),
            TaskResult(task_id='t2', points=5, max_points=5),
        ])

        selection = service.select_tasks_for_student(
            student_id='s1',
            event_id='e1',
            source_work_id='w1',
            mark_score=2,
        )

        self.assertEqual(selection.task_ids, ['t10'])
        self.assertEqual(selection.weak_group_ids, {'g1'})
        self.assertEqual(selection.target_difficulty, 3)

    def test_select_tasks_falls_back_to_all_work_groups_without_task_scores(self):
        service = self.service([])

        selection = service.select_tasks_for_student(
            student_id='s1',
            event_id='e1',
            source_work_id='w1',
            mark_score=None,
        )

        self.assertEqual(selection.task_ids, ['t10', 't20'])
        self.assertEqual(selection.weak_group_ids, {'g1', 'g2'})
