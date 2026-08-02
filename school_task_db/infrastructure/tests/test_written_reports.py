import datetime as dt

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import AcademicYear
from core_logic.entities.event_performance_report import (
    EventReportNarrative,
    SaveEventReportNarrativeParams,
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
from students.models import Student, StudentGroup
from tasks.models import Task
from works.models import Variant, VariantTask, Work


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
            task_type='computational',
            difficulty=2,
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
        self.variant_task = VariantTask.objects.create(
            variant=self.variant,
            task=self.task,
            source_selection_id='spec-row-1',
            content_order=1,
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

    def test_event_report_repository_returns_normalized_attempt_facts(self):
        repo = DjangoEventPerformanceReportRepository()

        source = repo.get_event_report_source(str(self.event.pk))

        self.assertEqual(source.event.name, self.event.name)
        self.assertEqual(len(source.participants), 2)
        self.assertEqual(source.participants[0].score, 2)
        self.assertEqual(len(source.task_scores), 1)
        self.assertEqual(source.task_scores[0].group_key, 'spec-row-1')
        self.assertEqual(source.task_scores[0].points, 0)
        self.assertEqual(source.task_scores[0].comment, 'Ошибка в формуле')

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

    def test_student_digest_repository_returns_marks_and_absences(self):
        repo = DjangoStudentDigestRepository()

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
        self.assertIn('Динамика: Второй закон Ньютона', html)

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
