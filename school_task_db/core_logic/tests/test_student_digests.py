import datetime as dt
from unittest import TestCase

from core_logic.entities.student_digest import (
    StudentDigestEntryFact,
    StudentDigestGroupRef,
    StudentDigestOptions,
    StudentDigestRequest,
    StudentDigestSource,
    StudentDigestStudentRef,
    StudentDigestStudentSource,
    StudentDigestTaskResultFact,
)
from core_logic.services.student_digest_service import StudentDigestService
from core_logic.use_cases.get_student_digests import GetStudentDigestsUseCase


class FakeStudentDigestRepository:
    def __init__(self, source):
        self.source = source

    def get_digest_groups(self, year):
        return (self.source.group,)

    def get_student_digest_source(self, group_id, start_date, end_date):
        if group_id != self.source.group.pk:
            return None
        return self.source


class StudentDigestTests(TestCase):
    def setUp(self):
        self.source = StudentDigestSource(
            group=StudentDigestGroupRef(pk='group-1', name='9А'),
            students=(
                StudentDigestStudentSource(
                    student=StudentDigestStudentRef(
                        pk='student-1',
                        full_name='Иванов Иван',
                    ),
                    entries=(
                        StudentDigestEntryFact(
                            event_id='event-1',
                            event_name='Контрольная',
                            work_name='Механика',
                            subject='Физика',
                            planned_date=dt.date(2026, 7, 15),
                            status='graded',
                            score=2,
                            points=3,
                            max_points=8,
                            recommendations='Повторить формулы',
                            teacher_comment='Проверить оформление решения',
                            task_results=(
                                StudentDigestTaskResultFact(
                                    topic_name='Динамика',
                                    subject='Физика',
                                    points=0,
                                    max_points=2,
                                    comment='Ошибка в формуле',
                                ),
                                StudentDigestTaskResultFact(
                                    topic_name='Импульс',
                                    subject='Физика',
                                    points=2,
                                    max_points=2,
                                    comment='Верное решение',
                                ),
                                StudentDigestTaskResultFact(
                                    topic_name='Разобранный пример',
                                    subject='Физика',
                                    points=0,
                                    max_points=2,
                                    comment='Не оценивать',
                                    is_assessable=False,
                                ),
                            ),
                        ),
                        StudentDigestEntryFact(
                            event_id='event-2',
                            event_name='Самостоятельная',
                            work_name='Импульс',
                            subject='Физика',
                            planned_date=dt.date(2026, 7, 18),
                            status='absent',
                        ),
                    ),
                ),
            ),
        )

    def test_builds_digest_with_focus_and_retake_items(self):
        digest = StudentDigestService().build(
            self.source,
            StudentDigestOptions(),
        )[0]

        self.assertEqual(digest.student.full_name, 'Иванов Иван')
        self.assertEqual(digest.average_score, 2)
        self.assertEqual(digest.grades_count, 1)
        self.assertEqual(digest.absent_count, 1)
        self.assertEqual(len(digest.retake_entries), 2)
        self.assertEqual(
            digest.focus_items,
            ('Повторить формулы', 'Повторить: Динамика'),
        )
        self.assertEqual(digest.subjects[0].title, 'Физика')
        self.assertEqual(digest.subjects[0].entries[0].teacher_comment, '')
        self.assertNotIn('Ошибка в формуле', digest.focus_items)

    def test_includes_teacher_comments_only_when_requested(self):
        digest = StudentDigestService().build(
            self.source,
            StudentDigestOptions(include_teacher_comments=True),
        )[0]

        self.assertEqual(
            digest.subjects[0].entries[0].teacher_comment,
            'Проверить оформление решения',
        )
        self.assertNotIn(
            'Проверить оформление решения',
            digest.focus_items,
        )

    def test_includes_task_comments_in_focus_only_when_requested(self):
        digest = StudentDigestService().build(
            self.source,
            StudentDigestOptions(include_task_comments=True),
        )[0]

        self.assertIn('Ошибка в формуле', digest.focus_items)
        self.assertNotIn('Верное решение', digest.focus_items)
        self.assertNotIn('Не оценивать', digest.focus_items)

    def test_deduplicates_atomic_focus_items_across_works(self):
        repeated = self.source.students[0].entries[0]
        source = StudentDigestSource(
            group=self.source.group,
            students=(
                StudentDigestStudentSource(
                    student=self.source.students[0].student,
                    entries=(repeated, repeated),
                ),
            ),
        )

        digest = StudentDigestService().build(
            source,
            StudentDigestOptions(),
        )[0]

        self.assertEqual(
            digest.focus_items,
            ('Повторить формулы', 'Повторить: Динамика'),
        )

    def test_can_hide_absences_and_raise_retake_threshold(self):
        digest = StudentDigestService().build(
            self.source,
            StudentDigestOptions(
                include_absences=False,
                retake_score_threshold=1,
            ),
        )[0]

        self.assertEqual(digest.absent_count, 0)
        self.assertEqual(digest.retake_entries, ())

    def test_use_case_returns_groups_period_and_digests(self):
        result = GetStudentDigestsUseCase(
            FakeStudentDigestRepository(self.source),
        ).execute(
            StudentDigestRequest(
                group_id='group-1',
                start_date=dt.date(2026, 7, 14),
                end_date=dt.date(2026, 7, 20),
            )
        )

        self.assertEqual(result.selected_group.name, '9А')
        self.assertEqual(result.students[0].pk, 'student-1')
        self.assertEqual(len(result.digests), 1)

    def test_use_case_filters_digests_to_selected_student(self):
        second_student = StudentDigestStudentSource(
            student=StudentDigestStudentRef(
                pk='student-2',
                full_name='Петров Пётр',
            ),
            entries=self.source.students[0].entries,
        )
        source = StudentDigestSource(
            group=self.source.group,
            students=(*self.source.students, second_student),
        )

        result = GetStudentDigestsUseCase(
            FakeStudentDigestRepository(source),
        ).execute(
            StudentDigestRequest(
                group_id='group-1',
                student_id='student-2',
                start_date=dt.date(2026, 7, 14),
                end_date=dt.date(2026, 7, 20),
            )
        )

        self.assertEqual(len(result.students), 2)
        self.assertEqual(result.selected_student.pk, 'student-2')
        self.assertEqual(len(result.digests), 1)
        self.assertEqual(result.digests[0].student.pk, 'student-2')

    def test_rejects_reversed_period(self):
        use_case = GetStudentDigestsUseCase(
            FakeStudentDigestRepository(self.source),
        )

        with self.assertRaisesRegex(ValueError, 'Начало периода'):
            use_case.execute(
                StudentDigestRequest(
                    start_date=dt.date(2026, 7, 20),
                    end_date=dt.date(2026, 7, 14),
                )
            )
