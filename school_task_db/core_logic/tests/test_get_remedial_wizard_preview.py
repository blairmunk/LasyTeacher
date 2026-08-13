from unittest import TestCase

from core_logic.entities.student import (
    RemedialWizardAnalogGroup,
    RemedialWizardPreviewSource,
    RemedialWizardTask,
    RemedialWizardTaskLog,
    StudentDetail,
    StudentGroupRef,
)
from core_logic.services.remedial_wizard_service import RemedialWizardService
from core_logic.use_cases.get_remedial_wizard_preview import (
    GetRemedialWizardPreviewUseCase,
    RemedialWizardPreviewRequest,
)
from core_logic.use_cases.get_remedial_wizard_start import (
    LIMIT_CHOICES,
    GetRemedialWizardStartUseCase,
)


class FakeStudentRepository:
    def __init__(self):
        self.request = None
        self.preview_source = RemedialWizardPreviewSource(
            group=StudentGroupRef(pk='group-1', name='9А'),
            students=(
                StudentDetail(
                    pk='student-1',
                    first_name='Иван',
                    last_name='Иванов',
                ),
            ),
        )
        self.groups = [StudentGroupRef(pk='group-1', name='9А')]

    def get_remedial_wizard_preview_source(self, group_id):
        self.request = group_id
        return self.preview_source

    def get_all_student_groups(self):
        return self.groups


class GetRemedialWizardPreviewUseCaseTests(TestCase):
    def test_execute_builds_preview_from_repository_source(self):
        repo = FakeStudentRepository()
        use_case = GetRemedialWizardPreviewUseCase(
            student_learning_repo=repo,
            service=RemedialWizardService(shuffle=lambda items: None),
        )

        result = use_case.execute(
            RemedialWizardPreviewRequest(
                group_id='group-1',
                threshold=60,
                limit_type='weight',
                limit_value=15,
                work_name='Повторение',
            )
        )

        self.assertEqual(repo.request, 'group-1')
        self.assertEqual(result.group, repo.preview_source.group)
        self.assertEqual(result.threshold, 60)
        self.assertEqual(result.limit_type, 'weight')
        self.assertEqual(result.limit_value, 15)
        self.assertEqual(result.work_name, 'Повторение')
        self.assertEqual(result.preview[0].student_level, 'unknown')

    def test_start_use_case_returns_groups_and_limit_choices(self):
        repo = FakeStudentRepository()
        use_case = GetRemedialWizardStartUseCase(student_repo=repo)

        result = use_case.execute()

        self.assertEqual(result.groups, [StudentGroupRef(pk='group-1', name='9А')])
        self.assertEqual(result.limit_choices, LIMIT_CHOICES)


class RemedialWizardServiceTests(TestCase):
    def setUp(self):
        self.service = RemedialWizardService(shuffle=lambda items: None)
        self.student = StudentDetail(
            pk='student-1',
            first_name='Иван',
            last_name='Иванов',
        )
        self.group = StudentGroupRef(pk='class-1', name='9А')

    def test_medium_student_gets_unattempted_task_at_group_difficulty(self):
        source = self._source(
            percentages=(60,),
            tasks=(
                RemedialWizardTask(
                    task_id='done',
                    difficulty=3,
                    analog_group_ids=('analog-1',),
                ),
                RemedialWizardTask(
                    task_id='replacement',
                    difficulty=3,
                    estimated_time=8,
                    analog_group_ids=('analog-1',),
                ),
            ),
        )

        result = self._build(source)

        row = result.preview[0]
        self.assertEqual(row.student_level, 'medium')
        self.assertEqual(row.task_ids, ('replacement',))
        self.assertEqual(row.total_weight, 3)
        self.assertEqual(row.est_time, 8)

    def test_weak_student_uses_tasks_not_harder_than_effective_difficulty(self):
        source = self._source(
            percentages=(20,),
            tasks=(
                RemedialWizardTask(
                    task_id='done',
                    difficulty=3,
                    analog_group_ids=('analog-1',),
                ),
                RemedialWizardTask(
                    task_id='easy',
                    difficulty=2,
                    analog_group_ids=('analog-1',),
                ),
                RemedialWizardTask(
                    task_id='hard',
                    difficulty=5,
                    analog_group_ids=('analog-1',),
                ),
            ),
        )

        result = self._build(source)

        self.assertEqual(result.preview[0].task_ids, ('easy',))

    def test_strong_student_uses_harder_tasks_and_honours_task_limit(self):
        source = self._source(
            percentages=(90,),
            tasks=(
                RemedialWizardTask(
                    task_id='done',
                    difficulty=3,
                    analog_group_ids=('analog-1',),
                ),
                RemedialWizardTask(
                    task_id='hard-1',
                    difficulty=4,
                    analog_group_ids=('analog-1',),
                ),
                RemedialWizardTask(
                    task_id='hard-2',
                    difficulty=5,
                    analog_group_ids=('analog-1',),
                ),
            ),
        )

        result = self._build(source, limit_value=1)

        self.assertEqual(result.preview[0].student_level, 'strong')
        self.assertEqual(result.preview[0].task_ids, ('hard-1',))

    def test_missing_group_returns_not_found(self):
        result = self._build(None)

        self.assertEqual(result.status, 'not_found')

    def _source(self, *, percentages, tasks):
        return RemedialWizardPreviewSource(
            group=self.group,
            students=(self.student,),
            task_logs=tuple(
                RemedialWizardTaskLog(
                    student_id=self.student.pk,
                    task_id='done',
                    analog_group_id='analog-1',
                    percentage=percentage,
                )
                for percentage in percentages
            ),
            tasks=tasks,
            analog_groups=(
                RemedialWizardAnalogGroup(
                    group_id='analog-1',
                    nominal_difficulty=3,
                ),
            ),
        )

    def _build(self, source, *, limit_value=10):
        return self.service.build(
            source,
            threshold=70,
            limit_type='tasks',
            limit_value=limit_value,
            work_name='Работа над ошибками',
        )
