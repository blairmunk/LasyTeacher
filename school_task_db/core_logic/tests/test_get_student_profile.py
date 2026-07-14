from unittest import TestCase

from core_logic.entities.student import (
    EventRef,
    ObjectRef,
    StudentParticipationProfile,
    WorkGroupRef,
    WorkRef,
)
from core_logic.services.analytics_service import StudentAnalyticsService
from core_logic.use_cases.get_student_profile import GetStudentProfileUseCase


class FakeStudentRepository:
    def __init__(self):
        self.requested_work_ids = None
        self.work = WorkRef(
            pk='w1',
            name='Контрольная',
            work_type='test',
            work_type_display='Контрольная работа',
        )

    def get_student_groups(self, student_id):
        return []

    def get_profile_participations(self, student_id):
        return [
            StudentParticipationProfile(
                participation=ObjectRef(pk='p1'),
                event=EventRef(pk='e1', name='КР'),
                work=self.work,
                mark=None,
                score=4,
                is_absent=False,
            ),
            StudentParticipationProfile(
                participation=ObjectRef(pk='p2'),
                event=EventRef(pk='e2', name='Без оценки'),
                work=self.work,
                mark=None,
                score=None,
                is_absent=False,
            ),
        ]

    def get_task_logs(self, student_id):
        return []

    def get_work_group_refs(self, work_ids):
        self.requested_work_ids = work_ids
        return [WorkGroupRef(work_id='w1', group_id='ag1', group_name='Скорость')]

    def get_task_results_for_event(self, student_id, event_id):
        return []


class GetStudentProfileUseCaseTests(TestCase):
    def test_execute_builds_profile_from_repository_data(self):
        repo = FakeStudentRepository()
        use_case = GetStudentProfileUseCase(
            student_repo=repo,
            analytics_service=StudentAnalyticsService(),
        )

        profile = use_case.execute('s1')

        self.assertEqual(repo.requested_work_ids, ['w1'])
        self.assertEqual(profile.stats['graded_works'], 1)
        self.assertEqual(profile.group_scores[0]['name'], 'Скорость')
