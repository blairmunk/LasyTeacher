from io import StringIO
from tempfile import TemporaryDirectory
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import AcademicYear
from curriculum.models import Topic
from events.models import Event, EventParticipation, Mark
from students.models import Student, StudentGroup
from task_groups.models import AnalogGroup, TaskGroup
from tasks.models import Task
from works.models import Variant, VariantTask, Work, WorkAnalogGroup


class ImportStudentsCsvCommandTests(TestCase):
    def test_dry_run_does_not_save_students_or_groups(self):
        with TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / 'students.csv'
            csv_path.write_text(
                (
                    'class,academic_year,last_name,first_name,middle_name,email\n'
                    '8А,2026-2027,Иванов,Иван,Петрович,ivanov@example.test\n'
                ),
                encoding='utf-8',
            )
            out = StringIO()

            call_command(
                'import_students_csv',
                str(csv_path),
                dry_run=True,
                stdout=out,
            )

        self.assertEqual(Student.objects.count(), 0)
        self.assertEqual(StudentGroup.objects.count(), 0)
        self.assertEqual(AcademicYear.objects.count(), 0)
        self.assertIn('DRY RUN', out.getvalue())

    def test_imports_students_groups_and_academic_year_from_csv(self):
        with TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / 'students.csv'
            csv_path.write_text(
                (
                    'класс,учебный_год,фамилия,имя,отчество,email\n'
                    '8А,2026-2027,Иванов,Иван,Петрович,ivanov@example.test\n'
                    '8А,2026-2027,Петрова,Анна,Сергеевна,\n'
                ),
                encoding='utf-8',
            )
            out = StringIO()

            call_command('import_students_csv', str(csv_path), stdout=out)

        year = AcademicYear.objects.get(name='2026-2027')
        group = StudentGroup.objects.get(name='8А', academic_year=year)
        self.assertEqual(Student.objects.count(), 2)
        self.assertEqual(group.students.count(), 2)
        self.assertTrue(year.is_active)
        self.assertIn('Импорт завершен', out.getvalue())

    def test_second_import_updates_existing_student_without_duplicate(self):
        with TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / 'students.csv'
            csv_path.write_text(
                (
                    'class,academic_year,last_name,first_name,middle_name,email\n'
                    '8А,2026-2027,Иванов,Иван,Петрович,ivanov@example.test\n'
                ),
                encoding='utf-8',
            )

            call_command('import_students_csv', str(csv_path), stdout=StringIO())
            call_command('import_students_csv', str(csv_path), stdout=StringIO())

        self.assertEqual(Student.objects.count(), 1)
        self.assertEqual(StudentGroup.objects.count(), 1)
        self.assertEqual(StudentGroup.objects.get().students.count(), 1)

    def test_dry_run_validates_academic_year_format(self):
        with TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / 'students.csv'
            csv_path.write_text(
                (
                    'class,academic_year,last_name,first_name\n'
                    '8А,2026,Иванов,Иван\n'
                ),
                encoding='utf-8',
            )

            with self.assertRaisesRegex(CommandError, '2026-2027'):
                call_command(
                    'import_students_csv',
                    str(csv_path),
                    dry_run=True,
                    stdout=StringIO(),
                )


class RemedialFromEventViewTests(TestCase):
    """Characterization tests for the current remedial-from-event flow."""

    def setUp(self):
        self.topic = Topic.objects.create(
            name='Кинематика',
            subject='Физика',
            section='Механика',
            grade_level=9,
        )
        self.student = Student.objects.create(
            last_name='Иванов',
            first_name='Иван',
        )
        self.source_work = Work.objects.create(
            name='Контрольная по кинематике',
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
            name='КР 9А',
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

        self.weak_original = self._task('Слабое исходное', difficulty=2)
        self.ok_original = self._task('Решённое исходное', difficulty=5)
        self.replacement_easy = self._task('Замена простая', difficulty=3)
        self.replacement_hard = self._task('Замена сложная', difficulty=6)

        self.weak_group = AnalogGroup.objects.create(name='Скорость')
        self.other_group = AnalogGroup.objects.create(name='Графики')
        WorkAnalogGroup.objects.create(
            work=self.source_work,
            analog_group=self.weak_group,
            order=1,
            weight=2,
        )
        TaskGroup.objects.create(task=self.weak_original, group=self.weak_group)
        TaskGroup.objects.create(task=self.replacement_easy, group=self.weak_group)
        TaskGroup.objects.create(task=self.replacement_hard, group=self.weak_group)
        TaskGroup.objects.create(task=self.ok_original, group=self.other_group)

        VariantTask.objects.create(
            variant=self.source_variant,
            task=self.weak_original,
            order=1,
            max_points=2,
            weight=2,
        )
        VariantTask.objects.create(
            variant=self.source_variant,
            task=self.ok_original,
            order=2,
            max_points=5,
            weight=5,
        )

        Mark.objects.create(
            participation=self.participation,
            score=2,
            points=5,
            max_points=7,
            task_scores={
                str(self.weak_original.pk): {'points': 0, 'max_points': 2},
                str(self.ok_original.pk): {'points': 5, 'max_points': 5},
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

    def test_create_student_saves_student(self):
        response = self.client.post(
            reverse('students:create'),
            data={
                'last_name': 'Петров',
                'first_name': 'Пётр',
                'middle_name': 'Петрович',
                'email': 'petrov@example.test',
            },
        )

        student = Student.objects.get(last_name='Петров')
        self.assertRedirects(
            response,
            reverse('students:list'),
            fetch_redirect_response=False,
        )
        self.assertEqual(student.first_name, 'Пётр')
        self.assertEqual(student.email, 'petrov@example.test')

    def test_update_student_saves_student(self):
        response = self.client.post(
            reverse('students:update', args=[self.student.pk]),
            data={
                'last_name': 'Иванов',
                'first_name': 'Иван',
                'middle_name': 'Иванович',
                'email': 'ivanov@example.test',
            },
        )

        self.student.refresh_from_db()
        self.assertRedirects(
            response,
            reverse('students:list'),
            fetch_redirect_response=False,
        )
        self.assertEqual(self.student.middle_name, 'Иванович')
        self.assertEqual(self.student.email, 'ivanov@example.test')

    def test_update_student_returns_404_for_missing_student(self):
        response = self.client.get(
            reverse(
                'students:update',
                args=['550e8400-e29b-41d4-a716-446655440000'],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_student_list_contains_user_edit_link(self):
        response = self.client.get(reverse('students:list'))

        self.assertContains(
            response,
            reverse('students:update', args=[self.student.pk]),
        )
        self.assertNotContains(response, '/admin/students/student/')

    def test_create_student_group_saves_group(self):
        response = self.client.post(
            reverse('students:group-create'),
            data={
                'name': '9Б',
                'students': [str(self.student.pk)],
            },
        )

        group = StudentGroup.objects.get(name='9Б')
        self.assertRedirects(
            response,
            reverse('students:group-detail', args=[group.pk]),
            fetch_redirect_response=False,
        )
        self.assertEqual(list(group.students.all()), [self.student])

    def test_update_student_group_saves_group(self):
        group = StudentGroup.objects.create(name='9А')

        response = self.client.post(
            reverse('students:group-update', args=[group.pk]),
            data={
                'name': '9А-1',
                'students': [str(self.student.pk)],
            },
        )

        group.refresh_from_db()
        self.assertRedirects(
            response,
            reverse('students:group-detail', args=[group.pk]),
            fetch_redirect_response=False,
        )
        self.assertEqual(group.name, '9А-1')
        self.assertEqual(list(group.students.all()), [self.student])

    def test_update_student_group_returns_404_for_missing_group(self):
        response = self.client.get(
            reverse(
                'students:group-update',
                args=['550e8400-e29b-41d4-a716-446655440000'],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_student_group_pages_contain_user_edit_links(self):
        group = StudentGroup.objects.create(name='9А')

        list_response = self.client.get(reverse('students:group-list'))
        detail_response = self.client.get(
            reverse('students:group-detail', args=[group.pk]),
        )

        self.assertContains(
            list_response,
            reverse('students:group-update', args=[group.pk]),
        )
        self.assertContains(
            detail_response,
            reverse('students:group-update', args=[group.pk]),
        )
        self.assertNotContains(detail_response, '/admin/students/studentgroup/')

    def test_get_shows_remedial_preview_analysis_for_event(self):
        response = self.client.get(
            reverse('students:remedial-from-event', args=[self.event.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['event'], self.event)
        self.assertEqual(response.context['work'], self.source_work)
        self.assertEqual(response.context['weak_students'], 1)

        analysis = response.context['analysis']
        self.assertEqual(len(analysis), 1)
        row = analysis[0]
        self.assertEqual(row['student'], self.student)
        self.assertEqual(row['variant'], self.source_variant)
        self.assertEqual(row['score_pct'], 71.4)
        self.assertEqual(row['points'], 5.0)
        self.assertEqual(row['max_points'], 7.0)
        self.assertEqual(row['mark_score'], 2)
        self.assertEqual(row['weak_tasks_count'], 1)
        self.assertEqual(row['weak_tasks'], [str(self.weak_original.pk)])
        self.assertEqual(row['status'], 'weak')

    def test_post_creates_remedial_work_variant_and_event_from_weak_groups(self):
        response = self.client.post(
            reverse('students:remedial-from-event', args=[self.event.pk]),
            {
                'selected_students': [str(self.student.pk)],
                'work_name': 'Работа над ошибками 9А',
                'create_event': '1',
                'event_date': '2026-03-10',
            },
        )

        remedial_work = Work.objects.get(name='Работа над ошибками 9А')
        remedial_variant = Variant.objects.get(
            work=remedial_work,
            assigned_student=self.student,
            variant_type='remedial',
        )
        remedial_event = Event.objects.get(work=remedial_work)
        participation = EventParticipation.objects.get(
            event=remedial_event,
            student=self.student,
        )

        self.assertRedirects(
            response,
            reverse('events:detail', args=[remedial_event.pk]),
            fetch_redirect_response=False,
        )
        self.assertEqual(remedial_work.work_type, 'remedial')
        self.assertEqual(remedial_work.variant_counter, 1)
        self.assertEqual(remedial_work.max_score, self.replacement_easy.difficulty)
        self.assertEqual(remedial_variant.source_work, self.source_work)
        self.assertEqual(remedial_variant.max_score_snapshot, self.replacement_easy.difficulty)
        self.assertEqual(remedial_event.status, 'planned')
        self.assertEqual(remedial_event.description, f'Работа над ошибками по: {self.source_work.name}')
        self.assertEqual(participation.variant, remedial_variant)
        self.assertEqual(participation.status, 'assigned')

        variant_task = VariantTask.objects.get(variant=remedial_variant)
        self.assertEqual(variant_task.task, self.replacement_easy)
        self.assertEqual(variant_task.order, 1)
        self.assertEqual(variant_task.max_points, self.replacement_easy.difficulty)
        self.assertEqual(variant_task.weight, self.replacement_easy.difficulty)

    def test_post_without_selected_students_redirects_without_creating_remedial_work(self):
        response = self.client.post(
            reverse('students:remedial-from-event', args=[self.event.pk]),
            {
                'work_name': 'Не должна создаться',
                'create_event': '1',
                'event_date': '2026-03-10',
            },
        )

        self.assertRedirects(
            response,
            reverse('students:remedial-from-event', args=[self.event.pk]),
            fetch_redirect_response=False,
        )
        self.assertFalse(Work.objects.filter(name='Не должна создаться').exists())

    def test_student_remedial_page_uses_clean_context_data(self):
        response = self.client.get(reverse('students:remedial', args=[self.student.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['done_count'], 2)
        self.assertEqual(response.context['total_available'], 2)
        remedial_groups = response.context['remedial_groups']
        self.assertEqual(len(remedial_groups), 1)
        self.assertEqual(remedial_groups[0]['group'], self.weak_group)
        self.assertEqual(remedial_groups[0]['available_count'], 2)
        self.assertEqual(remedial_groups[0]['avg_pct'], 0.0)

    def test_student_remedial_page_handles_student_without_task_logs(self):
        student = Student.objects.create(last_name='Без', first_name='Истории')

        response = self.client.get(reverse('students:remedial', args=[student.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['no_data'])

    def test_student_remedial_post_creates_orphan_variant(self):
        response = self.client.post(
            reverse('students:remedial', args=[self.student.pk]),
            {
                'max_tasks': '5',
                'groups': [str(self.weak_group.pk)],
            },
        )

        variant = Variant.objects.get(
            work__isnull=True,
            assigned_student=self.student,
            variant_type='remedial',
        )
        self.assertRedirects(
            response,
            reverse('works:variant-detail', args=[variant.pk]),
            fetch_redirect_response=False,
        )
        self.assertEqual(variant.work_name_snapshot, 'Работа над ошибками — Иванов И.')
        self.assertEqual(variant.max_score_snapshot, 9)
        variant_tasks = VariantTask.objects.filter(variant=variant)
        self.assertEqual(variant_tasks.count(), 2)
        self.assertEqual(
            {variant_task.task for variant_task in variant_tasks},
            {self.replacement_easy, self.replacement_hard},
        )

    def test_remedial_wizard_step1_uses_clean_start_context(self):
        group = StudentGroup.objects.create(name='9А')

        response = self.client.get(reverse('students:remedial-wizard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['groups']), 1)
        self.assertEqual(response.context['groups'][0].pk, str(group.pk))
        self.assertEqual(str(response.context['groups'][0]), '9А')
        self.assertEqual(response.context['limit_choices'][0][0], 'tasks')

    def test_remedial_wizard_step2_uses_clean_preview_context(self):
        group = StudentGroup.objects.create(name='9А')
        group.students.add(self.student)

        response = self.client.post(
            reverse('students:remedial-wizard'),
            {
                'step': '2',
                'group_id': str(group.pk),
                'threshold': '70',
                'limit_type': 'tasks',
                'limit_value': '10',
                'work_name': 'Работа над ошибками 9А',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['group'], group)
        self.assertEqual(response.context['work_name'], 'Работа над ошибками 9А')
        self.assertEqual(response.context['students_with_tasks'], 1)
        self.assertEqual(response.context['total_tasks'], 1)
        preview = response.context['preview']
        self.assertEqual(len(preview), 1)
        self.assertEqual(preview[0]['student'].pk, str(self.student.pk))
        self.assertEqual(preview[0]['student'].full_name, self.student.get_full_name())
        self.assertEqual(preview[0]['student_level'], 'medium')
        self.assertEqual(preview[0]['tasks_count'], 1)

    def test_remedial_wizard_step3_creates_work_variants_and_event(self):
        group = StudentGroup.objects.create(name='9А')
        group.students.add(self.student)

        response = self.client.post(
            reverse('students:remedial-wizard'),
            {
                'step': '3',
                'group_id': str(group.pk),
                'work_name': 'Работа над ошибками 9А',
                'create_event': '1',
                'event_date': '2026-03-10',
                'selected_students': [str(self.student.pk)],
                f'task_ids_{self.student.pk}': (
                    f'{self.replacement_easy.pk},{self.replacement_hard.pk}'
                ),
            },
        )

        work = Work.objects.get(name='Работа над ошибками 9А')
        event = Event.objects.get(work=work)
        variant = Variant.objects.get(work=work, assigned_student=self.student)
        participation = EventParticipation.objects.get(event=event)

        self.assertRedirects(
            response,
            reverse('events:detail', args=[event.pk]),
            fetch_redirect_response=False,
        )
        self.assertEqual(work.work_type, 'remedial')
        self.assertEqual(work.max_score, 9)
        self.assertEqual(work.variant_counter, 1)
        self.assertEqual(event.description, 'Работа над ошибками для 9А')
        self.assertEqual(variant.variant_type, 'remedial')
        self.assertEqual(variant.max_score_snapshot, 9)
        self.assertEqual(participation.student, self.student)
        self.assertEqual(participation.variant, variant)

    def test_remedial_solutions_open_for_orphan_remedial_variant(self):
        remedial_variant = Variant.objects.create(
            work=None,
            number=1,
            work_name_snapshot='Работа над ошибками',
            max_score_snapshot=3,
            variant_type='remedial',
            assigned_student=self.student,
            source_work=self.source_work,
        )
        VariantTask.objects.create(
            variant=remedial_variant,
            task=self.replacement_easy,
            order=1,
            max_points=3,
            weight=3,
        )

        response = self.client.get(
            reverse('students:remedial-solutions', args=[remedial_variant.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['variant'], remedial_variant)
        self.assertEqual(response.context['student'].pk, str(self.student.pk))
        self.assertEqual(response.context['student'].short_name, self.student.get_short_name())
        self.assertEqual(response.context['source_work'], self.source_work)
        self.assertEqual(response.context['new_tasks'].count(), 1)
        self.assertEqual(len(response.context['original_tasks']), 2)
        self.assertEqual(response.context['original_tasks'][0].status, 'fail')
        self.assertEqual(response.context['original_tasks'][0].group_name, 'Скорость')
        self.assertEqual(response.context['original_tasks'][1].status, 'ok')
        self.assertContains(response, 'К варианту')

    def test_remedial_solutions_redirect_orphan_without_source_work_to_variant(self):
        orphan_variant = Variant.objects.create(
            work=None,
            number=1,
            work_name_snapshot='Сирота',
            variant_type='remedial',
            assigned_student=self.student,
        )

        response = self.client.get(
            reverse('students:remedial-solutions', args=[orphan_variant.pk])
        )

        self.assertRedirects(
            response,
            reverse('works:variant-detail', args=[orphan_variant.pk]),
            fetch_redirect_response=False,
        )

    def test_remedial_solutions_returns_404_for_missing_variant(self):
        response = self.client.get(
            reverse(
                'students:remedial-solutions',
                args=['00000000-0000-0000-0000-000000000000'],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_remedial_solutions_requires_assigned_student(self):
        remedial_variant = Variant.objects.create(
            work=None,
            number=1,
            work_name_snapshot='Без ученика',
            variant_type='remedial',
            source_work=self.source_work,
        )

        response = self.client.get(
            reverse('students:remedial-solutions', args=[remedial_variant.pk])
        )

        self.assertRedirects(
            response,
            reverse('works:variant-detail', args=[remedial_variant.pk]),
            fetch_redirect_response=False,
        )

    def test_student_detail_uses_profile_context_from_clean_use_case(self):
        group = StudentGroup.objects.create(name='9А')
        group.students.add(self.student)

        response = self.client.get(reverse('students:detail', args=[self.student.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['student'].pk, str(self.student.pk))
        self.assertEqual(
            response.context['student'].full_name,
            self.student.get_full_name(),
        )
        self.assertEqual(response.context['student_groups'][0].name, '9А')
        self.assertEqual(response.context['stats']['total_works'], 1)
        self.assertEqual(response.context['stats']['graded_works'], 1)
        self.assertEqual(response.context['stats']['avg_score'], 2)
        self.assertEqual(response.context['stats']['student_level'], 'medium')
        self.assertEqual(response.context['task_log_stats']['total'], 2)
        heatmap_group_names = {
            row['name'] for row in response.context['heatmap_groups']
        }
        self.assertIn('Скорость', heatmap_group_names)
        self.assertEqual(response.context['group_scores'][0]['name'], 'Скорость')
        self.assertEqual(response.context['participations_data'][0].score, 2)

    def test_student_detail_returns_404_for_missing_student(self):
        response = self.client.get(
            reverse(
                'students:detail',
                args=['550e8400-e29b-41d4-a716-446655440000'],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_student_list_uses_clean_list_context(self):
        response = self.client.get(reverse('students:list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['students'][0].pk, str(self.student.pk))
        self.assertEqual(
            response.context['students'][0].last_name,
            self.student.last_name,
        )

    def test_student_group_list_uses_clean_list_context(self):
        group = StudentGroup.objects.create(name='9А')
        group.students.add(self.student)

        response = self.client.get(reverse('students:group-list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['student_groups'][0].pk, str(group.pk))
        self.assertEqual(response.context['student_groups'][0].name, group.name)
        self.assertEqual(response.context['student_groups'][0].students_count, 1)

    def test_student_group_detail_uses_clean_detail_queryset(self):
        group = StudentGroup.objects.create(name='9А')
        group.students.add(self.student)

        response = self.client.get(reverse('students:group-detail', args=[group.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['studentgroup'].pk, str(group.pk))
        self.assertEqual(response.context['studentgroup'].name, group.name)
        self.assertEqual(response.context['studentgroup'].students_count, 1)
        self.assertEqual(
            response.context['studentgroup'].students[0].pk,
            str(self.student.pk),
        )

    def test_student_group_detail_returns_404_for_missing_group(self):
        response = self.client.get(
            reverse(
                'students:group-detail',
                args=['550e8400-e29b-41d4-a716-446655440000'],
            )
        )

        self.assertEqual(response.status_code, 404)
