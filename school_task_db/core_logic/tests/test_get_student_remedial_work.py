from unittest import TestCase

from core_logic.entities.student import (
    ObjectRef,
    StudentRemedialCandidateTask,
    StudentRemedialSource,
    StudentRemedialTaskLog,
)
from core_logic.services.student_remedial_service import StudentRemedialService
from core_logic.use_cases.get_student_remedial_work import (
    GetStudentRemedialWorkUseCase,
)


class FakeStudentRepository:
    def __init__(self):
        self.requested_student_id = None
        group = ObjectRef(pk='group-1', name='Кинематика')
        topic = ObjectRef(pk='topic-1', name='Скорость')
        self.source = StudentRemedialSource(
            task_logs=(
                StudentRemedialTaskLog(
                    task_id='done-1',
                    analog_group=group,
                    topic=topic,
                    percentage=20,
                    is_correct=False,
                ),
                StudentRemedialTaskLog(
                    task_id='done-2',
                    analog_group=group,
                    topic=topic,
                    percentage=80,
                    is_correct=True,
                ),
            ),
            tasks=(
                StudentRemedialCandidateTask(
                    task_id='done-1',
                    text='Решённое задание',
                    analog_group_ids=('group-1',),
                ),
                StudentRemedialCandidateTask(
                    task_id='new-1',
                    text='Новое задание',
                    analog_group_ids=('group-1',),
                ),
            ),
        )

    def get_student_remedial_source(self, student_id):
        self.requested_student_id = student_id
        return self.source


class GetStudentRemedialWorkUseCaseTests(TestCase):
    def test_execute_builds_remedial_analysis_from_repository_source(self):
        repo = FakeStudentRepository()
        use_case = GetStudentRemedialWorkUseCase(
            student_learning_repo=repo,
            service=StudentRemedialService(shuffle=lambda items: None),
        )

        result = use_case.execute('student-1')

        self.assertEqual(repo.requested_student_id, 'student-1')
        self.assertFalse(result.no_data)
        self.assertEqual(result.done_count, 2)
        self.assertEqual(result.total_available, 1)
        self.assertEqual(result.remedial_groups[0]['avg_pct'], 50.0)
        self.assertEqual(result.remedial_groups[0]['correct'], 1)
        self.assertEqual(result.remedial_groups[0]['wrong'], 1)
        self.assertEqual(
            result.remedial_groups[0]['available_tasks'][0].pk,
            'new-1',
        )
        self.assertEqual(result.weak_topics[0]['topic__name'], 'Скорость')

    def test_service_reports_no_data_for_empty_history(self):
        result = StudentRemedialService().analyze(StudentRemedialSource())

        self.assertTrue(result.no_data)

    def test_service_selects_two_new_tasks_per_weak_group(self):
        repo = FakeStudentRepository()
        source = StudentRemedialSource(
            task_logs=repo.source.task_logs,
            tasks=repo.source.tasks + (
                StudentRemedialCandidateTask(
                    task_id='new-2',
                    text='Ещё одно задание',
                    analog_group_ids=('group-1',),
                ),
                StudentRemedialCandidateTask(
                    task_id='new-3',
                    text='Третье задание',
                    analog_group_ids=('group-1',),
                ),
            ),
        )
        service = StudentRemedialService(shuffle=lambda items: None)

        selected = service.select_task_ids(
            source,
            max_tasks=10,
            selected_group_ids=[],
        )

        self.assertEqual(selected, ['new-1', 'new-2'])
