from datetime import datetime
from unittest import TestCase

from core_logic.entities.student import (
    EventRef,
    MarkRef,
    ObjectRef,
    StudentGroupRef,
    StudentParticipationProfile,
    StudentTaskLogProfile,
    WorkGroupRef,
    WorkRef,
)
from core_logic.services.analytics_service import StudentAnalyticsService


class StudentAnalyticsServiceTests(TestCase):
    def test_build_profile_calculates_stats_level_heatmaps_and_group_scores(self):
        service = StudentAnalyticsService()
        work = WorkRef(
            pk='w1',
            name='Контрольная',
            work_type='test',
            work_type_display='Контрольная работа',
        )

        profile = service.build_profile(
            student_groups=[StudentGroupRef(pk='g1', name='9А')],
            participations=[
                StudentParticipationProfile(
                    participation=ObjectRef(pk='p1'),
                    event=EventRef(
                        pk='e1',
                        name='КР',
                        planned_date=datetime(2026, 3, 10),
                    ),
                    work=work,
                    mark=MarkRef(pk='m1', score=2, points=3, max_points=5),
                    score=2,
                    is_absent=False,
                    variant_number=1,
                ),
                StudentParticipationProfile(
                    participation=ObjectRef(pk='p2'),
                    event=EventRef(pk='e2', name='Пропуск'),
                    work=work,
                    mark=None,
                    score=None,
                    is_absent=True,
                ),
            ],
            task_logs=[
                StudentTaskLogProfile(
                    task=ObjectRef(pk='t1', name='Задание 1'),
                    event=ObjectRef(pk='e1', name='КР'),
                    topic_name='Кинематика',
                    analog_group=ObjectRef(pk='ag1', name='Скорость'),
                    difficulty=2,
                    points=0,
                    max_points=2,
                    is_correct=False,
                    percentage=0,
                    completed_at=datetime(2026, 3, 10),
                ),
                StudentTaskLogProfile(
                    task=ObjectRef(pk='t2', name='Задание 2'),
                    event=ObjectRef(pk='e1', name='КР'),
                    topic_name='Кинематика',
                    analog_group=ObjectRef(pk='ag1', name='Скорость'),
                    difficulty=4,
                    points=4,
                    max_points=5,
                    is_correct=True,
                    percentage=80,
                    completed_at=datetime(2026, 3, 10),
                ),
            ],
            work_group_refs=[
                WorkGroupRef(work_id='w1', group_id='ag1', group_name='Скорость'),
            ],
        )

        self.assertEqual(profile.student_groups[0].name, '9А')
        self.assertEqual(profile.stats['total_works'], 2)
        self.assertEqual(profile.stats['graded_works'], 1)
        self.assertEqual(profile.stats['absent_count'], 1)
        self.assertEqual(profile.stats['avg_score'], 2)
        self.assertEqual(profile.stats['attendance_rate'], 50)
        self.assertEqual(profile.stats['score_counts'][2], 1)
        self.assertEqual(profile.stats['student_level'], 'weak')
        self.assertEqual(profile.stats['overall_avg'], 40)
        self.assertEqual(profile.scores_timeline[0].date, '10.03.2026')
        self.assertEqual(profile.task_log_stats['total'], 2)
        self.assertEqual(profile.task_log_stats['correct'], 1)
        self.assertEqual(profile.task_log_stats['wrong'], 1)
        self.assertEqual(profile.task_log_stats['avg_pct'], 40)
        self.assertEqual(profile.heatmap_groups[0]['name'], 'Скорость')
        self.assertEqual(profile.heatmap_groups[0]['avg_pct'], 40)
        self.assertEqual(profile.heatmap_topics[0]['name'], 'Кинематика')
        self.assertEqual(
            [cell['name'] for cell in profile.heatmap_difficulty],
            ['Сложность 2', 'Сложность 4'],
        )
        self.assertEqual(profile.group_scores[0]['avg'], 2)
