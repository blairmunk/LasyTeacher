import datetime as dt

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import AcademicYear
from codifier.models import CodifierSpec, ContentEntry, Requirement
from core_logic.entities.event_performance_report import (
    EventReportNarrative,
    SaveEventReportNarrativeParams,
)
from core_logic.services.event_performance_report_service import (
    EventPerformanceReportService,
)
from core_logic.value_objects.document_recipes import (
    EVENT_PERFORMANCE_REPORT_DOCUMENT_TYPE,
)
from curriculum.models import Course, SubTopic, Topic
from document_engine.models import PrintSettings
from events.models import Event, EventParticipation, Mark
from infrastructure.repositories.django_event_performance_report_repo import (
    DjangoEventPerformanceReportRepository,
)
from infrastructure.repositories.django_student_digest_repo import (
    DjangoStudentDigestRepository,
)
from infrastructure.tests.variant_task_factory import (
    capture_attempt_snapshot,
    create_variant_task,
)
from students.models import Student, StudentGroup
from tasks.models import Task
from works.models import Variant, Work


class WrittenReportRepositoryTests(TestCase):
    def setUp(self):
        self.year = AcademicYear.objects.create(
            name='2026-2027',
            start_date=dt.date(2026, 9, 1),
            end_date=dt.date(2027, 8, 31),
            is_active=True,
        )
        self.group = StudentGroup.objects.create(
            name='9А',
            academic_year=self.year,
        )
        self.student = Student.objects.create(
            last_name='Иванов',
            first_name='Иван',
        )
        self.absent_student = Student.objects.create(
            last_name='Петров',
            first_name='Пётр',
        )
        self.group.students.add(self.student, self.absent_student)
        self.topic = Topic.objects.create(
            name='Динамика',
            subject='Физика',
            section='Механика',
            grade_level=9,
        )
        self.subtopic = SubTopic.objects.create(
            topic=self.topic,
            name='Второй закон Ньютона',
        )
        self.task = Task.objects.create(
            text='Найти силу',
            answer='10 Н',
            topic=self.topic,
            subtopic=self.subtopic,
            content_element='1.2',
            requirement_element='2.1',
            task_type='computational',
            difficulty=2,
        )
        self.codifier = CodifierSpec.objects.create(
            name='ОГЭ по физике 2026',
            short_name='ОГЭ 2026',
            subject='Физика',
            exam_type='oge',
            year=2026,
        )
        self.requirement = Requirement.objects.create(
            codifier=self.codifier,
            code='2.3',
            name='Применять физические законы',
        )
        self.requirement.tasks.add(self.task)
        self.content_entry = ContentEntry.objects.create(
            codifier=self.codifier,
            code='1.2',
            name='Применение второго закона Ньютона',
            topic=self.topic,
            subtopic=self.subtopic,
        )
        self.work = Work.objects.create(
            name='Контрольная по динамике',
            work_type='test',
        )
        self.variant = Variant.objects.create(
            work=self.work,
            number=1,
            work_name_snapshot=self.work.name,
        )
        self.variant_task = create_variant_task(
            variant=self.variant,
            task=self.task,
            source_selection_id='spec-row-1',
            content_order=30,
            order=1,
            max_points=2,
            is_assessable=True,
        )
        self.course = Course.objects.create(
            name='Физика 9',
            subject='Физика',
            grade_level=9,
            year=self.year,
        )
        self.course.student_groups.add(self.group)
        self.event = Event.objects.create(
            name='Контрольная 9А',
            work=self.work,
            course=self.course,
            planned_date=timezone.make_aware(
                dt.datetime(2026, 10, 15, 9, 0),
            ),
            status='graded',
        )
        self.participation = EventParticipation.objects.create(
            event=self.event,
            student=self.student,
            variant=self.variant,
            status='graded',
        )
        self.absent_participation = EventParticipation.objects.create(
            event=self.event,
            student=self.absent_student,
            variant=self.variant,
            status='absent',
        )
        self.mark = Mark.objects.create(
            participation=self.participation,
            score=2,
            points=0,
            max_points=2,
            mistakes_analysis='Не записана формула',
            recommendations='Повторить второй закон Ньютона',
            teacher_comment='Нужна консультация',
            needs_attention=True,
            task_scores={
                str(self.variant_task.pk): {
                    'task_id': str(self.task.pk),
                    'variant_task_id': str(self.variant_task.pk),
                    'points': 0,
                    'max_points': 2,
                    'comment': 'Ошибка в формуле',
                },
            },
        )
        self.attempt = capture_attempt_snapshot(self.mark)

    def test_event_report_repository_returns_normalized_attempt_facts(self):
        repo = DjangoEventPerformanceReportRepository()

        source = repo.get_event_report_source(str(self.event.pk))

        self.assertEqual(source.event.name, self.event.name)
        self.assertEqual(len(source.participants), 2)
        self.assertEqual(source.participants[0].score, 2)
        self.assertEqual(len(source.task_scores), 1)
        self.assertEqual(
            source.task_scores[0].group_key,
            f'selection:{self.variant_task.source_selection_id}:slot:1',
        )
        self.assertEqual(source.task_scores[0].order, 1)
        self.assertEqual(source.task_scores[0].points, 0)
        self.assertEqual(source.task_scores[0].comment, 'Ошибка в формуле')
        self.assertEqual(source.specification[0].order, 1)
        self.assertEqual(source.specification[0].content_element, '1.2')
        self.assertEqual(source.specification[0].requirement_element, '2.1')
        self.assertEqual(
            source.specification[0].codifier_requirements,
            ('ОГЭ 2026: 2.3',),
        )
        self.assertEqual(
            source.specification[0].content_element_descriptions,
            ('ОГЭ 2026: Применение второго закона Ньютона',),
        )

    def test_event_report_groups_reordered_variants_by_specification_slot(self):
        second_variant = Variant.objects.create(
            work=self.work,
            number=2,
            work_name_snapshot=self.work.name,
        )
        second_variant_task = create_variant_task(
            variant=second_variant,
            task=self.task,
            source_selection_id='spec-row-1',
            content_order=30,
            order=2,
            max_points=2,
            is_assessable=True,
        )
        self.absent_participation.variant = second_variant
        self.absent_participation.status = 'graded'
        self.absent_participation.save(
            update_fields=['variant', 'status'],
        )
        second_mark = Mark.objects.create(
            participation=self.absent_participation,
            score=4,
            points=1,
            max_points=2,
            task_scores={
                str(second_variant_task.pk): {
                    'task_id': str(self.task.pk),
                    'variant_task_id': str(second_variant_task.pk),
                    'points': 1,
                    'max_points': 2,
                },
            },
        )
        capture_attempt_snapshot(second_mark)

        source = DjangoEventPerformanceReportRepository().get_event_report_source(
            str(self.event.pk),
        )
        report = EventPerformanceReportService().build(source)

        self.assertEqual(
            {fact.group_key for fact in source.task_scores},
            {'selection:spec-row-1:slot:1'},
        )
        self.assertEqual(len(report.task_summaries), 1)
        self.assertEqual(report.task_summaries[0].attempts, 2)
        self.assertEqual(len(report.specification_items), 1)

    def test_written_reports_ignore_uncaptured_mark_changes(self):
        self.mark.score = 5
        self.mark.recommendations = 'Несохранённая рекомендация'
        self.mark.task_scores[str(self.variant_task.pk)]['points'] = 2
        self.mark.save()

        event_source = (
            DjangoEventPerformanceReportRepository()
            .get_event_report_source(str(self.event.pk))
        )
        digest_source = DjangoStudentDigestRepository().get_student_digest_source(
            str(self.group.pk),
            start_date=dt.date(2026, 10, 13),
            end_date=dt.date(2026, 10, 19),
        )

        self.assertEqual(event_source.participants[0].score, 2)
        self.assertEqual(event_source.task_scores[0].points, 0)
        digest_entry = digest_source.students[0].entries[0]
        self.assertEqual(digest_entry.score, 2)
        self.assertEqual(
            digest_entry.recommendations,
            'Повторить второй закон Ньютона',
        )

    def test_written_reports_use_latest_captured_attempt_revision(self):
        self.mark.score = 4
        self.mark.recommendations = 'Проверить единицы измерения'
        self.mark.task_scores[str(self.variant_task.pk)]['points'] = 1
        self.mark.save()
        capture_attempt_snapshot(self.mark)

        event_source = (
            DjangoEventPerformanceReportRepository()
            .get_event_report_source(str(self.event.pk))
        )
        digest_source = DjangoStudentDigestRepository().get_student_digest_source(
            str(self.group.pk),
            start_date=dt.date(2026, 10, 13),
            end_date=dt.date(2026, 10, 19),
        )

        self.assertEqual(event_source.participants[0].score, 4)
        self.assertEqual(event_source.task_scores[0].points, 1)
        digest_entry = digest_source.students[0].entries[0]
        self.assertEqual(digest_entry.score, 4)
        self.assertEqual(
            digest_entry.recommendations,
            'Проверить единицы измерения',
        )

    def test_event_report_repository_saves_narrative(self):
        repo = DjangoEventPerformanceReportRepository()

        result = repo.save_event_report_narrative(
            SaveEventReportNarrativeParams(
                event_id=str(self.event.pk),
                narrative=EventReportNarrative(
                    possible_causes='Пробелы в формулах',
                    recommendations='Повторить тему',
                    planned_actions='Консультация',
                    additional_notes='Контроль через неделю',
                ),
            )
        )
        source = repo.get_event_report_source(str(self.event.pk))

        self.assertEqual(result.status, 'saved')
        self.assertEqual(source.narrative.planned_actions, 'Консультация')

    def test_event_report_uses_variant_task_metadata_snapshot(self):
        self.task.content_element = '9.9'
        self.task.requirement_element = '9.8'
        self.task.save(update_fields=[
            'content_element',
            'requirement_element',
        ])
        self.requirement.code = '9.7'
        self.requirement.save(update_fields=['code'])
        self.content_entry.name = 'Изменённый элемент содержания'
        self.content_entry.save(update_fields=['name'])

        source = DjangoEventPerformanceReportRepository().get_event_report_source(
            str(self.event.pk),
        )

        self.assertEqual(source.specification[0].content_element, '1.2')
        self.assertEqual(source.specification[0].requirement_element, '2.1')
        self.assertEqual(
            source.specification[0].codifier_requirements,
            ('ОГЭ 2026: 2.3',),
        )
        self.assertEqual(
            source.specification[0].content_element_descriptions,
            ('ОГЭ 2026: Применение второго закона Ньютона',),
        )

    def test_student_digest_repository_returns_marks_and_absences(self):
        repo = DjangoStudentDigestRepository()
        self.topic.name = 'Изменённая тема банка'
        self.topic.save(update_fields=['name'])

        groups = repo.get_digest_groups(self.year)
        source = repo.get_student_digest_source(
            str(self.group.pk),
            start_date=dt.date(2026, 10, 13),
            end_date=dt.date(2026, 10, 19),
        )

        self.assertEqual(groups[0].name, '9А')
        self.assertEqual(len(source.students), 2)
        graded = source.students[0].entries[0]
        absent = source.students[1].entries[0]
        self.assertEqual(graded.score, 2)
        self.assertEqual(graded.subject, 'Физика')
        self.assertEqual(
            graded.failed_topics,
            ('Динамика: Второй закон Ньютона',),
        )
        self.assertEqual(graded.task_comments, ('Ошибка в формуле',))
        self.assertEqual(absent.status, 'absent')

    def test_event_report_view_renders_and_saves_written_sections(self):
        response = self.client.get(
            reverse('reports:event-performance', args=[self.event.pk]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['report'].average_score, 2)
        self.assertContains(response, 'Контрольная 9А')
        self.assertContains(response, 'Динамика: Второй закон Ньютона')
        self.assertContains(response, 'Краткая спецификация работы')
        self.assertContains(response, 'Применение второго закона Ньютона')
        self.assertContains(response, 'Нужна консультация')
        self.assertNotContains(response, 'Найти силу')

        post_response = self.client.post(
            reverse('reports:event-performance', args=[self.event.pk]),
            {
                'possible_causes': 'Недостаточно практики',
                'recommendations': 'Повторить формулы',
                'planned_actions': 'Консультация',
                'additional_notes': 'Проверить через неделю',
            },
        )

        self.assertRedirects(
            post_response,
            reverse('reports:event-performance', args=[self.event.pk]),
            fetch_redirect_response=False,
        )
        source = DjangoEventPerformanceReportRepository().get_event_report_source(
            str(self.event.pk),
        )
        self.assertEqual(source.narrative.recommendations, 'Повторить формулы')

    def test_student_digest_view_renders_individual_sheet(self):
        response = self.client.get(
            reverse('reports:student-digests'),
            {
                'apply': '1',
                'group': str(self.group.pk),
                'start_date': '2026-10-13',
                'end_date': '2026-10-19',
                'include_summary': 'on',
                'include_details': 'on',
                'include_focus': 'on',
                'include_retakes': 'on',
                'include_absences': 'on',
                'retake_score_threshold': '2',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['page'].digests), 2)
        self.assertContains(response, 'Иванов Иван')
        self.assertContains(response, 'Работы к сдаче или пересдаче')
        self.assertContains(response, 'Повторить второй закон Ньютона')
        self.assertNotContains(response, 'Нужна консультация')

        comments_response = self.client.get(
            reverse('reports:student-digests'),
            {
                'apply': '1',
                'group': str(self.group.pk),
                'start_date': '2026-10-13',
                'end_date': '2026-10-19',
                'include_details': 'on',
                'include_teacher_comments': 'on',
            },
        )
        self.assertContains(comments_response, 'Нужна консультация')
        self.assertContains(comments_response, 'Комментарии учителя')

    def test_student_digest_view_and_document_can_select_one_student(self):
        query = {
            'apply': '1',
            'group': str(self.group.pk),
            'student': str(self.student.pk),
            'start_date': '2026-10-13',
            'end_date': '2026-10-19',
            'include_details': 'on',
        }

        response = self.client.get(
            reverse('reports:student-digests'),
            query,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['page'].selected_student.pk, str(self.student.pk))
        self.assertEqual(len(response.context['page'].digests), 1)
        self.assertContains(response, 'Индивидуальный лист: Иванов Иван')

        document_response = self.client.post(
            reverse('reports:student-digests-document'),
            {
                **query,
                'renderer_type': 'html',
                'format': 'A4',
            },
        )
        html = document_response.content.decode('utf-8')

        self.assertEqual(document_response.status_code, 200)
        self.assertIn('Иванов Иван', html)
        self.assertNotIn('Петров Пётр', html)
        self.assertEqual(html.count('report-kicker">Дайджест оценок'), 1)

    def test_event_report_document_endpoint_renders_sectioned_html(self):
        response = self.client.post(
            reverse(
                'reports:event-performance-document',
                args=[self.event.pk],
            ),
            {'renderer_type': 'html', 'format': 'A4'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/html')
        self.assertIn('inline; filename="event_report_', response['Content-Disposition'])
        html = response.content.decode('utf-8')
        self.assertIn('Контрольная 9А', html)
        self.assertIn('document-section-event_report_summary', html)
        self.assertIn(
            'document-section-event_report_specification',
            html,
        )
        self.assertIn('№ 1', html)
        self.assertIn('1.2', html)
        self.assertIn('ОГЭ 2026: 2.3', html)
        self.assertIn('Применение второго закона Ньютона', html)
        self.assertIn('Динамика: Второй закон Ньютона', html)
        self.assertNotIn('Найти силу', html)
        self.assertNotIn('Нужна консультация', html)

    def test_event_report_document_controls_optional_details(self):
        without_details = self.client.post(
            reverse(
                'reports:event-performance-document',
                args=[self.event.pk],
            ),
            {
                'renderer_type': 'html',
                'report_options_submitted': '1',
            },
        )
        with_details = self.client.post(
            reverse(
                'reports:event-performance-document',
                args=[self.event.pk],
            ),
            {
                'renderer_type': 'html',
                'report_options_submitted': '1',
                'include_content_element_text': 'on',
                'include_teacher_notes': 'on',
            },
        )

        compact_html = without_details.content.decode('utf-8')
        detailed_html = with_details.content.decode('utf-8')
        self.assertNotIn('Применение второго закона Ньютона', compact_html)
        self.assertNotIn('Нужна консультация', compact_html)
        self.assertIn('Применение второго закона Ньютона', detailed_html)
        self.assertIn('Нужна консультация', detailed_html)
        self.assertIn(
            'document-section-event_report_teacher_notes',
            detailed_html,
        )

    def test_event_report_document_applies_explicit_presentation_profile(self):
        profile = PrintSettings.objects.create(
            name='Компактный отчёт',
            document_type=EVENT_PERFORMANCE_REPORT_DOCUMENT_TYPE,
            custom_css='.report-metric { min-height: 10mm; }',
        )

        response = self.client.post(
            reverse(
                'reports:event-performance-document',
                args=[self.event.pk],
            ),
            {
                'renderer_type': 'html',
                'format': 'A4',
                'presentation_profile_id': str(profile.pk),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '.report-metric { min-height: 10mm; }',
        )

    def test_student_digest_document_endpoint_renders_one_page_per_student(self):
        response = self.client.post(
            reverse('reports:student-digests-document'),
            {
                'apply': '1',
                'group': str(self.group.pk),
                'start_date': '2026-10-13',
                'end_date': '2026-10-19',
                'include_summary': 'on',
                'include_details': 'on',
                'include_focus': 'on',
                'include_retakes': 'on',
                'include_absences': 'on',
                'retake_score_threshold': '2',
                'renderer_type': 'html',
                'format': 'A4',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/html')
        html = response.content.decode('utf-8')
        self.assertIn('Иванов Иван', html)
        self.assertIn('Петров Пётр', html)
        self.assertEqual(html.count('report-kicker">Дайджест оценок'), 2)
        self.assertEqual(
            html.count(
                'class="document-section document-section-page_break '
                'document-page-break"'
            ),
            1,
        )
        self.assertIn('Работы к сдаче или пересдаче', html)

    def test_digest_document_prints_teacher_comments_without_details(self):
        response = self.client.post(
            reverse('reports:student-digests-document'),
            {
                'apply': '1',
                'group': str(self.group.pk),
                'start_date': '2026-10-13',
                'end_date': '2026-10-19',
                'include_teacher_comments': 'on',
                'renderer_type': 'html',
            },
        )

        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')
        self.assertIn(
            'document-section-student_digest_teacher_comments',
            html,
        )
        self.assertIn('Нужна консультация', html)
        self.assertNotIn('document-section-student_digest_details', html)
