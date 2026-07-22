from unittest import TestCase

from core_logic.entities.review import (
    EventReviewParticipationRow,
    ReviewEventProgress,
    ReviewEventRef,
    ReviewMarkRef,
    ReviewParticipationRef,
    ReviewStudentRef,
    ReviewTaskRef,
    ReviewVariantRef,
    ReviewVariantTaskRef,
)
from core_logic.services.review_service import ReviewService


class ReviewServiceTests(TestCase):
    def test_calculate_score_uses_review_thresholds(self):
        service = ReviewService()

        self.assertEqual(service.calculate_score(9, 10).score, 5)
        self.assertEqual(service.calculate_score(7, 10).score, 4)
        self.assertEqual(service.calculate_score(5, 10).score, 3)
        self.assertEqual(service.calculate_score(4, 10).score, 2)
        self.assertEqual(service.calculate_score(1, 0).percentage, 0)

    def test_parse_submission_returns_grade_fields_and_task_scores(self):
        service = ReviewService()

        submission = service.parse_submission({
            'score': '4',
            'points': '7',
            'max_points': '10',
            'teacher_comment': 'Хорошо',
            'mistakes_analysis': 'Повторить формулы',
            'recommendations': 'Решить ещё',
            'task_task-1': '2',
            'task_task-1_max': '3',
            'task_task-1_comment': 'Верно',
        })

        self.assertEqual(submission.score, 4)
        self.assertEqual(submission.points, 7)
        self.assertEqual(submission.max_points, 10)
        self.assertEqual(submission.teacher_comment, 'Хорошо')
        self.assertEqual(
            submission.task_scores,
            {
                'task-1': {
                    'points': 2,
                    'max_points': 3,
                    'comment': 'Верно',
                }
            },
        )

    def test_parse_submission_tolerates_empty_numbers(self):
        submission = ReviewService().parse_submission({
            'score': '',
            'points': '',
            'max_points': 'bad',
            'task_task-1': '',
            'task_task-1_max': 'bad',
        })

        self.assertIsNone(submission.score)
        self.assertIsNone(submission.points)
        self.assertIsNone(submission.max_points)
        self.assertEqual(submission.task_scores['task-1']['points'], 0)
        self.assertEqual(submission.task_scores['task-1']['max_points'], 5)

    def test_parse_submission_accepts_variant_task_score_keys(self):
        submission = ReviewService().parse_submission({
            'task_variant-task-1': '2',
            'task_variant-task-1_max': '3',
            'task_variant-task-1_comment': 'Верно',
            'task_variant-task-1_task_id': 'task-1',
            'task_variant-task-1_variant_task_id': 'variant-task-1',
        })

        self.assertEqual(
            submission.task_scores,
            {
                'variant-task-1': {
                    'points': 2,
                    'max_points': 3,
                    'comment': 'Верно',
                    'task_id': 'task-1',
                    'variant_task_id': 'variant-task-1',
                }
            },
        )

    def test_validate_work_scan_accepts_supported_files(self):
        validation = ReviewService().validate_work_scan(
            size=1024,
            content_type='application/pdf',
        )

        self.assertTrue(validation.accepted)
        self.assertEqual(validation.warning, '')

    def test_validate_work_scan_rejects_large_or_unsupported_files(self):
        service = ReviewService()

        large = service.validate_work_scan(
            size=11 * 1024 * 1024,
            content_type='application/pdf',
        )
        unsupported = service.validate_work_scan(
            size=1024,
            content_type='text/plain',
        )

        self.assertFalse(large.accepted)
        self.assertIn('Файл слишком большой', large.warning)
        self.assertFalse(unsupported.accepted)
        self.assertIn('Неподдерживаемый формат', unsupported.warning)

    def test_build_dashboard_categorizes_events_by_status_and_progress(self):
        service = ReviewService()

        dashboard = service.build_dashboard([
            ReviewEventProgress(
                event=ReviewEventRef(pk='e1', name='План', status='planned'),
                total_participants=2,
                active_participants=2,
                graded_participants=0,
                absent_participants=0,
                progress_percentage=0,
                remaining=2,
            ),
            ReviewEventProgress(
                event=ReviewEventRef(pk='e2', name='Начата', status='completed'),
                total_participants=2,
                active_participants=2,
                graded_participants=1,
                absent_participants=0,
                progress_percentage=50,
                remaining=1,
            ),
            ReviewEventProgress(
                event=ReviewEventRef(pk='e3', name='Готова', status='graded'),
                total_participants=2,
                active_participants=2,
                graded_participants=2,
                absent_participants=0,
                progress_percentage=100,
                remaining=0,
            ),
        ])

        self.assertEqual([row.event.pk for row in dashboard.needs_review], ['e1'])
        self.assertEqual([row.event.pk for row in dashboard.in_progress], ['e2'])
        self.assertEqual([row.event.pk for row in dashboard.fully_graded], ['e3'])
        self.assertEqual(dashboard.total_events, 3)

    def test_build_event_review_calculates_progress_and_score_distribution(self):
        service = ReviewService()
        event = ReviewEventRef(pk='event-1', name='КР')
        student = ReviewStudentRef(pk='s1', last_name='А', first_name='А')
        participation = ReviewParticipationRef(pk='p1', student=student, event=event)

        review = service.build_event_review(
            participations=[
                EventReviewParticipationRow(
                    participation=participation,
                    mark=ReviewMarkRef(pk='m1', score=4, points=8, max_points=10),
                    has_mark=True,
                    is_absent=False,
                    student=student,
                    variant=ReviewVariantRef(pk='v1', number=1),
                ),
                EventReviewParticipationRow(
                    participation=ReviewParticipationRef(
                        pk='p2',
                        student=ReviewStudentRef(pk='s2', last_name='Б', first_name='Б'),
                        event=event,
                    ),
                    mark=None,
                    has_mark=False,
                    is_absent=False,
                    student=ReviewStudentRef(pk='s2', last_name='Б', first_name='Б'),
                    variant=ReviewVariantRef(pk='v2', number=2),
                ),
            ],
            available_variants=[],
        )

        self.assertFalse(review.blocked)
        self.assertEqual(review.active_participants, 2)
        self.assertEqual(review.graded_participants, 1)
        self.assertEqual(review.progress_percentage, 50)
        self.assertEqual(review.avg_score, 4)
        self.assertEqual(review.score_distribution[4], 1)

    def test_build_task_score_rows_uses_existing_scores_and_variant_weights(self):
        service = ReviewService()
        task = ReviewTaskRef(id='task-1', text='Задание', difficulty=2)

        rows = service.build_task_score_rows(
            variant_tasks=[
                ReviewVariantTaskRef(
                    task=task,
                    variant_task_id='variant-task-1',
                    weight=3,
                ),
            ],
            existing_scores={
                'task-1': {
                    'points': 2,
                    'max_points': 3,
                    'comment': 'Верно',
                }
            },
        )

        self.assertEqual(rows[0].task, task)
        self.assertEqual(rows[0].number, 1)
        self.assertEqual(rows[0].points, 2)
        self.assertEqual(rows[0].max_points, 3)
        self.assertEqual(rows[0].variant_task_id, 'variant-task-1')
        self.assertEqual(rows[0].score_key, 'variant-task-1')
        self.assertEqual(rows[0].comment, 'Верно')

    def test_build_task_score_rows_prefers_existing_variant_task_scores(self):
        service = ReviewService()
        task = ReviewTaskRef(id='task-1', text='Задание', difficulty=2)

        rows = service.build_task_score_rows(
            variant_tasks=[
                ReviewVariantTaskRef(
                    task=task,
                    variant_task_id='variant-task-1',
                    weight=3,
                ),
            ],
            existing_scores={
                'task-1': {'points': 1, 'max_points': 3},
                'variant-task-1': {
                    'points': 2,
                    'max_points': 3,
                    'comment': 'По snapshot-строке',
                },
            },
        )

        self.assertEqual(rows[0].points, 2)
        self.assertEqual(rows[0].comment, 'По snapshot-строке')

    def test_build_task_score_rows_falls_back_to_payload_task_id(self):
        service = ReviewService()
        task = ReviewTaskRef(id='task-1', text='Задание', difficulty=2)

        rows = service.build_task_score_rows(
            variant_tasks=[
                ReviewVariantTaskRef(
                    task=task,
                    variant_task_id='variant-task-1',
                    weight=3,
                ),
            ],
            existing_scores={
                'stored-score-row-1': {
                    'task_id': 'task-1',
                    'points': 2,
                    'max_points': 3,
                    'comment': 'По task_id внутри payload',
                },
            },
        )

        self.assertEqual(rows[0].points, 2)
        self.assertEqual(rows[0].max_points, 3)
        self.assertEqual(rows[0].comment, 'По task_id внутри payload')

    def test_filters_assessable_variant_tasks(self):
        service = ReviewService()
        assessable_task = ReviewVariantTaskRef(
            task=ReviewTaskRef(id='task-1', text='Задание'),
            weight=3,
        )
        demo_task = ReviewVariantTaskRef(
            task=ReviewTaskRef(id='task-demo', text='Демо'),
            weight=10,
            is_assessable=False,
        )

        result = service.assessable_variant_tasks(
            [demo_task, assessable_task],
        )

        self.assertEqual(result, [assessable_task])

    def test_build_navigation_returns_neighbors_and_progress(self):
        service = ReviewService()
        event = ReviewEventRef(pk='event-1', name='КР')
        participations = [
            ReviewParticipationRef(
                pk='p1',
                student=ReviewStudentRef(pk='s1', last_name='А', first_name='А'),
                event=event,
            ),
            ReviewParticipationRef(
                pk='p2',
                student=ReviewStudentRef(pk='s2', last_name='Б', first_name='Б'),
                event=event,
            ),
            ReviewParticipationRef(
                pk='p3',
                student=ReviewStudentRef(pk='s3', last_name='В', first_name='В'),
                event=event,
            ),
        ]

        nav = service.build_navigation(participations, 'p2')

        self.assertEqual(nav.previous_participation.pk, 'p1')
        self.assertEqual(nav.next_participation.pk, 'p3')
        self.assertEqual(nav.current_position, 2)
        self.assertEqual(nav.total_positions, 3)
        self.assertEqual(nav.navigation_progress, 66.7)
