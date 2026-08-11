import datetime as dt
from unittest.mock import Mock

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from core.models import AcademicYear, ImportLog
from core_logic.services.grading_service import GradingService
from core_logic.services.remedial_service import RemedialService
from core_logic.services.student_task_result_service import (
    StudentTaskResultService,
)
from core_logic.services.work_variant_composition_service import (
    WorkVariantCompositionService,
)
from core_logic.entities.work_variant_composition import (
    VariantContentBlockCreationPlan,
)
from core_logic.services.remedial_variant_content_service import (
    build_remedial_variant_creation_plan,
)
from core_logic.services.work_spec_sync_service import WorkSpecSyncService
from core_logic.interfaces.event_commands import (
    CreateEventParams,
)
from core_logic.interfaces.orphan_variant_repo import (
    CreateWorkFromOrphanVariantsParams,
)
from core_logic.interfaces.work_commands import (
    CreateWorkParams,
    CreateWorkWithSpecificationParams,
    CreateWorkWithVariantsParams,
    CreateWorkWithVariantFromTasksParams,
    NewWorkVariantParams,
    WorkContentBlockParams,
    WorkTaskSelectionParams,
)
from core_logic.entities.task import (
    SourceCreateParams,
    TaskExportFilters,
    TaskGroupListFilters,
    TaskImageSaveParams,
    TaskListFilters,
    TaskSaveParams,
)
from core_logic.entities.student import SaveStudentGroupParams, SaveStudentParams
from core_logic.entities.work import WorkListFilters
from core_logic.use_cases.create_remedial_from_event import (
    CreateRemedialFromEventUseCase,
    RemedialFromEventRequest,
)
from core_logic.use_cases.create_work_from_orphans import (
    CreateWorkFromOrphansRequest,
    CreateWorkFromOrphansUseCase,
)
from core_logic.use_cases.get_remedial_sheet_data import (
    GetRemedialSheetDataUseCase,
)
from core_logic.use_cases.export_tasks import (
    ExportTasksRequest,
    ExportTasksUseCase,
)
from core_logic.use_cases.compose_work_variants import (
    ComposeWorkVariantsRequest,
    ComposeWorkVariantsUseCase,
)
from core_logic.use_cases.grade_student_work import (
    GradeStudentWorkRequest,
    GradeStudentWorkUseCase,
)
from core_logic.use_cases.sync_work_analog_groups import (
    SyncWorkAnalogGroupsRequest,
    SyncWorkAnalogGroupsUseCase,
)
from core_logic.use_cases.toggle_participation_absent import (
    ToggleParticipationAbsentRequest,
    ToggleParticipationAbsentUseCase,
)
from core_logic.value_objects.task_print_settings import (
    DEFAULT_BLANK_CELLS_ROWS,
    TASK_BANK_ROLE_DEMO,
    TASK_BANK_ROLE_PRACTICE,
    TASK_BANK_ROLE_REMEDIAL,
    TASK_RENDER_MODE_WITH_FULL_SOLUTION,
)
from codifier.models import CodifierSpec, ContentEntry, Requirement
from curriculum.models import Course, CourseAssignment, SubTopic, Topic
from events.models import AttemptSnapshot, Event, EventParticipation, Mark
from infrastructure.repositories.django_attempt_snapshot_repo import (
    DjangoAttemptSnapshotRepository,
)
from infrastructure.repositories.django_codifier_repo import DjangoCodifierRepository
from infrastructure.repositories.django_core_repo import DjangoCoreRepository
from infrastructure.repositories.django_curriculum_repo import (
    DjangoCurriculumRepository,
)
from infrastructure.repositories.django_event_attempt_repo import (
    DjangoEventAttemptRepository,
)
from infrastructure.repositories.django_event_participation_repo import (
    DjangoEventParticipationRepository,
)
from infrastructure.repositories.django_event_read_repo import (
    DjangoEventReadRepository,
)
from infrastructure.repositories.django_event_write_repo import (
    DjangoEventWriteRepository,
)
from infrastructure.repositories.django_participation_grading_repo import (
    DjangoParticipationGradingRepository,
)
from infrastructure.repositories.django_orphan_variant_repo import (
    DjangoOrphanVariantRepository,
)
from infrastructure.repositories.django_review_repo import DjangoReviewRepository
from infrastructure.repositories.django_review_session_repo import (
    DjangoReviewSessionRepository,
)
from infrastructure.repositories.django_review_task_repo import (
    DjangoReviewTaskRepository,
)
from infrastructure.repositories.django_source_repo import DjangoSourceRepository
from infrastructure.repositories.django_student_repo import DjangoStudentRepository
from infrastructure.repositories.django_student_profile_repo import (
    DjangoStudentProfileRepository,
)
from infrastructure.repositories.django_student_remedial_repo import (
    DjangoStudentRemedialRepository,
)
from infrastructure.repositories.django_task_read_repo import (
    DjangoTaskReadRepository,
)
from infrastructure.repositories.django_task_write_repo import (
    DjangoTaskWriteRepository,
)
from infrastructure.repositories.django_task_selection_repo import (
    DjangoTaskSelectionRepository,
)
from infrastructure.repositories.django_task_catalog_repo import (
    DjangoTaskCatalogRepository,
)
from infrastructure.repositories.django_task_export_repo import (
    DjangoTaskExportRepository,
)
from infrastructure.repositories.django_task_group_repo import (
    DjangoTaskGroupRepository,
)
from infrastructure.repositories.django_work_specification_repo import (
    DjangoWorkSpecificationRepository,
)
from infrastructure.repositories.django_work_variant_creation_repo import (
    DjangoWorkVariantCreationRepository,
)
from infrastructure.repositories.django_variant_generation_form_repo import (
    DjangoVariantGenerationFormRepository,
)
from infrastructure.repositories.django_work_spec_sync_repo import (
    DjangoWorkSpecSyncRepository,
)
from infrastructure.repositories.django_work_variant_composition_repo import (
    DjangoWorkVariantCompositionRepository,
)
from infrastructure.repositories.django_work_read_repo import (
    DjangoWorkReadRepository,
)
from infrastructure.repositories.django_variant_read_repo import (
    DjangoVariantReadRepository,
)
from infrastructure.repositories.django_variant_lifecycle_repo import (
    DjangoVariantLifecycleRepository,
)
from infrastructure.repositories.django_work_document_repo import (
    DjangoWorkDocumentRepository,
)
from infrastructure.repositories.django_remedial_sheet_repo import (
    DjangoRemedialSheetRepository,
)
from infrastructure.repositories.django_remedial_task_group_repo import (
    DjangoRemedialTaskGroupRepository,
)
from infrastructure.repositories.django_remedial_source_repo import (
    DjangoRemedialSourceRepository,
)
from infrastructure.tests.variant_task_factory import (
    capture_attempt_snapshot,
    create_variant_task,
)
from infrastructure.services.django_transaction_manager import (
    DjangoTransactionManager,
)
from students.models import Student, StudentGroup
from task_groups.models import AnalogGroup, TaskGroup
from tasks.models import Source, Task, TaskImage
from works.models import (
    Variant,
    VariantContentBlockSnapshot,
    VariantTask,
    Work,
    WorkAnalogGroup,
    WorkContentBlock,
)
from review.models import ReviewComment, ReviewSession


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
        self.subtopic = SubTopic.objects.create(
            topic=self.topic,
            name='Второй закон Ньютона',
            order=1,
        )

        self.weak_group = AnalogGroup.objects.create(name='Законы Ньютона')
        self.ok_group = AnalogGroup.objects.create(name='Импульс')
        self.weak_selection = WorkAnalogGroup.objects.create(
            work=self.source_work,
            analog_group=self.weak_group,
            order=1,
            weight=2,
        )
        TaskGroup.objects.create(task=self.original_weak, group=self.weak_group)
        TaskGroup.objects.create(task=self.replacement, group=self.weak_group)
        TaskGroup.objects.create(task=self.too_hard, group=self.weak_group)
        TaskGroup.objects.create(task=self.original_ok, group=self.ok_group)

        create_variant_task(
            variant=self.source_variant,
            task=self.original_weak,
            order=1,
            max_points=2,
            weight=2,
            source_selection_id=str(self.weak_selection.pk),
            content_order=self.weak_selection.order,
        )
        create_variant_task(
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
        capture_attempt_snapshot(self.mark)

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
            student_remedial_repo=DjangoStudentRemedialRepository(),
            student_profile_repo=DjangoStudentProfileRepository(),
            task_repo=DjangoTaskSelectionRepository(),
            task_group_repo=DjangoRemedialTaskGroupRepository(),
            remedial_source_repo=DjangoRemedialSourceRepository(),
        )

        selection = service.select_tasks_for_student(
            student_id=str(self.student.pk),
            event_id=str(self.event.pk),
            mark_score=2,
        )

        self.assertEqual(selection.student_id, str(self.student.pk))
        self.assertEqual(selection.task_ids, [str(self.replacement.pk)])
        self.assertEqual(selection.weak_group_ids, {str(self.weak_group.pk)})
        self.assertEqual(selection.target_difficulty, 3)

    def test_student_repository_returns_task_level_mark_results(self):
        weak_variant_task = VariantTask.objects.get(
            variant=self.source_variant,
            task=self.original_weak,
        )
        ok_variant_task = VariantTask.objects.get(
            variant=self.source_variant,
            task=self.original_ok,
        )
        self.mark.task_scores = {
            str(self.original_weak.pk): {'points': 0, 'max_points': 2},
            str(ok_variant_task.pk): {
                'task_id': str(self.original_ok.pk),
                'points': 5,
                'max_points': 5,
            },
        }
        self.mark.save()
        capture_attempt_snapshot(self.mark)
        self.mark.task_scores = {}
        self.mark.save(update_fields=['task_scores'])

        results = StudentTaskResultService().build(
            DjangoStudentRemedialRepository().get_task_results_source_for_event(
                student_id=str(self.student.pk),
                event_id=str(self.event.pk),
            ),
        )
        result_by_task = {result.task_id: result for result in results}

        weak_result = result_by_task[str(self.original_weak.pk)]
        self.assertEqual(weak_result.points, 0)
        self.assertEqual(weak_result.max_points, 2)
        self.assertEqual(weak_result.group_id, str(self.weak_group.pk))
        self.assertEqual(weak_result.group_name, self.weak_group.name)
        self.assertEqual(
            weak_result.variant_task_id,
            str(weak_variant_task.pk),
        )
        self.assertEqual(result_by_task[str(self.original_ok.pk)].points, 5)
        self.assertEqual(
            result_by_task[str(self.original_ok.pk)].variant_task_id,
            str(ok_variant_task.pk),
        )

    def test_student_results_ignore_non_assessable_legacy_scores(self):
        demo_variant_task = VariantTask.objects.get(
            variant=self.source_variant,
            task=self.original_ok,
        )
        demo_variant_task.is_assessable = False
        demo_variant_task.save(update_fields=['is_assessable'])
        capture_attempt_snapshot(self.mark)

        results = StudentTaskResultService().build(
            DjangoStudentRemedialRepository().get_task_results_source_for_event(
                student_id=str(self.student.pk),
                event_id=str(self.event.pk),
            ),
        )

        self.assertEqual(
            [result.task_id for result in results],
            [str(self.original_weak.pk)],
        )

    def test_student_repository_returns_profile_data(self):
        original_event_name = self.event.name
        original_work_name = self.source_work.name
        self.mark.score = 5
        self.mark.points = 7
        self.mark.save(update_fields=['score', 'points'])
        self.event.name = 'Изменённое событие'
        self.event.save(update_fields=['name'])
        self.source_work.name = 'Изменённая работа'
        self.source_work.save(update_fields=['name'])
        student_repo = DjangoStudentRepository()
        learning_repo = DjangoStudentProfileRepository()

        groups = student_repo.get_student_groups(str(self.student.pk))
        participations = learning_repo.get_profile_participations(
            str(self.student.pk),
        )
        task_logs = learning_repo.get_task_logs(str(self.student.pk))
        work_groups = learning_repo.get_work_group_refs(
            [str(self.source_work.pk)],
        )

        self.assertEqual(groups[0].name, '9Б')
        self.assertEqual(participations[0].event.name, original_event_name)
        self.assertEqual(participations[0].work.name, original_work_name)
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

    def test_student_repository_returns_list_page_data(self):
        repo = DjangoStudentRepository()

        students = repo.get_list_students()
        student_groups = repo.get_list_student_groups()

        self.assertEqual(students[0].pk, str(self.student.pk))
        self.assertEqual(students[0].last_name, self.student.last_name)
        self.assertEqual(students[0].first_name, self.student.first_name)
        self.assertEqual(students[0].email, self.student.email)
        self.assertEqual(student_groups[0].pk, str(self.group.pk))
        self.assertEqual(student_groups[0].name, self.group.name)
        self.assertEqual(student_groups[0].short_uuid, self.group.get_short_uuid())
        self.assertEqual(student_groups[0].students_count, 1)

    def test_student_repository_filters_list_page_data_by_academic_year(self):
        year_2026 = AcademicYear.objects.create(
            name='2026-2027',
            start_date=dt.date(2026, 9, 1),
            end_date=dt.date(2027, 8, 31),
            is_active=True,
        )
        year_2027 = AcademicYear.objects.create(
            name='2027-2028',
            start_date=dt.date(2027, 9, 1),
            end_date=dt.date(2028, 8, 31),
        )
        group_2026 = StudentGroup.objects.create(
            name='8А',
            academic_year=year_2026,
        )
        group_2027 = StudentGroup.objects.create(
            name='8А',
            academic_year=year_2027,
        )
        student_2026 = Student.objects.create(
            last_name='Иванов',
            first_name='Иван',
        )
        student_2027 = Student.objects.create(
            last_name='Петров',
            first_name='Пётр',
        )
        group_2026.students.add(student_2026)
        group_2027.students.add(student_2027)
        repo = DjangoStudentRepository()

        students = repo.get_list_students(year=year_2026)
        groups = repo.get_list_student_groups(year=year_2026)

        self.assertEqual([student.pk for student in students], [str(student_2026.pk)])
        self.assertEqual([group.pk for group in groups], [str(group_2026.pk)])

    def test_student_repository_returns_detail_page_objects(self):
        repo = DjangoStudentRepository()

        student = repo.get_student(str(self.student.pk))
        missing_student = repo.get_student(
            '00000000-0000-0000-0000-000000000000',
        )
        student_group = repo.get_student_group(str(self.group.pk))
        missing_student_group = repo.get_student_group(
            '00000000-0000-0000-0000-000000000000',
        )

        self.assertEqual(student.pk, str(self.student.pk))
        self.assertEqual(student.first_name, self.student.first_name)
        self.assertEqual(student.last_name, self.student.last_name)
        self.assertEqual(student.email, self.student.email)
        self.assertEqual(student.short_uuid, self.student.get_short_uuid())
        self.assertEqual(student.full_name, self.student.get_full_name())
        self.assertEqual(student.short_name, self.student.get_short_name())
        self.assertIsNone(missing_student)
        self.assertEqual(student_group.pk, str(self.group.pk))
        self.assertEqual(student_group.name, self.group.name)
        self.assertEqual(student_group.students[0].pk, str(self.student.pk))
        self.assertEqual(student_group.students[0].last_name, self.student.last_name)
        self.assertIsNone(missing_student_group)

    def test_event_repository_creates_and_updates_event(self):
        repo = DjangoEventWriteRepository()
        course = Course.objects.create(
            name='Механика',
            subject='Физика',
            grade_level=9,
        )
        planned_date = timezone.make_aware(
            dt.datetime.combine(dt.date(2026, 3, 10), dt.time(9, 0)),
        )

        event_id = repo.create_event(
            CreateEventParams(
                name='Новая КР',
                work_id=str(self.source_work.pk),
                date=planned_date,
                status='planned',
                course_id=str(course.pk),
                description='Описание',
                location='101',
            )
        )
        updated = repo.update_event(
            CreateEventParams(
                event_id=event_id,
                name='Новая КР исправленная',
                work_id=str(self.source_work.pk),
                date=planned_date,
                status='completed',
                course_id=str(course.pk),
                description='Новое описание',
                location='202',
            )
        )
        missing_updated = repo.update_event(
            CreateEventParams(
                event_id='00000000-0000-0000-0000-000000000000',
                name='Нет',
                work_id=str(self.source_work.pk),
            )
        )

        event = Event.objects.get(pk=event_id)
        self.assertTrue(updated)
        self.assertFalse(missing_updated)
        self.assertEqual(event.name, 'Новая КР исправленная')
        self.assertEqual(event.status, 'completed')
        self.assertEqual(event.course, course)
        self.assertEqual(event.description, 'Новое описание')
        self.assertEqual(event.location, '202')

    def test_work_repository_returns_update_lock_context(self):
        repo = DjangoWorkSpecificationRepository()

        context = repo.get_work_update_context(str(self.source_work.pk))
        missing = repo.get_work_update_context(
            '00000000-0000-0000-0000-000000000000',
        )

        self.assertEqual(context.work_id, str(self.source_work.pk))
        self.assertTrue(context.has_variants)
        self.assertTrue(context.has_events)
        self.assertTrue(context.assessment_mode_locked)
        self.assertIsNone(missing)

    def test_work_repository_updates_work_and_content_plan_together(self):
        work = Work.objects.create(name='Черновик')
        old_group = AnalogGroup.objects.create(name='Старая тема')
        new_group = AnalogGroup.objects.create(name='Новая тема')
        WorkAnalogGroup.objects.create(
            work=work,
            analog_group=old_group,
            order=10,
        )

        updated = DjangoWorkSpecificationRepository().update_work_with_specification(
            CreateWorkWithSpecificationParams(
                work=CreateWorkParams(
                    work_id=str(work.pk),
                    name='Готовая работа',
                    work_type='quiz',
                    duration=35,
                    max_score=8,
                ),
                specs=[
                    WorkTaskSelectionParams(
                        analog_group_id=str(new_group.pk),
                        order=20,
                        count=2,
                        weight=4,
                    ),
                ],
                content_blocks=[
                    WorkContentBlockParams(
                        content_type='text',
                        order=10,
                        title='Инструкция',
                        body='Покажите ход решения.',
                    ),
                ],
            ),
        )

        self.assertTrue(updated)
        work.refresh_from_db()
        spec = WorkAnalogGroup.objects.get(work=work)
        block = WorkContentBlock.objects.get(work=work)
        self.assertEqual(work.name, 'Готовая работа')
        self.assertEqual(work.work_type, 'quiz')
        self.assertEqual(work.duration, 35)
        self.assertEqual(work.max_score, 8)
        self.assertEqual(spec.analog_group, new_group)
        self.assertEqual(spec.count, 2)
        self.assertEqual(block.body, 'Покажите ход решения.')

    def test_work_repository_creates_work_with_variants(self):
        repo = DjangoWorkVariantCreationRepository()

        created = repo.create_work_with_variants(
            CreateWorkWithVariantsParams(
                work=CreateWorkParams(
                    name='Работа над ошибками',
                    work_type='remedial',
                    max_score=5,
                    variant_counter=2,
                ),
                variants=[
                    NewWorkVariantParams(
                        student_id=str(self.student.pk),
                        plan=build_remedial_variant_creation_plan(
                            task_ids=[str(self.original_weak.pk)],
                            tasks=[self.original_weak],
                            number=1,
                            work_name='Работа над ошибками',
                            content_blocks=[
                                VariantContentBlockCreationPlan(
                                    source_content_id='content-1',
                                    content_type='text',
                                    order=0,
                                    title='Памятка',
                                    content={
                                        'body': 'Проверьте вычисления.',
                                    },
                                ),
                            ],
                        ),
                        source_work_id=str(self.source_work.pk),
                    ),
                    NewWorkVariantParams(
                        student_id=str(self.student.pk),
                        plan=build_remedial_variant_creation_plan(
                            task_ids=[str(self.original_ok.pk)],
                            tasks=[self.original_ok],
                            number=2,
                            work_name='Работа над ошибками',
                        ),
                    ),
                ],
            )
        )

        work = Work.objects.get(pk=created.work_id)
        variants = list(
            Variant.objects.filter(work=work).order_by('number')
        )
        variant_tasks = list(
            VariantTask.objects.filter(variant__work=work).order_by(
                'variant__number',
                'order',
            )
        )

        self.assertEqual(len(created.variant_ids), 2)
        self.assertEqual(work.variant_counter, 2)
        self.assertEqual(
            [str(variant.pk) for variant in variants],
            created.variant_ids,
        )
        self.assertEqual(
            [variant.max_score_snapshot for variant in variants],
            [2, 5],
        )
        self.assertEqual(variants[0].source_work, self.source_work)
        self.assertEqual(
            [variant_task.task for variant_task in variant_tasks],
            [self.original_weak, self.original_ok],
        )
        content_snapshot = VariantContentBlockSnapshot.objects.get(
            variant=variants[0],
        )
        self.assertEqual(content_snapshot.title, 'Памятка')
        self.assertEqual(
            content_snapshot.content,
            {'body': 'Проверьте вычисления.'},
        )
        self.assertFalse(
            VariantContentBlockSnapshot.objects.filter(
                variant=variants[1],
            ).exists()
        )

    def test_work_repository_rolls_back_work_when_variant_creation_fails(self):
        repo = DjangoWorkVariantCreationRepository()
        original_create_variant = repo._create_variant_from_plan
        work_count = Work.objects.count()
        variant_count = Variant.objects.count()

        def create_variant_or_fail(params):
            if params.plan.number == 2:
                raise RuntimeError('variant creation failed')
            return original_create_variant(params)

        repo._create_variant_from_plan = create_variant_or_fail

        with self.assertRaises(RuntimeError):
            repo.create_work_with_variants(
                CreateWorkWithVariantsParams(
                    work=CreateWorkParams(
                        name='Незавершённая работа',
                        work_type='remedial',
                        variant_counter=2,
                    ),
                    variants=[
                        NewWorkVariantParams(
                            student_id=str(self.student.pk),
                            plan=build_remedial_variant_creation_plan(
                                task_ids=[str(self.original_weak.pk)],
                                tasks=[self.original_weak],
                                number=1,
                                work_name='Незавершённая работа',
                            ),
                        ),
                        NewWorkVariantParams(
                            student_id=str(self.student.pk),
                            plan=build_remedial_variant_creation_plan(
                                task_ids=[str(self.original_ok.pk)],
                                tasks=[self.original_ok],
                                number=2,
                                work_name='Незавершённая работа',
                            ),
                        ),
                    ],
                )
            )

        self.assertEqual(Work.objects.count(), work_count)
        self.assertEqual(Variant.objects.count(), variant_count)

    def test_work_repository_creates_work_with_specification(self):
        group = AnalogGroup.objects.create(name='Спецификация новой работы')
        topic = Topic.objects.create(
            name='Энергия',
            subject='Физика',
            section='Механика',
            grade_level=8,
            description='Энергия характеризует способность совершать работу.',
        )

        work_id = DjangoWorkSpecificationRepository().create_work_with_specification(
            CreateWorkWithSpecificationParams(
                work=CreateWorkParams(
                    name='Работа со спецификацией',
                    work_type='practice',
                    duration=35,
                    max_score=6,
                ),
                specs=[
                    WorkTaskSelectionParams(
                        analog_group_id=str(group.pk),
                        order=1,
                        count=2,
                        weight=3,
                    ),
                ],
                content_blocks=[
                    WorkContentBlockParams(
                        content_type='theory',
                        order=10,
                        title='Теория',
                        topic_ids=[str(topic.pk)],
                    ),
                    WorkContentBlockParams(
                        content_type='text',
                        order=30,
                        title='Инструкция',
                        body='Покажите вычисления.',
                    ),
                ],
            )
        )

        work = Work.objects.get(pk=work_id)
        spec = WorkAnalogGroup.objects.get(work=work)
        self.assertEqual(work.name, 'Работа со спецификацией')
        self.assertEqual(work.work_type, 'practice')
        self.assertEqual(work.duration, 35)
        self.assertEqual(spec.analog_group, group)
        self.assertEqual(spec.count, 2)
        self.assertEqual(spec.weight, 3)
        content_blocks = list(work.content_blocks.order_by('order'))
        self.assertEqual(
            [block.content_type for block in content_blocks],
            ['theory', 'text'],
        )
        self.assertEqual(
            list(content_blocks[0].topics.values_list('pk', flat=True)),
            [topic.pk],
        )
        self.assertEqual(content_blocks[1].body, 'Покажите вычисления.')

    def test_student_repository_creates_and_updates_student(self):
        repo = DjangoStudentRepository()

        create_result = repo.create_student(
            SaveStudentParams(
                first_name='Пётр',
                last_name='Петров',
                middle_name='Петрович',
                email='petrov@example.test',
            )
        )
        update_result = repo.update_student(
            SaveStudentParams(
                student_id=create_result.student_id,
                first_name='Павел',
                last_name='Петров',
                middle_name='',
                email='pavel@example.test',
            )
        )
        missing_result = repo.update_student(
            SaveStudentParams(
                student_id='00000000-0000-0000-0000-000000000000',
                first_name='Нет',
                last_name='Такого',
            )
        )

        student = Student.objects.get(pk=create_result.student_id)
        self.assertEqual(create_result.status, 'created')
        self.assertEqual(update_result.status, 'updated')
        self.assertEqual(student.first_name, 'Павел')
        self.assertEqual(student.email, 'pavel@example.test')
        self.assertEqual(missing_result.status, 'not_found')

    def test_student_repository_creates_and_updates_student_group(self):
        repo = DjangoStudentRepository()
        second_student = Student.objects.create(
            first_name='Пётр',
            last_name='Петров',
        )

        create_result = repo.create_student_group(
            SaveStudentGroupParams(
                name='10А',
                student_ids=[str(self.student.pk)],
            )
        )
        update_result = repo.update_student_group(
            SaveStudentGroupParams(
                group_id=create_result.group_id,
                name='10Б',
                student_ids=[str(second_student.pk)],
            )
        )
        missing_result = repo.update_student_group(
            SaveStudentGroupParams(
                group_id='00000000-0000-0000-0000-000000000000',
                name='Нет',
            )
        )

        group = StudentGroup.objects.get(pk=create_result.group_id)
        self.assertEqual(create_result.status, 'created')
        self.assertEqual(update_result.status, 'updated')
        self.assertEqual(group.name, '10Б')
        self.assertEqual(list(group.students.all()), [second_student])
        self.assertEqual(missing_result.status, 'not_found')

    def test_task_repository_returns_filtered_task_list_data(self):
        repo = DjangoTaskReadRepository()

        grouped_tasks = repo.get_list_tasks(
            TaskListFilters(
                search='слабое',
                topic_id=str(self.topic.pk),
                group_filter='has_group',
                analog_group_id=str(self.weak_group.pk),
                verified='0',
            )
        )
        ungrouped_tasks = repo.get_list_tasks(TaskListFilters(group_filter='no_group'))

        self.assertEqual(grouped_tasks[0].pk, str(self.original_weak.pk))
        self.assertEqual(grouped_tasks[0].text, self.original_weak.text)
        self.assertEqual(grouped_tasks[0].topic_name, self.topic.name)
        self.assertEqual(grouped_tasks[0].task_type_display, self.original_weak.get_task_type_display())
        self.assertEqual(grouped_tasks[0].difficulty_display, self.original_weak.get_difficulty_display())
        self.assertTrue(grouped_tasks[0].has_group)
        self.assertEqual(grouped_tasks[0].group_count, 1)
        self.assertEqual(list(ungrouped_tasks), [])
        self.assertEqual(repo.count_tasks(), 4)
        self.assertEqual(repo.count_ungrouped_tasks(), 0)
        task_catalog = DjangoTaskCatalogRepository()
        self.assertEqual(list(task_catalog.get_subtopics_for_topic('')), [])
        self.assertIn(
            str(self.topic.pk),
            [option.pk for option in task_catalog.get_list_topics()],
        )
        self.assertIn(
            str(self.weak_group.pk),
            [
                option.pk
                for option in DjangoTaskGroupRepository().get_list_analog_groups()
            ],
        )

    def test_task_repository_uses_injected_math_status_filter(self):
        math_status_cache = Mock()
        math_status_cache.get_tasks_with_math_ids.return_value = {
            self.original_weak.pk,
        }
        math_status_cache.get_tasks_with_errors_ids.return_value = {
            self.original_ok.pk,
        }
        repo = DjangoTaskReadRepository(math_status_cache=math_status_cache)

        with_math = repo.get_list_tasks(
            TaskListFilters(math_filter='with_math')
        )
        with_errors = repo.get_list_tasks(
            TaskListFilters(math_filter='with_errors')
        )

        self.assertEqual([task.pk for task in with_math], [
            str(self.original_weak.pk),
        ])
        self.assertEqual([task.pk for task in with_errors], [
            str(self.original_ok.pk),
        ])
        math_status_cache.get_tasks_with_math_ids.assert_called_once_with()
        math_status_cache.get_tasks_with_errors_ids.assert_called_once_with()

    def test_task_group_repository_returns_filtered_list_data(self):
        repo = DjangoTaskGroupRepository()

        groups = repo.get_list_task_groups(
            TaskGroupListFilters(
                search='Ньют',
                topic_id=str(self.topic.pk),
                difficulty='2',
                group_filter='nonempty',
                sort='tasks_desc',
                min_tasks='1',
                max_tasks='3',
            )
        )
        empty_groups = repo.get_list_task_groups(
            TaskGroupListFilters(group_filter='empty')
        )

        self.assertEqual(groups[0].pk, str(self.weak_group.pk))
        self.assertEqual(groups[0].name, self.weak_group.name)
        self.assertEqual(groups[0].task_count, 3)
        self.assertEqual(groups[0].sample_task_text, self.original_weak.text)
        self.assertEqual(list(empty_groups), [])
        self.assertEqual(repo.count_analog_groups(), 2)
        self.assertEqual(repo.count_empty_analog_groups(), 0)
        self.assertEqual(repo.count_task_group_memberships(), 4)

    def test_task_group_repository_returns_detail_data(self):
        repo = DjangoTaskGroupRepository()

        group = repo.get_analog_group_detail(str(self.weak_group.pk))
        missing_group = repo.get_analog_group_detail(
            '00000000-0000-0000-0000-000000000000',
        )
        tasks = repo.get_task_group_detail_tasks(str(self.weak_group.pk))

        self.assertEqual(group.pk, str(self.weak_group.pk))
        self.assertEqual(group.name, self.weak_group.name)
        self.assertIsNone(missing_group)
        self.assertEqual(len(tasks), 3)
        self.assertEqual(tasks[0].topic, str(self.topic))
        self.assertEqual(tasks[0].task_type_display, 'Расчётная задача')

    def test_task_group_repository_returns_add_tasks_form_data(self):
        repo = DjangoTaskGroupRepository()

        group = repo.get_analog_group_detail(str(self.weak_group.pk))
        available_tasks = repo.get_available_tasks_for_analog_group(
            group_id=str(self.weak_group.pk),
            search='сильное',
        )

        self.assertEqual(group.pk, str(self.weak_group.pk))
        self.assertEqual(group.name, self.weak_group.name)
        self.assertEqual(available_tasks[0].pk, str(self.original_ok.pk))
        self.assertEqual(available_tasks[0].text, self.original_ok.text)
        self.assertEqual(
            available_tasks[0].task_type_display,
            self.original_ok.get_task_type_display(),
        )
        self.assertIsNone(
            repo.get_analog_group_detail(
                '00000000-0000-0000-0000-000000000000',
            )
        )

    def test_task_repository_returns_detail_and_reference_data(self):
        repo = DjangoTaskReadRepository()

        detail_task = repo.get_task(str(self.original_weak.pk))
        missing_task = repo.get_task('00000000-0000-0000-0000-000000000000')
        task_groups = repo.get_task_detail_groups(str(self.original_weak.pk))
        task_catalog = DjangoTaskCatalogRepository()
        subtopics = task_catalog.get_subtopic_options(str(self.topic.pk))
        missing_subtopics = task_catalog.get_subtopic_options(
            '00000000-0000-0000-0000-000000000000',
        )

        self.assertEqual(detail_task.pk, str(self.original_weak.pk))
        self.assertEqual(detail_task.topic, str(self.topic))
        self.assertEqual(detail_task.text, self.original_weak.text)
        self.assertEqual(detail_task.task_type_display, 'Расчётная задача')
        self.assertEqual(detail_task.created_at, self.original_weak.created_at)
        self.assertIsNone(missing_task)
        self.assertEqual(task_groups[0].pk, str(self.weak_group.pk))
        self.assertEqual(task_groups[0].name, self.weak_group.name)
        self.assertEqual(subtopics[0].id, str(self.subtopic.pk))
        self.assertEqual(subtopics[0].name, self.subtopic.name)
        self.assertEqual(missing_subtopics, [])

    def test_source_repository_returns_list_with_task_count(self):
        source = Source.objects.create(name='Сборник задач')
        self.original_weak.source = source
        self.original_weak.save()
        repo = DjangoSourceRepository()

        sources = repo.get_source_list_sources()

        self.assertEqual(sources[0].pk, str(source.pk))
        self.assertEqual(sources[0].name, source.name)
        self.assertEqual(sources[0].source_type_display, source.get_source_type_display())
        self.assertEqual(sources[0].task_count, 1)

    def test_source_repository_creates_source(self):
        repo = DjangoSourceRepository()

        result = repo.create_source(
            SourceCreateParams(
                name='Сборник задач',
                short_name='Сборник',
                source_type='problem_book',
                author='Автор',
                year=2026,
                url='https://example.test',
                isbn='123',
                notes='Заметки',
            )
        )

        source = Source.objects.get(pk=result.pk)
        self.assertEqual(result.display_name, 'Сборник')
        self.assertEqual(source.name, 'Сборник задач')
        self.assertEqual(source.source_type, 'problem_book')
        self.assertEqual(source.year, 2026)

    def test_task_repository_creates_and_updates_task(self):
        repo = DjangoTaskWriteRepository()

        create_result = repo.create_task(
            TaskSaveParams(
                text='Новая задача',
                answer='Ответ',
                topic_id=str(self.topic.pk),
                task_type='computational',
                difficulty=2,
                cognitive_level='apply',
                short_solution='Кратко',
                source_detail='стр. 10',
                grade=9,
                is_verified=True,
            )
        )
        update_result = repo.update_task(
            TaskSaveParams(
                task_id=create_result.task_id,
                text='Обновлённая задача',
                answer='Новый ответ',
                topic_id=str(self.topic.pk),
                task_type='theoretical',
                difficulty=3,
                cognitive_level='understand',
                teacher_notes='Проверить',
            )
        )
        missing_result = repo.update_task(
            TaskSaveParams(
                task_id='00000000-0000-0000-0000-000000000000',
                text='Нет',
                answer='Нет',
                topic_id=str(self.topic.pk),
                task_type='computational',
                difficulty=1,
            )
        )

        task = Task.objects.get(pk=create_result.task_id)
        self.assertEqual(create_result.status, 'created')
        self.assertEqual(update_result.status, 'updated')
        self.assertEqual(task.text, 'Обновлённая задача')
        self.assertEqual(task.answer, 'Новый ответ')
        self.assertEqual(task.task_type, 'theoretical')
        self.assertEqual(task.difficulty, 3)
        self.assertEqual(task.teacher_notes, 'Проверить')
        self.assertEqual(missing_result.status, 'not_found')

    def test_task_repository_saves_task_images(self):
        repo = DjangoTaskWriteRepository()
        task = Task.objects.create(
            text='Задача с рисунком',
            answer='Ответ',
            topic=self.topic,
            task_type='computational',
            difficulty=2,
        )

        create_result = repo.save_task_images(
            task_id=str(task.pk),
            images=[
                TaskImageSaveParams(
                    image=SimpleUploadedFile(
                        'task.png',
                        b'file-content',
                        content_type='image/png',
                    ),
                    position='bottom_70',
                    caption='Рисунок',
                    order=1,
                )
            ],
        )
        image = TaskImage.objects.get(task=task)
        update_result = repo.save_task_images(
            task_id=str(task.pk),
            images=[
                TaskImageSaveParams(
                    image_id=str(image.pk),
                    image=image.image,
                    position='right_40',
                    caption='Обновлённый рисунок',
                    order=2,
                )
            ],
        )
        image.refresh_from_db()
        delete_result = repo.save_task_images(
            task_id=str(task.pk),
            images=[TaskImageSaveParams(image_id=str(image.pk), delete=True)],
        )
        missing_result = repo.save_task_images(
            task_id='00000000-0000-0000-0000-000000000000',
            images=[],
        )

        self.assertEqual(create_result.status, 'saved')
        self.assertEqual(create_result.created_images, 1)
        self.assertEqual(update_result.status, 'saved')
        self.assertEqual(image.position, 'right_40')
        self.assertEqual(image.caption, 'Обновлённый рисунок')
        self.assertEqual(image.order, 2)
        self.assertEqual(delete_result.deleted_images, 1)
        self.assertFalse(TaskImage.objects.filter(pk=image.pk).exists())
        self.assertEqual(missing_result.status, 'not_found')

    def test_task_export_repository_builds_payload(self):
        source = Source.objects.create(
            name='Сборник задач',
            short_name='Сборник',
            source_type='problem_book',
            author='Автор',
            year=2026,
            url='https://example.test/book',
            isbn='123',
        )
        self.original_weak.source = source
        self.original_weak.source_detail = 'стр. 1'
        self.original_weak.save()
        repo = DjangoTaskExportRepository()

        payload = ExportTasksUseCase(repo).execute(ExportTasksRequest(
            filters=TaskExportFilters(topic_id=str(self.topic.pk)),
            export_date='2026-07-17',
        )).payload
        tasks_by_id = {task['id']: task for task in payload['tasks']}
        weak_task = tasks_by_id[str(self.original_weak.pk)]

        self.assertEqual(payload['version'], '1.2')
        self.assertEqual(payload['export_date'], '2026-07-17')
        self.assertEqual(weak_task['text'], self.original_weak.text)
        self.assertEqual(weak_task['source']['short_name'], 'Сборник')
        self.assertEqual(weak_task['source_detail'], 'стр. 1')
        self.assertIn(
            {
                'id': str(self.weak_group.pk),
                'bank_role': 'control',
            },
            weak_task['groups'],
        )
        self.assertIn(
            {
                'id': str(self.weak_group.pk),
                'name': self.weak_group.name,
                'description': '',
                'difficulty': self.weak_group.difficulty,
            },
            payload['analog_groups'],
        )
        self.assertIn(
            {
                'id': str(source.pk),
                'name': source.name,
                'short_name': source.short_name,
                'source_type': source.source_type,
                'author': source.author,
                'year': source.year,
                'url': source.url,
                'isbn': source.isbn,
            },
            payload['sources'],
        )

    def test_task_repository_deletes_task(self):
        repo = DjangoTaskWriteRepository()
        task_id = str(self.too_hard.pk)

        deleted_count = repo.delete_task(task_id)

        self.assertEqual(deleted_count, 1)
        self.assertFalse(Task.objects.filter(pk=task_id).exists())

    def test_core_repository_returns_import_logs(self):
        first = ImportLog.objects.create(filename='first.json')
        second = ImportLog.objects.create(
            filename='second.json',
            status=ImportLog.Status.SUCCESS,
            duration_ms=1500,
            file_size=1536,
        )
        repo = DjangoCoreRepository()

        recent_logs = list(repo.get_recent_import_logs(limit=1))
        import_logs = list(repo.get_import_logs())

        self.assertEqual(recent_logs[0].filename, second.filename)
        self.assertEqual(import_logs[0].filename, second.filename)
        self.assertEqual(import_logs[1].filename, first.filename)
        self.assertEqual(import_logs[0].mode_display, second.get_mode_display())
        self.assertEqual(import_logs[0].status_icon, '✅')
        self.assertEqual(import_logs[0].duration_human, '1.5 с')
        self.assertEqual(import_logs[0].file_size_human, '1.5 КБ')

    def test_create_remedial_use_case_creates_django_objects(self):
        source_attempt = capture_attempt_snapshot(self.mark)
        student_repo = DjangoStudentRepository()
        task_repo = DjangoTaskSelectionRepository()
        work_repo = DjangoWorkVariantCreationRepository()
        event_repo = DjangoEventReadRepository()
        event_write_repo = DjangoEventWriteRepository()
        event_participation_repo = DjangoEventParticipationRepository()
        service = RemedialService(
            student_remedial_repo=DjangoStudentRemedialRepository(),
            student_profile_repo=DjangoStudentProfileRepository(),
            task_repo=task_repo,
            task_group_repo=DjangoRemedialTaskGroupRepository(),
            remedial_source_repo=DjangoRemedialSourceRepository(),
        )
        use_case = CreateRemedialFromEventUseCase(
            remedial_service=service,
            task_repo=task_repo,
            work_repo=work_repo,
            event_repo=event_repo,
            event_write_repo=event_write_repo,
            event_participation_repo=event_participation_repo,
            event_attempt_repo=DjangoEventAttemptRepository(),
            transaction_manager=DjangoTransactionManager(),
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
        self.assertEqual(
            remedial_variant.source_participation,
            self.participation,
        )
        self.assertEqual(
            remedial_variant.source_attempt_snapshot,
            source_attempt,
        )
        self.assertEqual(remedial_variant.max_score_snapshot, self.replacement.difficulty)
        self.assertEqual(remedial_event.status, 'planned')
        self.assertEqual(remedial_event.description, f'Работа над ошибками по: {self.source_work.name}')
        self.assertEqual(participation.variant, remedial_variant)
        self.assertEqual(participation.status, 'assigned')

        variant_task = VariantTask.objects.get(variant=remedial_variant)
        self.assertEqual(variant_task.task, self.replacement)
        self.assertEqual(variant_task.max_points, self.replacement.difficulty)
        self.assertEqual(variant_task.weight, self.replacement.difficulty)
        self.assertEqual(variant_task.order, 1)
        self.assertEqual(variant_task.content_order, 1)
        self.assertEqual(variant_task.bank_role, TASK_BANK_ROLE_REMEDIAL)
        self.assertTrue(variant_task.is_assessable)

    def test_remedial_transaction_rolls_back_work_when_participation_fails(self):
        capture_attempt_snapshot(self.mark)
        student_repo = DjangoStudentRepository()
        task_repo = DjangoTaskSelectionRepository()
        work_repo = DjangoWorkVariantCreationRepository()
        event_repo = DjangoEventReadRepository()
        event_write_repo = DjangoEventWriteRepository()
        event_participation_repo = DjangoEventParticipationRepository()
        service = RemedialService(
            student_remedial_repo=DjangoStudentRemedialRepository(),
            student_profile_repo=DjangoStudentProfileRepository(),
            task_repo=task_repo,
            task_group_repo=DjangoRemedialTaskGroupRepository(),
            remedial_source_repo=DjangoRemedialSourceRepository(),
        )

        def fail_participation(**kwargs):
            raise RuntimeError('participation creation failed')

        event_participation_repo.create_participation = fail_participation
        use_case = CreateRemedialFromEventUseCase(
            remedial_service=service,
            task_repo=task_repo,
            work_repo=work_repo,
            event_repo=event_repo,
            event_write_repo=event_write_repo,
            event_participation_repo=event_participation_repo,
            event_attempt_repo=DjangoEventAttemptRepository(),
            transaction_manager=DjangoTransactionManager(),
        )
        work_name = 'Откатываемая работа над ошибками'

        with self.assertRaises(RuntimeError):
            use_case.execute(
                RemedialFromEventRequest(
                    event_id=str(self.event.pk),
                    selected_student_ids=[str(self.student.pk)],
                    work_name=work_name,
                    create_event=True,
                    event_date='2026-03-10',
                )
            )

        self.assertFalse(Work.objects.filter(name=work_name).exists())
        self.assertFalse(Event.objects.filter(name=work_name).exists())

    def test_work_repository_returns_personal_remedial_variant_ids_for_work(
        self,
    ):
        remedial_work = Work.objects.create(
            name='Работа над ошибками',
            work_type='remedial',
        )
        first_student = Student.objects.create(
            last_name='Иванов',
            first_name='Иван',
        )
        second_student = Student.objects.create(
            last_name='Петров',
            first_name='Пётр',
        )
        second_variant = Variant.objects.create(
            work=remedial_work,
            number=2,
            work_name_snapshot=remedial_work.name,
            variant_type='remedial',
            assigned_student=second_student,
        )
        first_variant = Variant.objects.create(
            work=remedial_work,
            number=1,
            work_name_snapshot=remedial_work.name,
            variant_type='remedial',
            assigned_student=first_student,
        )
        participation_variant = Variant.objects.create(
            work=remedial_work,
            number=3,
            work_name_snapshot=remedial_work.name,
            variant_type='remedial',
            source_participation=self.participation,
        )
        Variant.objects.create(
            work=remedial_work,
            number=4,
            work_name_snapshot=remedial_work.name,
            variant_type='regular',
        )
        Variant.objects.create(
            work=remedial_work,
            number=5,
            work_name_snapshot=remedial_work.name,
            variant_type='remedial',
        )

        variant_ids = (
            DjangoRemedialSheetRepository()
            .get_work_personal_remedial_variant_ids(
                str(remedial_work.pk),
            )
        )

        self.assertEqual(
            variant_ids,
            [
                str(first_variant.pk),
                str(second_variant.pk),
                str(participation_variant.pk),
            ],
        )

    def test_work_repository_returns_variant_ids_for_work(self):
        work = Work.objects.create(name='Контрольная')
        second_variant = Variant.objects.create(
            work=work,
            number=2,
            work_name_snapshot=work.name,
        )
        first_variant = Variant.objects.create(
            work=work,
            number=1,
            work_name_snapshot=work.name,
        )

        variant_ids = DjangoWorkDocumentRepository().get_work_variant_ids(
            str(work.pk),
        )

        self.assertEqual(
            variant_ids,
            [str(first_variant.pk), str(second_variant.pk)],
        )

    def test_work_document_source_contains_ordered_immutable_variant_data(self):
        content_block = VariantContentBlockSnapshot.objects.create(
            variant=self.source_variant,
            source_content_id='theory-1',
            content_type='text',
            order=3,
            title='Памятка',
            content={'body': 'Проверьте единицы.'},
        )

        source = DjangoWorkDocumentRepository().get_work_document_source(
            str(self.source_work.pk),
        )

        self.assertEqual(source.pk, str(self.source_work.pk))
        self.assertEqual(source.name, self.source_work.name)
        self.assertEqual(len(source.score_spec_rows), 1)
        self.assertEqual(source.score_spec_rows[0].weight, 2)
        self.assertEqual(len(source.variants), 1)
        variant = source.variants[0]
        self.assertEqual(variant.pk, str(self.source_variant.pk))
        self.assertEqual(
            [task.task_id for task in variant.tasks],
            [str(self.original_weak.pk), str(self.original_ok.pk)],
        )
        self.assertEqual(
            variant.tasks[0].task_snapshot['text'],
            self.original_weak.text,
        )
        self.assertEqual(variant.content_blocks[0].pk, str(content_block.pk))
        self.assertEqual(
            variant.content_blocks[0].content,
            {'body': 'Проверьте единицы.'},
        )

    def test_work_document_source_returns_none_for_missing_work(self):
        source = DjangoWorkDocumentRepository().get_work_document_source(
            '00000000-0000-0000-0000-000000000000',
        )

        self.assertIsNone(source)

    def test_work_repository_returns_none_for_missing_remedial_sheet(self):
        sheet_data = DjangoRemedialSheetRepository().get_remedial_sheet_source(
            '00000000-0000-0000-0000-000000000000',
        )

        self.assertIsNone(sheet_data)

    def test_remedial_sheet_reads_original_tasks_from_attempt_snapshot(self):
        attempt = self.participation.attempt_snapshots.get(revision=1)
        variant_task = VariantTask.objects.get(
            variant=self.source_variant,
            task=self.original_weak,
        )
        changed_snapshot = dict(variant_task.task_snapshot)
        changed_snapshot['text'] = 'Изменёно после проверки'
        variant_task.task_snapshot = changed_snapshot
        variant_task.save(update_fields=['task_snapshot'])
        remedial_variant = Variant.objects.create(
            number=1,
            variant_type='remedial',
            assigned_student=self.student,
            source_work=self.source_work,
            source_participation=self.participation,
            source_attempt_snapshot=attempt,
        )

        source = DjangoRemedialSheetRepository().get_remedial_sheet_source(
            str(remedial_variant.pk),
        )

        original = next(
            row
            for row in source.original_tasks
            if row.task.pk == str(self.original_weak.pk)
        )
        self.assertEqual(original.task.text, self.original_weak.text)

    def test_remedial_sheet_uses_frozen_specification_block_name(self):
        attempt = self.participation.attempt_snapshots.get(revision=1)
        task_result = attempt.task_results.get(
            task_id_snapshot=str(self.original_weak.pk),
        )
        original_group_name = self.weak_group.name
        self.weak_group.name = 'Переименованная группа'
        self.weak_group.save(update_fields=['name'])
        remedial_variant = Variant.objects.create(
            number=1,
            variant_type='remedial',
            assigned_student=self.student,
            source_work=self.source_work,
            source_participation=self.participation,
            source_attempt_snapshot=attempt,
        )

        source = DjangoRemedialSheetRepository().get_remedial_sheet_source(
            str(remedial_variant.pk),
        )
        original = next(
            row
            for row in source.original_tasks
            if row.task.pk == str(self.original_weak.pk)
        )

        self.assertEqual(
            task_result.source_selection_name_snapshot,
            original_group_name,
        )
        self.assertEqual(original.group_name, original_group_name)

    def test_remedial_sheet_returns_frozen_content_blocks(self):
        remedial_work = Work.objects.create(
            name='Работа над ошибками',
            work_type='remedial',
        )
        remedial_variant = Variant.objects.create(
            work=remedial_work,
            number=1,
            variant_type='remedial',
            assigned_student=self.student,
        )
        content_block = VariantContentBlockSnapshot.objects.create(
            variant=remedial_variant,
            source_content_id='content-source-1',
            content_type='text',
            order=7,
            title='Памятка',
            content={'body': 'Проверьте вычисления.'},
        )

        sheet_data = GetRemedialSheetDataUseCase(
            DjangoRemedialSheetRepository(),
        ).execute(str(remedial_variant.pk))

        self.assertEqual(len(sheet_data.content_blocks), 1)
        self.assertEqual(
            sheet_data.content_blocks[0].pk,
            str(content_block.pk),
        )
        self.assertEqual(
            sheet_data.content_blocks[0].content,
            {'body': 'Проверьте вычисления.'},
        )

    def test_remedial_sheet_uses_exact_source_participation(self):
        second_source_variant = Variant.objects.create(
            work=self.source_work,
            number=2,
            work_name_snapshot=self.source_work.name,
        )
        create_variant_task(
            variant=second_source_variant,
            task=self.replacement,
            order=1,
            max_points=3,
        )
        second_event = Event.objects.create(
            name='Повторное проведение',
            work=self.source_work,
            planned_date=self.event.planned_date,
            status='graded',
        )
        second_participation = EventParticipation.objects.create(
            event=second_event,
            student=self.student,
            variant=second_source_variant,
            status='graded',
        )
        second_mark = Mark.objects.create(
            participation=second_participation,
            score=4,
            points=3,
            max_points=3,
            task_scores={
                str(self.replacement.pk): {
                    'points': 3,
                    'max_points': 3,
                },
            },
        )
        source_attempt = capture_attempt_snapshot(second_mark)
        second_mark.score = 2
        second_mark.points = 0
        second_mark.save(update_fields=['score', 'points'])
        remedial_work = Work.objects.create(
            name='РнО по повторной попытке',
            work_type='remedial',
        )
        remedial_variant = Variant.objects.create(
            work=remedial_work,
            number=1,
            variant_type='remedial',
            assigned_student=self.student,
            source_work=self.source_work,
            source_participation=second_participation,
            source_attempt_snapshot=source_attempt,
        )

        sheet_data = GetRemedialSheetDataUseCase(
            DjangoRemedialSheetRepository(),
        ).execute(str(remedial_variant.pk))

        self.assertEqual(sheet_data.mark.score, 4)
        self.assertEqual(sheet_data.mark.points, 3)
        self.assertEqual(
            sheet_data.original_tasks[0].task.pk,
            str(self.replacement.pk),
        )

    def test_work_repository_returns_detail_page_data(self):
        repo = DjangoWorkReadRepository()
        content_block = WorkContentBlock.objects.create(
            work=self.source_work,
            content_type='theory',
            order=2,
            title='Опорная теория',
            include_subtopics=True,
        )
        content_block.topics.add(self.topic)

        work = repo.get_work_detail(str(self.source_work.pk))
        missing_work = repo.get_work_detail(
            '550e8400-e29b-41d4-a716-446655440000',
        )
        variants = repo.get_detail_variants(str(self.source_work.pk))
        analog_groups = repo.get_detail_analog_groups(str(self.source_work.pk))
        content_blocks = repo.get_detail_content_blocks(
            str(self.source_work.pk),
        )

        self.assertEqual(work.pk, str(self.source_work.pk))
        self.assertEqual(work.name, self.source_work.name)
        self.assertIsNone(missing_work)
        self.assertEqual(len(variants), 1)
        self.assertEqual(variants[0].pk, str(self.source_variant.pk))
        self.assertEqual(analog_groups[0].analog_group.name, self.weak_group.name)
        self.assertEqual(content_blocks[0].content_type, 'theory')
        self.assertEqual(content_blocks[0].title, 'Опорная теория')
        self.assertEqual(content_blocks[0].topic_ids, (str(self.topic.pk),))
        self.assertTrue(content_blocks[0].include_subtopics)
        self.assertEqual(
            analog_groups[0].selection_id,
            str(
                WorkAnalogGroup.objects.get(
                    work=self.source_work,
                    analog_group=self.weak_group,
                ).pk
            ),
        )
        self.assertGreaterEqual(len(analog_groups[0].task_bank_roles), 1)

    def test_work_repository_returns_list_page_data(self):
        read_repo = DjangoWorkReadRepository()
        repo = DjangoVariantGenerationFormRepository()

        works = read_repo.get_list_works()
        work = repo.get_work_generation_target(str(self.source_work.pk))
        generation_groups = repo.get_variant_generation_group_sources(
            str(self.source_work.pk),
        )
        missing_work = repo.get_work_generation_target(
            '550e8400-e29b-41d4-a716-446655440000',
        )

        self.assertEqual(works[0].pk, str(self.source_work.pk))
        self.assertEqual(works[0].name, self.source_work.name)
        self.assertEqual(works[0].duration, self.source_work.duration)
        self.assertEqual(works[0].variant_count, 1)
        self.assertEqual(works[0].work_type, self.source_work.work_type)
        self.assertEqual(
            works[0].work_type_display,
            self.source_work.get_work_type_display(),
        )
        self.assertEqual(work.pk, str(self.source_work.pk))
        self.assertEqual(work.variant_counter, self.source_work.variant_counter)
        self.assertEqual(generation_groups[0].group_name, self.weak_group.name)
        self.assertEqual(len(generation_groups[0].task_bank_roles), 3)
        self.assertIsNone(missing_work)

    def test_work_repository_filters_list_page_data(self):
        remedial_work = Work.objects.create(
            name='Работа над ошибками',
            work_type='remedial',
        )
        empty_work = Work.objects.create(
            name='Пустая самостоятельная',
            work_type='quiz',
        )

        repo = DjangoWorkReadRepository()

        remedial_works = repo.get_list_works(
            WorkListFilters(work_type='remedial'),
        )
        non_remedial_works = repo.get_list_works(
            WorkListFilters(hide_remedial=True),
        )
        works_with_variants = repo.get_list_works(
            WorkListFilters(variant_status='with_variants'),
        )
        works_without_variants = repo.get_list_works(
            WorkListFilters(variant_status='without_variants'),
        )
        searched_works = repo.get_list_works(
            WorkListFilters(q='самостоятельная'),
        )

        self.assertEqual([work.pk for work in remedial_works], [str(remedial_work.pk)])
        self.assertNotIn(str(remedial_work.pk), [work.pk for work in non_remedial_works])
        self.assertIn(str(self.source_work.pk), [work.pk for work in works_with_variants])
        self.assertNotIn(str(empty_work.pk), [work.pk for work in works_with_variants])
        self.assertIn(str(empty_work.pk), [work.pk for work in works_without_variants])
        self.assertEqual([work.pk for work in searched_works], [str(empty_work.pk)])

    def test_curriculum_repository_returns_course_detail_data(self):
        course = Course.objects.create(
            name='Физика 9',
            subject='Физика',
            grade_level=9,
        )
        assignment = CourseAssignment.objects.create(
            course=course,
            work=self.source_work,
            order=1,
        )
        repo = DjangoCurriculumRepository()

        courses = repo.get_courses()
        loaded_course = repo.get_course(str(course.pk))
        missing_course = repo.get_course(
            '550e8400-e29b-41d4-a716-446655440000',
        )
        assignments = repo.get_course_assignments(str(course.pk))
        work_groups = repo.get_work_analog_groups(str(self.source_work.pk))
        variants_count = repo.count_work_variants(str(self.source_work.pk))
        topic = Topic.objects.create(
            name='Кинематика',
            subject='Физика',
            section='Механика',
            grade_level=9,
        )
        subtopic = SubTopic.objects.create(
            topic=topic,
            name='Средняя скорость',
            description='Описание',
            order=1,
        )
        subtopics = repo.get_topic_subtopics(str(topic.pk))
        missing_subtopics = repo.get_topic_subtopics(
            '550e8400-e29b-41d4-a716-446655440000',
        )
        topics = repo.get_topics()
        loaded_topic = repo.get_topic(str(topic.pk))
        topic_detail_subtopics = repo.get_topic_detail_subtopics(str(topic.pk))
        missing_topic = repo.get_topic(
            '550e8400-e29b-41d4-a716-446655440000',
        )

        self.assertEqual(courses[0].pk, str(course.pk))
        self.assertEqual(courses[0].assignments_count, 1)
        self.assertEqual(loaded_course.pk, str(course.pk))
        self.assertEqual(loaded_course.name, course.name)
        self.assertEqual(loaded_course.subject, course.subject)
        self.assertIsNone(missing_course)
        self.assertEqual(assignments[0].order, assignment.order)
        self.assertEqual(assignments[0].work.pk, str(self.source_work.pk))
        self.assertEqual(assignments[0].work.name, self.source_work.name)
        self.assertEqual(work_groups[0].group_name, self.weak_group.name)
        self.assertEqual(variants_count, 1)
        self.assertEqual(subtopics, [{
            'id': str(subtopic.pk),
            'name': 'Средняя скорость',
            'description': 'Описание',
        }])
        self.assertEqual(missing_subtopics, [])
        loaded_list_topic = next(item for item in topics if item.pk == str(topic.pk))
        self.assertEqual(loaded_list_topic.subtopics_count, 1)
        self.assertEqual(loaded_topic.pk, str(topic.pk))
        self.assertEqual(loaded_topic.name, topic.name)
        self.assertIsNone(missing_topic)
        self.assertEqual(topic_detail_subtopics[0].pk, str(subtopic.pk))
        self.assertEqual(topic_detail_subtopics[0].name, subtopic.name)

    def test_curriculum_repository_filters_courses_by_academic_year(self):
        year_2026 = AcademicYear.objects.create(
            name='2026-2027',
            start_date=dt.date(2026, 9, 1),
            end_date=dt.date(2027, 8, 31),
            is_active=True,
        )
        year_2027 = AcademicYear.objects.create(
            name='2027-2028',
            start_date=dt.date(2027, 9, 1),
            end_date=dt.date(2028, 8, 31),
        )
        course_2026 = Course.objects.create(
            name='Физика 8',
            subject='Физика',
            grade_level=8,
            year=year_2026,
        )
        Course.objects.create(
            name='Физика 9',
            subject='Физика',
            grade_level=9,
            year=year_2027,
        )

        courses = DjangoCurriculumRepository().get_courses(year=year_2026)

        self.assertEqual([course.pk for course in courses], [str(course_2026.pk)])

    def test_codifier_repository_returns_list_and_detail_data(self):
        codifier = CodifierSpec.objects.create(
            name='ОГЭ 2026 Физика',
            short_name='ОГЭ 2026',
            subject='Физика',
            exam_type='oge',
            year=2026,
        )
        root = ContentEntry.objects.create(
            codifier=codifier,
            code='1',
            name='Механика',
        )
        leaf = ContentEntry.objects.create(
            codifier=codifier,
            parent=root,
            code='1.1',
            name='Динамика',
            topic=self.topic,
        )
        requirement = Requirement.objects.create(
            codifier=codifier,
            code='1',
            name='Знать понятия',
        )
        repo = DjangoCodifierRepository()

        codifiers = repo.get_list_codifiers()
        loaded_codifier = repo.get_codifier(str(codifier.pk))
        missing_codifier = repo.get_codifier(
            '550e8400-e29b-41d4-a716-446655440000',
        )
        content_tree = repo.get_content_tree(str(codifier.pk))
        requirements = repo.get_requirements(str(codifier.pk))
        coverage = repo.get_coverage(str(codifier.pk))

        self.assertEqual(codifiers[0].pk, str(codifier.pk))
        self.assertEqual(codifiers[0].short_name, codifier.short_name)
        self.assertEqual(codifiers[0].content_entries_count, 2)
        self.assertEqual(codifiers[0].requirements_count, 1)
        self.assertEqual(loaded_codifier.pk, str(codifier.pk))
        self.assertEqual(loaded_codifier.short_name, codifier.short_name)
        self.assertEqual(loaded_codifier.content_entries_count, 2)
        self.assertIsNone(missing_codifier)
        self.assertEqual(content_tree[0].code, root.code)
        self.assertEqual(content_tree[0].children[0].code, leaf.code)
        self.assertEqual(content_tree[0].children[0].topic.name, self.topic.name)
        self.assertEqual(requirements[0].code, requirement.code)
        self.assertEqual(requirements[0].name, requirement.name)
        self.assertEqual(coverage['total'], 1)
        self.assertEqual(coverage['covered'], 1)
        self.assertEqual(leaf.parent, root)

    def test_codifier_repository_builds_deep_naturally_sorted_tree(self):
        codifier = CodifierSpec.objects.create(
            name='Авторский кодификатор',
            short_name='Авторский',
            subject='Физика',
            exam_type='custom',
            year=2026,
        )
        root = ContentEntry.objects.create(
            codifier=codifier,
            code='1',
            name='Механика',
        )
        later = ContentEntry.objects.create(
            codifier=codifier,
            parent=root,
            code='1.10',
            name='Поздний раздел',
        )
        middle = ContentEntry.objects.create(
            codifier=codifier,
            parent=root,
            code='1.2',
            name='Средний раздел',
        )
        first = ContentEntry.objects.create(
            codifier=codifier,
            parent=root,
            code='1.1',
            name='Первый раздел',
            topic=self.topic,
        )
        deep = ContentEntry.objects.create(
            codifier=codifier,
            parent=middle,
            code='1.2.1',
            name='Глубокий элемент',
            topic=self.topic,
            subtopic=self.subtopic,
        )
        self.replacement.subtopic = self.subtopic
        self.replacement.save(update_fields=['subtopic'])
        other_codifier = CodifierSpec.objects.create(
            name='Другой авторский кодификатор',
            short_name='Другой',
            subject='Физика',
            exam_type='custom',
            year=2027,
        )
        sibling = ContentEntry.objects.create(
            codifier=other_codifier,
            code='5.4',
            name='Та же подтема',
            topic=self.topic,
            subtopic=self.subtopic,
        )

        repo = DjangoCodifierRepository()
        tree = repo.get_content_tree(str(codifier.pk))
        coverage = repo.get_coverage(str(codifier.pk))

        self.assertEqual(
            [entry.code for entry in tree[0].children],
            [first.code, middle.code, later.code],
        )
        deep_data = tree[0].children[1].children[0]
        self.assertEqual(deep_data.code, deep.code)
        self.assertEqual(deep_data.task_count, 1)
        self.assertEqual(deep_data.sibling_codes[0].code, sibling.code)
        self.assertEqual(coverage['total'], 3)
        self.assertEqual(coverage['covered'], 2)

    def test_core_repository_returns_dashboard_counts(self):
        orphan = Variant.objects.create(
            work=None,
            number=1,
            work_name_snapshot='Сирота',
        )
        repo = DjangoCoreRepository()

        self.assertEqual(repo.count_tasks(), 4)
        self.assertEqual(repo.count_works(), 1)
        self.assertEqual(repo.count_variants(), 2)
        self.assertEqual(repo.count_orphan_variants(), 1)
        self.assertEqual(repo.count_students(), 1)
        self.assertEqual(repo.count_events(), 1)
        self.assertEqual(repo.count_analog_groups(), 2)
        self.assertIsNotNone(orphan.pk)

    def test_core_repository_returns_global_search_results(self):
        repo = DjangoCoreRepository()

        text_results = repo.search_by_text(['слабое'])
        uuid_results = repo.search_by_uuid(self.source_work.get_short_uuid())

        self.assertEqual(text_results['tasks'][0].pk, str(self.original_weak.pk))
        self.assertEqual(text_results['tasks'][0].text, self.original_weak.text)
        self.assertEqual(list(text_results['works']), [])
        self.assertEqual(list(text_results['groups']), [])
        self.assertEqual(uuid_results['works'][0].pk, str(self.source_work.pk))
        self.assertEqual(uuid_results['works'][0].name, self.source_work.name)

    def test_work_repository_returns_variant_list_page_data(self):
        repo = DjangoVariantReadRepository()

        variants = repo.get_list_variants()

        self.assertEqual(variants[0].pk, str(self.source_variant.pk))
        self.assertEqual(variants[0].number, self.source_variant.number)
        self.assertEqual(variants[0].work.name, self.source_work.name)
        self.assertEqual(variants[0].work.duration, self.source_work.duration)
        self.assertEqual(variants[0].task_count, 2)

    def test_work_repository_returns_form_analog_group_options(self):
        repo = DjangoWorkReadRepository()

        analog_group_options = repo.get_work_form_analog_group_options()

        self.assertEqual(
            {group.name for group in analog_group_options},
            {self.weak_group.name, self.ok_group.name},
        )

    def test_work_repository_returns_variant_detail_page_data(self):
        repo = DjangoVariantReadRepository()

        variant = repo.get_variant_detail(str(self.source_variant.pk))
        missing_variant = repo.get_variant_detail(
            '550e8400-e29b-41d4-a716-446655440000',
        )
        variant_tasks = repo.get_variant_detail_tasks(str(self.source_variant.pk))
        total_max_points = repo.get_variant_total_max_points(
            str(self.source_variant.pk),
        )

        self.assertEqual(variant.pk, str(self.source_variant.pk))
        self.assertEqual(variant.display_name, self.source_work.name)
        self.assertIsNone(missing_variant)
        self.assertEqual(len(variant_tasks), 2)
        self.assertEqual(variant_tasks[0].task.pk, str(self.original_weak.pk))
        self.assertEqual(variant_tasks[0].task.text, self.original_weak.text)
        self.assertEqual(total_max_points, 7)

    def test_variant_detail_resolves_student_from_source_participation(self):
        remedial_variant = Variant.objects.create(
            number=2,
            work_name_snapshot='Работа над ошибками',
            variant_type='remedial',
            source_participation=self.participation,
        )

        variant = DjangoVariantReadRepository().get_variant_detail(
            str(remedial_variant.pk),
        )

        self.assertEqual(variant.assigned_student.pk, str(self.student.pk))
        self.assertEqual(
            variant.assigned_student.full_name,
            self.student.get_full_name(),
        )

    def test_work_repository_returns_orphan_variant_list_data(self):
        orphan = Variant.objects.create(
            work=None,
            number=7,
            work_name_snapshot='Сирота',
        )
        repo = DjangoOrphanVariantRepository()

        variants = repo.get_orphan_variants()
        total_orphans = repo.count_orphan_variants()

        self.assertEqual(total_orphans, 1)
        self.assertEqual(variants[0].pk, str(orphan.pk))
        self.assertEqual(variants[0].display_name, 'Сирота')
        self.assertEqual(variants[0].short_uuid, orphan.get_short_uuid())
        self.assertEqual(variants[0].task_count, 0)
        self.assertEqual(variants[0].total_max_points, 0)

    def test_work_repository_syncs_analog_groups_from_variants(self):
        WorkAnalogGroup.objects.filter(work=self.source_work).delete()
        repo = DjangoWorkSpecSyncRepository()

        result = SyncWorkAnalogGroupsUseCase(
            repo,
            transaction_manager=DjangoTransactionManager(),
        ).execute(
            SyncWorkAnalogGroupsRequest(
                work_id=str(self.source_work.pk),
            )
        )
        groups = WorkAnalogGroup.objects.filter(work=self.source_work)

        self.assertEqual(result.status, 'synced')
        self.assertEqual(result.created_count, 2)
        self.assertEqual(groups.count(), 2)
        self.assertEqual(
            {group.analog_group for group in groups},
            {self.weak_group, self.ok_group},
        )

    def test_work_repository_does_not_sync_missing_work(self):
        result = SyncWorkAnalogGroupsUseCase(
            DjangoWorkSpecSyncRepository(),
            transaction_manager=DjangoTransactionManager(),
        ).execute(
            SyncWorkAnalogGroupsRequest(
                work_id='00000000-0000-0000-0000-000000000000',
            )
        )

        self.assertEqual(result.status, 'not_found')
        self.assertEqual(result.created_count, 0)

    def test_work_repository_rejects_stale_specification_sync_plan(self):
        WorkAnalogGroup.objects.filter(work=self.source_work).delete()
        repo = DjangoWorkSpecSyncRepository()
        source = repo.get_work_spec_sync_source(str(self.source_work.pk))
        plan = WorkSpecSyncService().build_plan(source.variant_group_ids)
        self.source_work.variant_counter += 1
        self.source_work.save()

        result = repo.save_work_spec_sync_plan(
            work_id=str(self.source_work.pk),
            expected_variant_counter=source.variant_counter,
            plan=plan,
        )

        self.assertEqual(result.status, 'conflict')
        self.assertFalse(
            WorkAnalogGroup.objects.filter(work=self.source_work).exists()
        )

    def test_task_group_repository_mutates_bulk_memberships(self):
        repo = DjangoTaskGroupRepository()
        new_group_id = repo.create_analog_group(
            name='Новая группа',
            description='Описание',
        )
        updated = repo.update_analog_group(
            group_id=new_group_id,
            name='Обновлённая группа',
            description='Новое описание',
        )
        missing_updated = repo.update_analog_group(
            group_id='550e8400-e29b-41d4-a716-446655440000',
            name='Нет',
        )

        self.assertTrue(updated)
        self.assertFalse(missing_updated)
        self.assertTrue(repo.analog_group_name_exists('Обновлённая группа'))
        self.assertEqual(
            DjangoTaskSelectionRepository().count_existing_task_ids(
                {str(self.original_weak.pk)},
            ),
            1,
        )

        created_count = repo.add_tasks_to_group(
            new_group_id,
            [str(self.original_weak.pk), str(self.replacement.pk)],
            bank_role=TASK_BANK_ROLE_DEMO,
        )
        duplicate_count = repo.add_tasks_to_group(
            new_group_id,
            [str(self.original_weak.pk)],
        )

        self.assertEqual(created_count, 2)
        self.assertEqual(duplicate_count, 0)
        self.assertEqual(
            set(
                TaskGroup.objects.filter(
                    group_id=new_group_id,
                    task_id__in=[self.original_weak.pk, self.replacement.pk],
                ).values_list('bank_role', flat=True)
            ),
            {TASK_BANK_ROLE_DEMO},
        )
        removed_count = repo.remove_tasks_from_all_groups(
            [str(self.original_weak.pk), str(self.replacement.pk)]
        )
        self.assertEqual(removed_count, 4)
        self.assertFalse(
            TaskGroup.objects.filter(
                task_id__in=[self.original_weak.pk, self.replacement.pk],
            ).exists()
        )

    def test_task_group_repository_updates_roles(self):
        repo = DjangoTaskGroupRepository()
        group = AnalogGroup.objects.create(name='Роли')
        other_group = AnalogGroup.objects.create(name='Другая группа')
        first_membership = TaskGroup.objects.create(
            task=self.original_weak,
            group=group,
        )
        second_membership = TaskGroup.objects.create(
            task=self.replacement,
            group=group,
        )
        other_membership = TaskGroup.objects.create(
            task=self.original_weak,
            group=other_group,
        )

        updated_count = repo.update_task_group_roles(
            group_id=str(group.pk),
            task_roles={
                str(self.original_weak.pk): TASK_BANK_ROLE_DEMO,
                str(self.replacement.pk): TASK_BANK_ROLE_PRACTICE,
                str(self.too_hard.pk): TASK_BANK_ROLE_DEMO,
            },
        )

        first_membership.refresh_from_db()
        second_membership.refresh_from_db()
        other_membership.refresh_from_db()
        self.assertEqual(updated_count, 2)
        self.assertEqual(first_membership.bank_role, TASK_BANK_ROLE_DEMO)
        self.assertEqual(second_membership.bank_role, TASK_BANK_ROLE_PRACTICE)
        self.assertEqual(other_membership.bank_role, 'control')

    def test_work_repository_composes_variants(self):
        repo = DjangoWorkVariantCompositionRepository()
        existing_count = Variant.objects.filter(work=self.source_work).count()
        existing_counter = self.source_work.variant_counter

        result = ComposeWorkVariantsUseCase(
            repo,
            transaction_manager=DjangoTransactionManager(),
        ).execute(
            ComposeWorkVariantsRequest(
                work_id=str(self.source_work.pk),
                count=2,
            )
        )

        self.source_work.refresh_from_db()
        variants = Variant.objects.filter(work=self.source_work)
        self.assertEqual(result.status, 'generated')
        self.assertEqual(result.created_count, 2)
        self.assertEqual(variants.count(), existing_count + 2)
        self.assertEqual(self.source_work.variant_counter, existing_counter + 2)
        self.assertEqual(
            variants.order_by('-number').first().varianttask_set.count(),
            1,
        )

    def test_compose_variants_use_case_handles_missing_work(self):
        result = ComposeWorkVariantsUseCase(
            DjangoWorkVariantCompositionRepository(),
            transaction_manager=DjangoTransactionManager(),
        ).execute(
            ComposeWorkVariantsRequest(
                work_id='00000000-0000-0000-0000-000000000000',
                count=2,
            )
        )

        self.assertEqual(result.status, 'not_found')
        self.assertEqual(result.created_count, 0)

    def test_work_repository_rejects_stale_variant_composition_plan(self):
        repo = DjangoWorkVariantCompositionRepository()
        composition_source = repo.get_variant_composition_source(
            str(self.source_work.pk),
        )
        composition_input = WorkVariantCompositionService().build_input(
            composition_source,
        )
        plan = WorkVariantCompositionService().compose(
            composition_input,
            count=2,
        )
        existing_count = Variant.objects.filter(work=self.source_work).count()
        self.source_work.variant_counter += 1
        self.source_work.save()

        result = repo.save_variant_composition_plan(
            work_id=str(self.source_work.pk),
            expected_variant_counter=composition_input.variant_counter,
            plan=plan,
        )

        self.assertEqual(result.status, 'conflict')
        self.assertEqual(
            Variant.objects.filter(work=self.source_work).count(),
            existing_count,
        )

    def test_work_repository_composes_variant_with_role_filtered_snapshot_rows(self):
        work = Work.objects.create(
            name='Рабочий лист',
            work_type='practice',
            max_score=0,
        )
        analog_group = AnalogGroup.objects.create(name='Один закон, разные роли')
        demo_task = self._task('Демо задача', difficulty=4)
        practice_task = self._task('Самостоятельная задача', difficulty=3)
        theory_topic = Topic.objects.create(
            name='Импульс',
            subject='Физика',
            section='Механика',
            grade_level=9,
            description='Импульс равен произведению массы на скорость.',
        )
        theory_subtopic = SubTopic.objects.create(
            topic=theory_topic,
            name='Закон сохранения импульса',
            description='Суммарный импульс замкнутой системы сохраняется.',
        )
        TaskGroup.objects.create(
            task=demo_task,
            group=analog_group,
            bank_role=TASK_BANK_ROLE_DEMO,
        )
        TaskGroup.objects.create(
            task=practice_task,
            group=analog_group,
            bank_role=TASK_BANK_ROLE_PRACTICE,
        )
        demo_selection = WorkAnalogGroup.objects.create(
            work=work,
            analog_group=analog_group,
            order=10,
            count=1,
            weight=4,
            bank_role_filter=TASK_BANK_ROLE_DEMO,
            render_mode=TASK_RENDER_MODE_WITH_FULL_SOLUTION,
            is_assessable=False,
            blank_cells_after=True,
            blank_cells_rows=9,
        )
        practice_selection = WorkAnalogGroup.objects.create(
            work=work,
            analog_group=analog_group,
            order=30,
            count=1,
            weight=3,
            bank_role_filter=TASK_BANK_ROLE_PRACTICE,
        )
        theory_block = WorkContentBlock.objects.create(
            work=work,
            content_type='theory',
            order=5,
            title='Опорная теория',
            include_subtopics=True,
        )
        theory_block.topics.add(theory_topic)
        text_block = WorkContentBlock.objects.create(
            work=work,
            content_type='text',
            order=15,
            title='Инструкция',
            body='Покажите ход решения.',
        )
        repo = DjangoWorkVariantCompositionRepository()

        result = ComposeWorkVariantsUseCase(
            repo,
            transaction_manager=DjangoTransactionManager(),
        ).execute(
            ComposeWorkVariantsRequest(
                work_id=str(work.pk),
                count=1,
            )
        )

        variant = Variant.objects.get(work=work)
        rows = list(variant.varianttask_set.select_related('task').order_by('order'))
        self.assertEqual(result.status, 'generated')
        self.assertEqual(result.created_count, 1)
        self.assertEqual(variant.max_score_snapshot, 3)
        self.assertEqual([row.task for row in rows], [demo_task, practice_task])
        self.assertEqual(rows[0].bank_role, TASK_BANK_ROLE_DEMO)
        self.assertEqual(
            rows[0].source_selection_id,
            str(demo_selection.pk),
        )
        self.assertEqual(rows[0].content_order, demo_selection.order)
        self.assertEqual(rows[0].render_mode, TASK_RENDER_MODE_WITH_FULL_SOLUTION)
        self.assertFalse(rows[0].is_assessable)
        self.assertTrue(rows[0].blank_cells_after)
        self.assertEqual(rows[0].blank_cells_rows, 9)
        self.assertEqual(rows[0].max_points, 0)
        self.assertEqual(rows[0].task_snapshot['text'], demo_task.text)
        self.assertEqual(
            rows[0].task_snapshot['topic_name'],
            demo_task.topic.name,
        )
        self.assertEqual(rows[1].bank_role, TASK_BANK_ROLE_PRACTICE)
        self.assertEqual(
            rows[1].source_selection_id,
            str(practice_selection.pk),
        )
        self.assertEqual(rows[1].content_order, practice_selection.order)
        self.assertTrue(rows[1].is_assessable)
        self.assertEqual(rows[1].blank_cells_rows, DEFAULT_BLANK_CELLS_ROWS)
        self.assertEqual(rows[1].max_points, 3)

        snapshots = list(
            VariantContentBlockSnapshot.objects.filter(
                variant=variant,
            ).order_by('order')
        )
        self.assertEqual(
            [snapshot.source_content_id for snapshot in snapshots],
            [str(theory_block.pk), str(text_block.pk)],
        )
        self.assertEqual(snapshots[0].title, 'Опорная теория')
        self.assertEqual(
            snapshots[0].content['topics'][0]['content'],
            'Импульс равен произведению массы на скорость.',
        )
        self.assertEqual(
            snapshots[0].content['topics'][0]['subtopics'][0]['content'],
            'Суммарный импульс замкнутой системы сохраняется.',
        )
        self.assertEqual(
            snapshots[1].content,
            {'body': 'Покажите ход решения.'},
        )

        theory_topic.description = 'Изменённая теория'
        theory_topic.save(update_fields=['description'])
        theory_subtopic.description = 'Изменённая подтема'
        theory_subtopic.save(update_fields=['description'])
        text_block.body = 'Изменённая инструкция'
        text_block.save(update_fields=['body'])
        snapshots[0].refresh_from_db()
        snapshots[1].refresh_from_db()

        self.assertEqual(
            snapshots[0].content['topics'][0]['content'],
            'Импульс равен произведению массы на скорость.',
        )
        self.assertEqual(
            snapshots[1].content['body'],
            'Покажите ход решения.',
        )

    def test_work_repository_creates_work_from_orphan_variants(self):
        first_orphan = Variant.objects.create(
            work=None,
            number=7,
            work_name_snapshot='Старая сирота',
            variant_type='regular',
        )
        second_orphan = Variant.objects.create(
            work=None,
            number=8,
            work_name_snapshot='Вторая сирота',
            variant_type='remedial',
        )
        create_variant_task(
            variant=first_orphan,
            task=self.original_weak,
            order=1,
            max_points=4,
            weight=4,
        )
        create_variant_task(
            variant=second_orphan,
            task=self.original_ok,
            order=1,
            max_points=6,
            weight=6,
        )
        use_case = CreateWorkFromOrphansUseCase(
            orphan_variant_repo=DjangoOrphanVariantRepository(),
        )

        result = use_case.execute(
            CreateWorkFromOrphansRequest(
                variant_ids=[str(second_orphan.pk), str(first_orphan.pk)],
                work_name='  Работа из сирот  ',
            )
        )

        self.assertEqual(result.status, 'created')
        work = Work.objects.get(pk=result.work_id)
        first_orphan.refresh_from_db()
        second_orphan.refresh_from_db()

        self.assertEqual(work.name, 'Работа из сирот')
        self.assertEqual(work.work_type, 'remedial')
        self.assertEqual(work.max_score, 6)
        self.assertEqual(work.variant_counter, 2)
        self.assertEqual(first_orphan.work, work)
        self.assertEqual(second_orphan.work, work)
        self.assertEqual(first_orphan.number, 1)
        self.assertEqual(second_orphan.number, 2)
        self.assertEqual(first_orphan.max_score_snapshot, 6)
        self.assertEqual(second_orphan.work_name_snapshot, work.name)

    def test_work_repository_does_not_create_work_for_non_orphan_variant(self):
        work_count = Work.objects.count()

        created = DjangoOrphanVariantRepository().create_work_from_orphan_variants(
            CreateWorkFromOrphanVariantsParams(
                name='Не должна сохраниться',
                work_type='remedial',
                max_score=0,
                variant_ids=[str(self.source_variant.pk)],
            )
        )

        self.assertIsNone(created)
        self.assertEqual(Work.objects.count(), work_count)

    def test_work_repository_creates_work_with_variant_from_tasks(self):
        repo = DjangoWorkVariantCreationRepository()

        created = repo.create_work_with_variant_from_tasks(
            CreateWorkWithVariantFromTasksParams(
                name='Работа из выбранных задач',
                work_type='quiz',
                task_ids=[
                    str(self.original_ok.pk),
                    '00000000-0000-0000-0000-000000000000',
                    str(self.original_weak.pk),
                ],
            )
        )

        work = Work.objects.get(pk=created.work_id)
        variant = Variant.objects.get(pk=created.variant_id)
        variant_tasks = list(
            VariantTask.objects.filter(variant=variant).order_by('order')
        )

        self.assertEqual(created.tasks_count, 2)
        self.assertEqual(work.name, 'Работа из выбранных задач')
        self.assertEqual(work.work_type, 'quiz')
        self.assertEqual(work.variant_counter, 1)
        self.assertEqual(variant.work, work)
        self.assertEqual(variant.number, 1)
        self.assertEqual(
            [variant_task.task for variant_task in variant_tasks],
            [self.original_ok, self.original_weak],
        )
        self.assertEqual(
            [variant_task.order for variant_task in variant_tasks],
            [1, 2],
        )
        self.assertEqual(
            [variant_task.max_points for variant_task in variant_tasks],
            [0, 0],
        )

    def test_work_repository_returns_variant_delete_info(self):
        repo = DjangoVariantLifecycleRepository()

        info = repo.get_variant_delete_info(str(self.source_variant.pk))
        missing_info = repo.get_variant_delete_info(
            '550e8400-e29b-41d4-a716-446655440000',
        )

        self.assertEqual(info.task_count, 2)
        self.assertEqual(info.participation_count, 1)
        self.assertTrue(info.has_participations)
        self.assertIsNone(missing_info)

    def test_work_repository_detaches_variant_from_work(self):
        repo = DjangoVariantLifecycleRepository()

        short_id = repo.detach_variant_from_work(str(self.source_variant.pk))

        self.source_variant.refresh_from_db()
        self.assertEqual(short_id, self.source_variant.get_short_uuid())
        self.assertIsNone(self.source_variant.work)

    def test_work_repository_deletes_variant_and_returns_previous_work_id(self):
        variant = Variant.objects.create(
            work=self.source_work,
            number=99,
            work_name_snapshot=self.source_work.name,
        )
        variant_id = str(variant.pk)
        repo = DjangoVariantLifecycleRepository()

        work_id = repo.delete_variant(variant_id)

        self.assertEqual(work_id, str(self.source_work.pk))
        self.assertFalse(Variant.objects.filter(pk=variant_id).exists())

    def test_work_repository_bulk_deletes_only_selected_work_variants(self):
        other_work = Work.objects.create(name='Другая работа')
        first_variant = Variant.objects.create(
            work=self.source_work,
            number=10,
            work_name_snapshot=self.source_work.name,
        )
        second_variant = Variant.objects.create(
            work=self.source_work,
            number=11,
            work_name_snapshot=self.source_work.name,
        )
        other_variant = Variant.objects.create(
            work=other_work,
            number=1,
            work_name_snapshot=other_work.name,
        )
        repo = DjangoVariantLifecycleRepository()

        deleted_count = repo.bulk_delete_work_variants(
            work_id=str(self.source_work.pk),
            variant_ids=[
                str(first_variant.pk),
                str(second_variant.pk),
                str(other_variant.pk),
            ],
        )

        self.assertEqual(deleted_count, 2)
        self.assertFalse(Variant.objects.filter(pk=first_variant.pk).exists())
        self.assertFalse(Variant.objects.filter(pk=second_variant.pk).exists())
        self.assertTrue(Variant.objects.filter(pk=other_variant.pk).exists())
        self.assertEqual(repo.count_work_variants(str(self.source_work.pk)), 1)

    def test_event_repository_grades_participation_and_syncs_review_state(self):
        self.event.status = 'completed'
        self.event.save()
        self.participation.status = 'completed'
        self.participation.save()
        variant_task = VariantTask.objects.get(
            variant=self.source_variant,
            task=self.original_weak,
        )
        demo_variant_task = VariantTask.objects.get(
            variant=self.source_variant,
            task=self.original_ok,
        )
        demo_variant_task.is_assessable = False
        demo_variant_task.save(update_fields=['is_assessable'])
        result = GradeStudentWorkUseCase(
            grading_repo=DjangoParticipationGradingRepository(),
            review_task_repo=DjangoReviewTaskRepository(),
            grading_service=GradingService(),
            transaction_manager=DjangoTransactionManager(),
            attempt_snapshot_repo=DjangoAttemptSnapshotRepository(),
        ).execute(
            GradeStudentWorkRequest(
                participation_id=str(self.participation.pk),
                score=4,
                points=6,
                max_points=7,
                teacher_comment='Хорошая работа',
                checked_by_username='teacher',
                task_scores={
                    str(variant_task.pk): {
                        'task_id': str(self.original_weak.pk),
                        'points': 1,
                        'max_points': 2,
                        'comment': 'Повторить',
                    },
                    str(demo_variant_task.pk): {
                        'task_id': str(self.original_ok.pk),
                        'points': 5,
                        'max_points': 5,
                        'comment': 'Не должно сохраниться',
                    },
                },
            )
        )

        self.mark.refresh_from_db()
        self.participation.refresh_from_db()
        self.event.refresh_from_db()
        attempt = AttemptSnapshot.objects.get(pk=result.attempt_snapshot_id)
        task_result = attempt.task_results.get(is_assessable_snapshot=True)

        self.assertEqual(result.status, 'saved')
        self.assertEqual(result.grade.score, 4)
        self.assertEqual(result.grade.student_name, 'Петров Пётр')
        self.assertEqual(self.mark.score, 4)
        self.assertEqual(self.mark.points, 1)
        self.assertEqual(self.mark.max_points, 2)
        self.assertEqual(self.mark.teacher_comment, 'Хорошая работа')
        self.assertEqual(self.mark.checked_by, 'teacher')
        self.assertEqual(
            self.mark.task_scores[str(variant_task.pk)]['task_id'],
            str(self.original_weak.pk),
        )
        self.assertNotIn(str(demo_variant_task.pk), self.mark.task_scores)
        self.assertIsNotNone(self.mark.checked_at)
        self.assertEqual(self.participation.status, 'graded')
        self.assertIsNotNone(self.participation.graded_at)
        self.assertEqual(self.event.status, 'graded')
        self.assertEqual(task_result.points, 1)
        self.assertEqual(task_result.checked_max_points, 2)
        self.assertEqual(task_result.comment, 'Повторить')
        self.assertEqual(task_result.variant_task, variant_task)

    def test_grading_use_case_waits_for_all_active_participants(self):
        self.event.status = 'completed'
        self.event.save()
        self.participation.status = 'completed'
        self.participation.save()
        second_student = Student.objects.create(
            last_name='Сидоров',
            first_name='Сидор',
        )
        second_participation = EventParticipation.objects.create(
            event=self.event,
            student=second_student,
            variant=self.source_variant,
            status='completed',
        )
        use_case = GradeStudentWorkUseCase(
            grading_repo=DjangoParticipationGradingRepository(),
            review_task_repo=DjangoReviewTaskRepository(),
            grading_service=GradingService(),
            transaction_manager=DjangoTransactionManager(),
        )

        first_result = use_case.execute(
            GradeStudentWorkRequest(
                participation_id=str(self.participation.pk),
                score=4,
            )
        )
        second_result = use_case.execute(
            GradeStudentWorkRequest(
                participation_id=str(second_participation.pk),
                score=5,
            )
        )

        self.assertEqual(first_result.grade.event_status, 'reviewing')
        self.assertEqual(second_result.grade.event_status, 'graded')
        self.event.refresh_from_db()
        self.assertEqual(self.event.status, 'graded')

    def test_event_repository_returns_list_and_detail_page_data(self):
        repo = DjangoEventReadRepository()

        events = repo.get_list_events()
        participations = repo.get_detail_participations(str(self.event.pk))
        available_variants = repo.get_available_variants(str(self.event.pk))
        event_ref = repo.get_by_id(str(self.event.pk))
        participation_ref = repo.get_participation_ref(str(self.participation.pk))
        event_by_id = {str(event.pk): event for event in events}

        self.assertIn(str(self.event.pk), event_by_id)
        self.assertEqual(event_by_id[str(self.event.pk)].participant_count, 1)
        self.assertEqual(participations[0].student.last_name, self.student.last_name)
        self.assertEqual(participations[0].variant.number, 1)
        self.assertEqual(participations[0].mark_obj.score, 2)
        self.assertEqual(available_variants[0].number, 1)
        self.assertEqual(event_ref.pk, str(self.event.pk))
        self.assertEqual(event_ref.work.name, self.source_work.name)
        self.assertEqual(event_ref.work_variant_count, 1)
        self.assertEqual(event_ref.date, self.event.planned_date)
        self.assertEqual(participation_ref.pk, str(self.participation.pk))
        self.assertEqual(participation_ref.event_id, str(self.event.pk))

    def test_event_repository_mutates_participants_variants_and_status(self):
        read_repo = DjangoEventReadRepository()
        write_repo = DjangoEventWriteRepository()
        participation_repo = DjangoEventParticipationRepository()
        second_student = Student.objects.create(
            last_name='Сидоров',
            first_name='Сидор',
        )
        second_variant = Variant.objects.create(
            work=self.source_work,
            number=2,
            work_name_snapshot=self.source_work.name,
        )

        created_count = participation_repo.add_participants(
            event_id=str(self.event.pk),
            student_ids=[str(self.student.pk), str(second_student.pk)],
        )
        second_participation = EventParticipation.objects.get(
            event=self.event,
            student=second_student,
        )
        assigned_count = participation_repo.assign_variants(
            event_id=str(self.event.pk),
            assignments={str(second_participation.pk): str(second_variant.pk)},
        )
        single_assignment = participation_repo.assign_variant(
            event_id=str(self.event.pk),
            participation_id=str(self.participation.pk),
            variant_id=str(second_variant.pk),
        )
        status = read_repo.get_event_status(str(self.event.pk))
        write_repo.set_event_status(str(self.event.pk), 'reviewing')

        self.participation.refresh_from_db()
        second_participation.refresh_from_db()
        self.event.refresh_from_db()

        self.assertEqual(created_count, 1)
        self.assertEqual(assigned_count, 1)
        self.assertEqual(second_participation.variant, second_variant)
        self.assertEqual(self.participation.variant, second_variant)
        self.assertEqual(single_assignment.variant_number, 2)
        self.assertEqual(single_assignment.student_name, 'Петров Пётр')
        self.assertEqual(status, 'graded')
        self.assertEqual(self.event.status, 'reviewing')

    def test_review_repository_returns_participation_review_data(self):
        ReviewComment.objects.create(
            text='Аккуратнее с единицами',
            category='suggestion',
            usage_count=3,
        )
        demo_task = self._task('Демо с решением', difficulty=4)
        demo_variant_task = create_variant_task(
            variant=self.source_variant,
            task=demo_task,
            order=3,
            max_points=0,
            weight=4,
            is_assessable=False,
        )
        self.original_weak.text = 'Изменённое задание банка'
        self.original_weak.answer = 'Изменённый ответ'
        self.original_weak.difficulty = 6
        self.original_weak.save(update_fields=['text', 'answer', 'difficulty'])
        self.topic.name = 'Изменённая тема банка'
        self.topic.save(update_fields=['name'])
        repo = DjangoReviewRepository()
        review_task_repo = DjangoReviewTaskRepository()

        participation = repo.get_participation(str(self.participation.pk))
        variant_tasks = review_task_repo.get_variant_tasks(
            str(self.participation.pk),
        )
        mark = repo.get_or_create_mark(str(self.participation.pk), default_max_points=7)
        navigation = repo.get_review_participations(str(self.event.pk))
        comments = repo.get_typical_comments()

        self.assertEqual(participation.student.last_name, 'Петров')
        self.assertEqual(participation.event.name, self.event.name)
        self.assertEqual(participation.variant.number, 1)
        self.assertEqual(len(variant_tasks), 3)
        self.assertEqual(variant_tasks[0].task.text, 'Исходное слабое')
        self.assertEqual(variant_tasks[0].task.answer, 'Ответ')
        self.assertEqual(variant_tasks[0].task.difficulty, 2)
        self.assertEqual(variant_tasks[0].task.topic.name, 'Динамика')
        self.assertEqual(variant_tasks[0].weight, 2)
        self.assertTrue(variant_tasks[0].is_assessable)
        self.assertEqual(variant_tasks[2].task.text, 'Демо с решением')
        self.assertEqual(
            variant_tasks[2].variant_task_id,
            str(demo_variant_task.pk),
        )
        self.assertFalse(variant_tasks[2].is_assessable)
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

    def test_review_repository_finalizes_event_and_toggles_absent(self):
        repo = DjangoReviewRepository()
        self.event.status = 'reviewing'
        self.event.save()
        second_student = Student.objects.create(
            last_name='Сидоров',
            first_name='Сидор',
        )
        second_participation = EventParticipation.objects.create(
            event=self.event,
            student=second_student,
            status='completed',
        )
        toggle_absent = ToggleParticipationAbsentUseCase(repo)

        event_ref = repo.finalize_event(str(self.event.pk))
        absent_result = toggle_absent.execute(ToggleParticipationAbsentRequest(
            participation_id=str(second_participation.pk),
        ))
        present_result = toggle_absent.execute(ToggleParticipationAbsentRequest(
            participation_id=str(second_participation.pk),
        ))
        checked_result = toggle_absent.execute(ToggleParticipationAbsentRequest(
            participation_id=str(self.participation.pk),
        ))

        self.event.refresh_from_db()
        second_participation.refresh_from_db()

        self.assertEqual(event_ref.pk, str(self.event.pk))
        self.assertEqual(event_ref.name, self.event.name)
        self.assertEqual(self.event.status, 'graded')
        self.assertTrue(absent_result.is_absent)
        self.assertEqual(absent_result.student_last_name, second_student.last_name)
        self.assertFalse(present_result.is_absent)
        self.assertEqual(second_participation.status, 'assigned')
        self.assertFalse(checked_result.changed)

    def test_review_repository_returns_save_navigation(self):
        repo = DjangoReviewRepository()
        second_student = Student.objects.create(
            last_name='Сидоров',
            first_name='Сидор',
        )
        second_participation = EventParticipation.objects.create(
            event=self.event,
            student=second_student,
            variant=self.source_variant,
            status='completed',
        )

        navigation = repo.get_save_navigation(str(self.participation.pk))
        Mark.objects.create(participation=second_participation, score=5)
        all_checked_navigation = repo.get_save_navigation(
            str(second_participation.pk),
        )

        self.assertEqual(navigation.event_id, str(self.event.pk))
        self.assertEqual(
            navigation.next_participation.pk,
            str(second_participation.pk),
        )
        self.assertFalse(navigation.all_checked)
        self.assertEqual(all_checked_navigation.event_id, str(self.event.pk))
        self.assertIsNone(all_checked_navigation.next_participation)
        self.assertTrue(all_checked_navigation.all_checked)

    def test_review_repository_syncs_and_returns_review_sessions(self):
        repo = DjangoReviewSessionRepository()
        reviewer = User.objects.create_user(username='teacher')

        session_ref = repo.sync_review_session(
            reviewer_id=str(reviewer.pk),
            event_id=str(self.event.pk),
            total_participations=3,
            checked_participations=1,
        )
        updated_ref = repo.sync_review_session(
            reviewer_id=str(reviewer.pk),
            event_id=str(self.event.pk),
            total_participations=3,
            checked_participations=2,
        )
        recent_sessions = repo.get_recent_sessions(str(reviewer.pk))
        session = ReviewSession.objects.get(
            reviewer=reviewer,
            event=self.event,
        )

        self.assertEqual(session_ref.event.name, self.event.name)
        self.assertEqual(updated_ref.checked_participations, 2)
        self.assertEqual(updated_ref.progress_percentage, 66.7)
        self.assertEqual(len(recent_sessions), 1)
        self.assertEqual(recent_sessions[0].pk, str(session.pk))
        self.assertEqual(session.total_participations, 3)
        self.assertEqual(session.checked_participations, 2)
