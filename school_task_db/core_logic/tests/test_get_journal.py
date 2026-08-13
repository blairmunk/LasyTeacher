from unittest import TestCase

from core_logic.entities.journal import (
    JournalEntryFact,
    JournalParticipationRef,
    JournalSource,
)
from core_logic.entities.report_refs import (
    ReportCourseRef,
    ReportEventRef,
    ReportGroupRef,
    ReportMarkFact,
    ReportStudentRef,
    ReportWorkRef,
)
from core_logic.use_cases.get_journal import GetJournalUseCase, JournalRequest


class FakeReportRepository:
    def __init__(self):
        self.course_id = None
        self.group_id = None
        self.year = None

    def get_journal_source(self, course_id, group_id, year):
        self.course_id = course_id
        self.group_id = group_id
        self.year = year
        work = ReportWorkRef(
            pk='work-1',
            name='Контрольная',
            work_type='control',
            work_type_display='Контрольная',
            duration=45,
        )
        return JournalSource(
            course=ReportCourseRef(pk='course-1', name='Физика'),
            group=ReportGroupRef(pk='group-1', name='7А'),
            students=[
                ReportStudentRef(pk='student-1', full_name='Иванов Иван'),
                ReportStudentRef(pk='student-2', full_name='Петров Пётр'),
            ],
            events=[
                ReportEventRef(
                    pk='event-1',
                    name='КР',
                    status='graded',
                    status_display='Проверено',
                    planned_date='date',
                    work=work,
                ),
            ],
            entries=[
                JournalEntryFact(
                    student_id='student-1',
                    event_id='event-1',
                    participation=JournalParticipationRef(
                        pk='participation-1',
                        status='graded',
                    ),
                    mark=ReportMarkFact(score=4, points=8, max_points=10),
                ),
            ],
            courses=[ReportCourseRef(pk='course-1', name='Физика')],
        )


class GetJournalUseCaseTests(TestCase):
    def test_execute_returns_repository_data(self):
        repo = FakeReportRepository()
        use_case = GetJournalUseCase(report_repo=repo)

        data = use_case.execute(
            JournalRequest(
                course_id='course-1',
                group_id='group-1',
                year='year',
                show_debts_only=True,
            ),
        )

        self.assertEqual(repo.course_id, 'course-1')
        self.assertEqual(repo.group_id, 'group-1')
        self.assertEqual(repo.year, 'year')
        self.assertEqual(len(data.rows), 1)
        self.assertEqual(data.rows[0].student.pk, 'student-2')
        self.assertEqual(data.rows[0].cells[0].status, 'missing')
        self.assertEqual(data.event_stats[0].graded, 1)
        self.assertEqual(data.event_stats[0].missing, 1)
        self.assertEqual(data.all_rows_count, 2)
        self.assertEqual(data.total_debts, 1)
        self.assertEqual(data.active_report, 'journal')
