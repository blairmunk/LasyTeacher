from django.test import TestCase
from django.utils import timezone

from core_logic.services.remedial_service import RemedialService
from core_logic.interfaces.event_repo import GradeParticipationParams
from core_logic.use_cases.create_remedial_from_event import (
    CreateRemedialFromEventUseCase,
    RemedialFromEventRequest,
)
from curriculum.models import Topic
from events.models import Event, EventParticipation, Mark
from infrastructure.repositories.django_event_repo import DjangoEventRepository
from infrastructure.repositories.django_review_repo import DjangoReviewRepository
from infrastructure.repositories.django_student_repo import DjangoStudentRepository
from infrastructure.repositories.django_task_repo import DjangoTaskRepository
from infrastructure.repositories.django_work_repo import DjangoWorkRepository
from students.models import Student, StudentGroup, StudentTaskLog
from task_groups.models import AnalogGroup, TaskGroup
from tasks.models import Task
from works.models import Variant, VariantTask, Work, WorkAnalogGroup
from review.models import ReviewComment


class DjangoRemedialRepositoryTests(TestCase):
    def setUp(self):
        self.topic = Topic.objects.create(
            name='Динамика',
            subject='Физика',
            section='Механика',
            grade_level=9,
        )
        self.student = Student.objects.create(
            last_name='Петров',
            first_name='Пётр',
        )
        self.group = StudentGroup.objects.create(name='9Б')
        self.group.students.add(self.student)
        self.source_work = Work.objects.create(
            name='Контрольная по динамике',
            work_type='test',
            max_score=7,
        )
        self.source_variant = Variant.objects.create(
            work=self.source_work,
            number=1,
            work_name_snapshot=self.source_work.name,
            max_score_snapshot=7,
        )
        self.event = Event.objects.create(
            name='КР 9Б',
            work=self.source_work,
            planned_date=timezone.now(),
            status='graded',
        )
        self.participation = EventParticipation.objects.create(
            event=self.event,
            student=self.student,
            variant=self.source_variant,
            status='graded',
        )

        self.original_weak = self._task('Исходное слабое', difficulty=2)
        self.original_ok = self._task('Исходное сильное', difficulty=5)
        self.replacement = self._task('Замена', difficulty=3)
        self.too_hard = self._task('Сложная замена', difficulty=6)

        self.weak_group = AnalogGroup.objects.create(name='Законы Ньютона')
        self.ok_group = AnalogGroup.objects.create(name='Импульс')
        WorkAnalogGroup.objects.create(
            work=self.source_work,
            analog_group=self.weak_group,
            order=1,
            weight=2,
        )
        TaskGroup.objects.create(task=self.original_weak, group=self.weak_group)
        TaskGroup.objects.create(task=self.replacement, group=self.weak_group)
        TaskGroup.objects.create(task=self.too_hard, group=self.weak_group)
        TaskGroup.objects.create(task=self.original_ok, group=self.ok_group)

        VariantTask.objects.create(
            variant=self.source_variant,
            task=self.original_weak,
            order=1,
            max_points=2,
            weight=2,
        )
        VariantTask.objects.create(
            variant=self.source_variant,
            task=self.original_ok,
            order=2,
            max_points=5,
            weight=5,
        )
        self.mark = Mark.objects.create(
            participation=self.participation,
            score=2,
            points=5,
            max_points=7,
            task_scores={
                str(self.original_weak.pk): {'points': 0, 'max_points': 2},
                str(self.original_ok.pk): {'points': 5, 'max_points': 5},
            },
        )

    def _task(self, text, difficulty):
        return Task.objects.create(
            text=text,
            answer='Ответ',
            topic=self.topic,
            task_type='computational',
            difficulty=difficulty,
        )

    def test_repositories_feed_the_pure_remedial_service(self):
        service = RemedialService(
            student_repo=DjangoStudentRepository(),
            task_repo=DjangoTaskRepository(),
            work_repo=DjangoWorkRepository(),
        )

        selection = service.select_tasks_for_student(
            student_id=str(self.student.pk),
            event_id=str(self.event.pk),
            source_work_id=str(self.source_work.pk),
            mark_score=2,
        )

        self.assertEqual(selection.student_id, str(self.student.pk))
        self.assertEqual(selection.task_ids, [str(self.replacement.pk)])
        self.assertEqual(selection.weak_group_ids, {str(self.weak_group.pk)})
        self.assertEqual(selection.target_difficulty, 3)

    def test_student_repository_returns_task_level_mark_results(self):
        results = DjangoStudentRepository().get_task_results_for_event(
            student_id=str(self.student.pk),
            event_id=str(self.event.pk),
        )
        result_by_task = {result.task_id: result for result in results}

        weak_result = result_by_task[str(self.original_weak.pk)]
        self.assertEqual(weak_result.points, 0)
        self.assertEqual(weak_result.max_points, 2)
        self.assertEqual(weak_result.group_id, str(self.weak_group.pk))
        self.assertEqual(weak_result.group_name, self.weak_group.name)

    def test_student_repository_returns_profile_data(self):
        repo = DjangoStudentRepository()

        groups = repo.get_student_groups(str(self.student.pk))
        participations = repo.get_profile_participations(str(self.student.pk))
        task_logs = repo.get_task_logs(str(self.student.pk))
        work_groups = repo.get_work_group_refs([str(self.source_work.pk)])

        self.assertEqual(groups[0].name, '9Б')
        self.assertEqual(participations[0].event.name, self.event.name)
        self.assertEqual(participations[0].work.name, self.source_work.name)
        self.assertEqual(participations[0].work.get_work_type_display(), 'Контрольная работа')
        self.assertEqual(participations[0].mark.points, 5)
        self.assertEqual(participations[0].score, 2)
        self.assertEqual(participations[0].variant_number, 1)
        task_logs_by_id = {log.task.pk: log for log in task_logs}
        weak_log = task_logs_by_id[str(self.original_weak.pk)]
        self.assertEqual(weak_log.task.name, self.original_weak.text)
        self.assertEqual(weak_log.analog_group.name, self.weak_group.name)
        self.assertEqual(weak_log.percentage, 0)
        self.assertEqual(work_groups[0].group_name, self.weak_group.name)

    def test_create_remedial_use_case_creates_django_objects(self):
        student_repo = DjangoStudentRepository()
        task_repo = DjangoTaskRepository()
        work_repo = DjangoWorkRepository()
        event_repo = DjangoEventRepository()
        service = RemedialService(
            student_repo=student_repo,
            task_repo=task_repo,
            work_repo=work_repo,
        )
        use_case = CreateRemedialFromEventUseCase(
            remedial_service=service,
            task_repo=task_repo,
            work_repo=work_repo,
            event_repo=event_repo,
        )

        result = use_case.execute(
            RemedialFromEventRequest(
                event_id=str(self.event.pk),
                selected_student_ids=[str(self.student.pk)],
                work_name='Работа над ошибками 9Б',
                create_event=True,
                event_date='2026-03-10',
            )
        )

        self.assertTrue(result.success)
        remedial_work = Work.objects.get(pk=result.work_id)
        remedial_variant = Variant.objects.get(
            work=remedial_work,
            assigned_student=self.student,
            variant_type='remedial',
        )
        remedial_event = Event.objects.get(pk=result.event_id)
        participation = EventParticipation.objects.get(
            event=remedial_event,
            student=self.student,
        )

        self.assertEqual(remedial_work.name, 'Работа над ошибками 9Б')
        self.assertEqual(remedial_work.work_type, 'remedial')
        self.assertEqual(remedial_work.max_score, self.replacement.difficulty)
        self.assertEqual(remedial_work.variant_counter, 1)
        self.assertEqual(remedial_variant.source_work, self.source_work)
        self.assertEqual(remedial_variant.max_score_snapshot, self.replacement.difficulty)
        self.assertEqual(remedial_event.status, 'planned')
        self.assertEqual(remedial_event.description, f'Работа над ошибками по: {self.source_work.name}')
        self.assertEqual(participation.variant, remedial_variant)
        self.assertEqual(participation.status, 'assigned')

        variant_task = VariantTask.objects.get(variant=remedial_variant)
        self.assertEqual(variant_task.task, self.replacement)
        self.assertEqual(variant_task.max_points, self.replacement.difficulty)
        self.assertEqual(variant_task.weight, self.replacement.difficulty)

    def test_event_repository_grades_participation_and_syncs_review_state(self):
        self.event.status = 'completed'
        self.event.save()
        self.participation.status = 'completed'
        self.participation.save()

        result = DjangoEventRepository().grade_participation(
            GradeParticipationParams(
                participation_id=str(self.participation.pk),
                score=4,
                points=6,
                max_points=7,
                teacher_comment='Хорошая работа',
                checked_by='teacher',
                task_scores={
                    str(self.original_weak.pk): {
                        'points': 1,
                        'max_points': 2,
                        'comment': 'Повторить',
                    },
                },
            )
        )

        self.mark.refresh_from_db()
        self.participation.refresh_from_db()
        self.event.refresh_from_db()
        weak_log = StudentTaskLog.objects.get(
            student=self.student,
            task=self.original_weak,
            event=self.event,
        )

        self.assertEqual(result.score, 4)
        self.assertEqual(result.student_name, 'Петров Пётр')
        self.assertEqual(self.mark.score, 4)
        self.assertEqual(self.mark.points, 6)
        self.assertEqual(self.mark.max_points, 7)
        self.assertEqual(self.mark.teacher_comment, 'Хорошая работа')
        self.assertEqual(self.mark.checked_by, 'teacher')
        self.assertIsNotNone(self.mark.checked_at)
        self.assertEqual(self.participation.status, 'graded')
        self.assertIsNotNone(self.participation.graded_at)
        self.assertEqual(self.event.status, 'graded')
        self.assertEqual(weak_log.points, 1)
        self.assertEqual(weak_log.max_points, 2)
        self.assertEqual(weak_log.comment, 'Повторить')

    def test_event_repository_returns_list_and_detail_page_data(self):
        repo = DjangoEventRepository()

        events = repo.get_list_events()
        participations = repo.get_detail_participations(str(self.event.pk))
        available_variants = repo.get_available_variants(str(self.event.pk))
        event_by_id = {str(event.pk): event for event in events}

        self.assertIn(str(self.event.pk), event_by_id)
        self.assertEqual(event_by_id[str(self.event.pk)].participant_count, 1)
        self.assertEqual(participations[0].student.last_name, self.student.last_name)
        self.assertEqual(participations[0].variant.number, 1)
        self.assertEqual(participations[0].mark_obj.score, 2)
        self.assertEqual(available_variants[0].number, 1)

    def test_review_repository_returns_participation_review_data(self):
        ReviewComment.objects.create(
            text='Аккуратнее с единицами',
            category='suggestion',
            usage_count=3,
        )
        repo = DjangoReviewRepository()

        participation = repo.get_participation(str(self.participation.pk))
        variant_tasks = repo.get_variant_tasks(str(self.participation.pk))
        mark = repo.get_or_create_mark(str(self.participation.pk), default_max_points=7)
        navigation = repo.get_review_participations(str(self.event.pk))
        comments = repo.get_typical_comments()

        self.assertEqual(participation.student.last_name, 'Петров')
        self.assertEqual(participation.event.name, self.event.name)
        self.assertEqual(participation.variant.number, 1)
        self.assertEqual(variant_tasks[0].task.text, self.original_weak.text)
        self.assertEqual(variant_tasks[0].task.topic.name, self.topic.name)
        self.assertEqual(variant_tasks[0].weight, 2)
        self.assertEqual(mark.score, 2)
        self.assertEqual(mark.task_scores[str(self.original_weak.pk)]['points'], 0)
        self.assertEqual(navigation[0].pk, str(self.participation.pk))
        self.assertEqual(comments[0].text, 'Аккуратнее с единицами')

    def test_review_repository_returns_dashboard_and_event_review_data(self):
        repo = DjangoReviewRepository()

        dashboard_events = repo.get_dashboard_events()
        event_rows = repo.get_event_review_participations(str(self.event.pk))
        available_variants = repo.get_available_variants(str(self.event.pk))

        dashboard_by_id = {row.event.pk: row for row in dashboard_events}
        dashboard_row = dashboard_by_id[str(self.event.pk)]
        event_row = event_rows[0]

        self.assertEqual(dashboard_row.event.name, self.event.name)
        self.assertEqual(dashboard_row.event.work.name, self.source_work.name)
        self.assertEqual(dashboard_row.total_participants, 1)
        self.assertEqual(dashboard_row.active_participants, 1)
        self.assertEqual(dashboard_row.graded_participants, 1)
        self.assertEqual(dashboard_row.progress_percentage, 100)
        self.assertEqual(event_row.student.last_name, self.student.last_name)
        self.assertEqual(event_row.variant.tasks.count, 2)
        self.assertTrue(event_row.has_mark)
        self.assertEqual(event_row.mark.score, 2)
        self.assertEqual(available_variants[0].number, 1)
