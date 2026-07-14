"""Pure student analytics calculations."""

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from core_logic.entities.student import (
    StudentGroupRef,
    StudentLevel,
    StudentParticipationProfile,
    StudentTaskLogProfile,
    WorkGroupRef,
)


@dataclass(frozen=True)
class ScoreTimelinePoint:
    date: str
    score: int
    work: str


@dataclass(frozen=True)
class StudentProfileData:
    student_groups: List[StudentGroupRef] = field(default_factory=list)
    participations_data: List[StudentParticipationProfile] = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    group_scores: List[dict] = field(default_factory=list)
    scores_timeline: List[ScoreTimelinePoint] = field(default_factory=list)
    task_log_stats: Optional[dict] = None
    heatmap_groups: List[dict] = field(default_factory=list)
    heatmap_topics: List[dict] = field(default_factory=list)
    heatmap_difficulty: List[dict] = field(default_factory=list)
    recent_task_log: List[StudentTaskLogProfile] = field(default_factory=list)


class StudentAnalyticsService:
    """Calculates student profile metrics without Django or database access."""

    def build_profile(
        self,
        student_groups: Iterable[StudentGroupRef],
        participations: Iterable[StudentParticipationProfile],
        task_logs: Iterable[StudentTaskLogProfile],
        work_group_refs: Iterable[WorkGroupRef],
    ) -> StudentProfileData:
        participation_rows = list(participations)
        task_log_rows = list(task_logs)

        stats, scores_timeline = self._build_stats(participation_rows, task_log_rows)
        return StudentProfileData(
            student_groups=list(student_groups),
            participations_data=participation_rows,
            stats=stats,
            group_scores=self._build_group_scores(
                participation_rows,
                list(work_group_refs),
            ),
            scores_timeline=scores_timeline,
            task_log_stats=self._build_task_log_stats(task_log_rows),
            heatmap_groups=self._build_heatmap_cells_by(
                task_log_rows,
                lambda log: log.analog_group.name if log.analog_group else None,
            ),
            heatmap_topics=self._build_heatmap_cells_by(
                task_log_rows,
                lambda log: log.topic_name or None,
            ),
            heatmap_difficulty=self._build_difficulty_cells(task_log_rows),
            recent_task_log=task_log_rows[:50],
        )

    def _build_stats(
        self,
        participations: List[StudentParticipationProfile],
        task_logs: List[StudentTaskLogProfile],
    ) -> tuple[dict, List[ScoreTimelinePoint]]:
        total_marks = 0
        total_score_sum = 0
        absent_count = 0
        score_counts = {2: 0, 3: 0, 4: 0, 5: 0}
        scores_timeline = []

        for participation in participations:
            if participation.is_absent:
                absent_count += 1

            score = participation.score
            if score:
                total_marks += 1
                total_score_sum += score
                if score in score_counts:
                    score_counts[score] += 1

                if participation.event.planned_date:
                    scores_timeline.append(
                        ScoreTimelinePoint(
                            date=participation.event.planned_date.strftime('%d.%m.%Y'),
                            score=score,
                            work=(
                                participation.work.name
                                if participation.work
                                else participation.event.name
                            ),
                        )
                    )

        avg_score = round(total_score_sum / total_marks, 2) if total_marks > 0 else 0
        total_participations = len(participations)
        attendance_rate = (
            round((total_participations - absent_count) / total_participations * 100, 1)
            if total_participations > 0
            else 100
        )
        overall_pct = self._average(
            log.percentage for log in task_logs if log.percentage is not None
        )
        level = self._student_level(overall_pct)

        return {
            'total_works': total_participations,
            'graded_works': total_marks,
            'absent_count': absent_count,
            'avg_score': avg_score,
            'attendance_rate': attendance_rate,
            'score_counts': score_counts,
            'student_level': level.value,
            'student_level_label': level.label_ru,
            'student_level_color': level.color,
            'overall_avg': round(overall_pct, 1),
        }, scores_timeline

    def _student_level(self, overall_pct: float) -> StudentLevel:
        if overall_pct < 50:
            return StudentLevel.WEAK
        if overall_pct < 80:
            return StudentLevel.MEDIUM
        return StudentLevel.STRONG

    def _build_group_scores(
        self,
        participations: List[StudentParticipationProfile],
        work_group_refs: List[WorkGroupRef],
    ) -> List[dict]:
        work_scores: Dict[str, List[int]] = {}
        for participation in participations:
            if participation.score is None or not participation.work:
                continue
            work_scores.setdefault(participation.work.pk, []).append(participation.score)

        group_scores: Dict[str, dict] = {}
        for ref in work_group_refs:
            if ref.work_id not in work_scores:
                continue

            data = group_scores.setdefault(
                ref.group_id,
                {'name': ref.group_name, 'scores': []},
            )
            data['scores'].extend(work_scores[ref.work_id])

        result = []
        for data in group_scores.values():
            scores = data['scores']
            result.append({
                'name': data['name'],
                'avg': round(sum(scores) / len(scores), 2) if scores else None,
                'count': len(scores),
                'min': min(scores) if scores else None,
                'max': max(scores) if scores else None,
            })

        return sorted(result, key=lambda row: row['avg'] or 0)

    def _build_task_log_stats(
        self,
        task_logs: List[StudentTaskLogProfile],
    ) -> Optional[dict]:
        if not task_logs:
            return None

        percentages = [
            log.percentage for log in task_logs if log.percentage is not None
        ]
        return {
            'total': len(task_logs),
            'correct': sum(1 for log in task_logs if log.is_correct is True),
            'wrong': sum(1 for log in task_logs if log.is_correct is False),
            'avg_pct': round(self._average(percentages), 1),
        }

    def _build_heatmap_cells_by(self, task_logs, key_func) -> List[dict]:
        buckets = {}
        for log in task_logs:
            name = key_func(log)
            if not name:
                continue
            buckets.setdefault(name, []).append(log)

        cells = [
            self._build_heatmap_cell(name, logs)
            for name, logs in buckets.items()
        ]
        return sorted(cells, key=lambda row: row['avg_pct'], reverse=True)

    def _build_difficulty_cells(
        self,
        task_logs: List[StudentTaskLogProfile],
    ) -> List[dict]:
        buckets = {}
        for log in task_logs:
            if log.difficulty is None:
                continue
            buckets.setdefault(log.difficulty, []).append(log)

        return [
            self._build_heatmap_cell(f'Сложность {difficulty}', buckets[difficulty])
            for difficulty in sorted(buckets)
        ]

    def _build_heatmap_cell(self, name: str, logs: List[StudentTaskLogProfile]) -> dict:
        percentages = [log.percentage for log in logs if log.percentage is not None]
        avg_pct = round(self._average(percentages), 1)
        return {
            'name': name,
            'total': len(logs),
            'correct': sum(1 for log in logs if log.is_correct is True),
            'avg_pct': avg_pct,
            'level': self._heatmap_level(avg_pct),
        }

    def _heatmap_level(self, percentage: float) -> int:
        if percentage == 0:
            return 0
        if percentage < 30:
            return 1
        if percentage < 55:
            return 2
        if percentage < 80:
            return 3
        return 4

    def _average(self, values) -> float:
        values = list(values)
        return sum(values) / len(values) if values else 0
