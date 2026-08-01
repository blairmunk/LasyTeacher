"""Pure calculations for summary reports."""

from collections import Counter
from datetime import timedelta

from core_logic.entities.report import (
    EventsStatusReportData,
    EventsStatusSource,
    JournalData,
    JournalSource,
    ReportsDashboardData,
    ReportsDashboardSource,
    StudentPerformanceReportData,
    StudentPerformanceSource,
    TaskDBHealthData,
    TaskDBHealthSource,
    WorkAnalysisReportData,
    WorkAnalysisSource,
)


class ReportSummaryService:
    def build_task_db_health(
        self,
        source: TaskDBHealthSource,
    ) -> TaskDBHealthData:
        empty_groups = [
            item.group for item in source.group_sizes if item.task_count == 0
        ]
        fragile_groups = [
            item.group for item in source.group_sizes if item.task_count == 1
        ]
        coverage_issues = [
            {
                'work': item.work,
                'group': item.group,
                'needed': item.needed,
                'available': item.available,
                'deficit': item.needed - item.available,
            }
            for item in source.coverage
            if item.available < item.needed
        ]
        health_counts = {
            'orphan_variants': source.orphan_variants_count,
            'empty_groups': len(empty_groups),
            'coverage_issues': len(coverage_issues),
            'ungrouped_tasks': source.ungrouped_tasks_count,
            'fragile_groups': len(fragile_groups),
            'works_no_variants': source.works_no_variants_count,
            'works_no_spec': source.works_no_spec_count,
        }
        return TaskDBHealthData(
            stats={
                'total_tasks': source.total_tasks,
                'total_groups': len(source.group_sizes),
                'total_works': source.total_works,
                'total_variants': source.total_variants,
            },
            orphan_variants={
                'count': source.orphan_variants_count,
                'items': source.orphan_variant_samples,
            },
            empty_groups={
                'count': len(empty_groups),
                'items': empty_groups[:20],
            },
            coverage_issues={
                'count': len(coverage_issues),
                'items': coverage_issues[:20],
            },
            difficulty_dist=[
                {
                    'difficulty': item.key or 0,
                    'count': item.count,
                    'pct': self._pct(item.count, source.total_tasks),
                }
                for item in source.difficulty_counts
            ],
            ungrouped_tasks={
                'count': source.ungrouped_tasks_count,
                'pct': self._pct(
                    source.ungrouped_tasks_count,
                    source.total_tasks,
                ),
            },
            fragile_groups={
                'count': len(fragile_groups),
                'items': fragile_groups[:20],
            },
            works_no_variants={
                'count': source.works_no_variants_count,
                'items': source.works_no_variant_samples,
            },
            works_no_spec={
                'count': source.works_no_spec_count,
                'items': source.works_no_spec_samples,
            },
            type_dist=[
                {
                    'task_type': item.key,
                    'count': item.count,
                    'label': item.label or item.key or '—',
                    'pct': self._pct(item.count, source.total_tasks),
                }
                for item in source.type_counts
            ],
            most_used_tasks=source.most_used_tasks,
            group_sizes=self._task_group_size_distribution(source.group_sizes),
            unverified_tasks={
                'count': source.unverified_tasks_count,
                'pct': self._pct(
                    source.unverified_tasks_count,
                    source.total_tasks,
                ),
            },
            no_source_tasks={
                'count': source.no_source_tasks_count,
                'pct': self._pct(
                    source.no_source_tasks_count,
                    source.total_tasks,
                ),
            },
            no_grade_tasks={
                'count': source.no_grade_tasks_count,
                'pct': self._pct(
                    source.no_grade_tasks_count,
                    source.total_tasks,
                ),
            },
            health=self._task_db_health_summary(health_counts),
            courses=source.courses,
        )

    @staticmethod
    def _task_group_size_distribution(group_sizes):
        counts = Counter(item.task_count for item in group_sizes)
        return [
            {'task_count': task_count, 'group_count': counts[task_count]}
            for task_count in sorted(counts)
        ]

    def _task_db_health_summary(self, counts):
        issues = sum(counts.values())
        if issues == 0:
            health = {
                'label': 'Отлично',
                'color': 'success',
                'icon': 'check-circle',
            }
        elif issues <= 5:
            health = {
                'label': 'Хорошо',
                'color': 'info',
                'icon': 'info-circle',
            }
        elif issues <= 15:
            health = {
                'label': 'Есть замечания',
                'color': 'warning',
                'icon': 'exclamation-triangle',
            }
        else:
            health = {
                'label': 'Требует внимания',
                'color': 'danger',
                'icon': 'exclamation-circle',
            }
        health['issues'] = issues
        health['issues_text'] = self._issues_text(issues)
        return health

    @staticmethod
    def _issues_text(issues):
        if 11 <= issues % 100 <= 19:
            return f'{issues} замечаний'
        if issues % 10 == 1:
            return f'{issues} замечание'
        if 2 <= issues % 10 <= 4:
            return f'{issues} замечания'
        return f'{issues} замечаний'

    @staticmethod
    def _pct(value, total):
        return round(value / total * 100, 1) if total else 0

    def build_journal(
        self,
        source: JournalSource,
        show_debts_only: bool = False,
    ) -> JournalData:
        entries = {
            (entry.student_id, entry.event_id): entry
            for entry in source.entries
        }
        all_rows = []
        for student in source.students:
            cells = [
                self._journal_cell(
                    event,
                    entries.get((student.pk, event.pk)),
                )
                for event in source.events
            ]
            scores = [
                cell['score']
                for cell in cells
                if cell['status'] == 'graded'
            ]
            all_rows.append({
                'student': student,
                'cells': cells,
                'avg_score': (
                    round(sum(scores) / len(scores), 1)
                    if scores
                    else None
                ),
                'score_count': len(scores),
                'debts': sum(
                    1
                    for cell in cells
                    if cell['status'] in ('absent', 'missing')
                ),
            })

        rows = (
            [row for row in all_rows if row['debts'] > 0]
            if show_debts_only
            else all_rows
        )
        return JournalData(
            course=source.course,
            group=source.group,
            events=source.events,
            event_stats=self._journal_event_stats(source.events, all_rows),
            rows=rows,
            all_rows_count=len(all_rows),
            show_debts_only=show_debts_only,
            total_debts=sum(row['debts'] for row in all_rows),
            students_with_debts=sum(
                1 for row in all_rows if row['debts'] > 0
            ),
            courses=source.courses,
        )

    def _journal_cell(self, event, entry):
        participation = entry.participation if entry else None
        mark = entry.mark if entry else None
        cell = {
            'event': event,
            'participation': participation,
            'mark': mark,
            'score': None,
            'status': 'missing',
            'css_class': 'journal-missing',
            'display': '',
            'variant': entry.variant if entry else None,
        }
        if participation is None:
            return cell
        if participation.status == 'absent':
            cell.update(
                status='absent',
                display='Н',
                css_class='journal-absent',
            )
        elif mark is not None and mark.score is not None:
            cell.update(
                status='graded',
                score=mark.score,
                display=str(mark.score),
                css_class=self._journal_score_css(mark.score),
            )
        elif participation.status in ('assigned', 'started'):
            cell.update(
                status='in_progress',
                display='…',
                css_class='journal-progress',
            )
        elif participation.status == 'completed':
            cell.update(
                status='completed',
                display='✓',
                css_class='journal-completed',
            )
        else:
            cell.update(status='assigned', display='–', css_class='')
        return cell

    @staticmethod
    def _journal_score_css(score):
        if score >= 5:
            return 'journal-5'
        if score == 4:
            return 'journal-4'
        if score == 3:
            return 'journal-3'
        return 'journal-2'

    @staticmethod
    def _journal_event_stats(events, rows):
        stats = []
        for event in events:
            cells = [
                cell
                for row in rows
                for cell in row['cells']
                if cell['event'].pk == event.pk
            ]
            stats.append({
                'event': event,
                'graded': sum(
                    1 for cell in cells if cell['status'] == 'graded'
                ),
                'absent': sum(
                    1 for cell in cells if cell['status'] == 'absent'
                ),
                'missing': sum(
                    1 for cell in cells if cell['status'] == 'missing'
                ),
                'total': len(cells),
            })
        return stats

    def build_reports_dashboard(
        self,
        source: ReportsDashboardSource,
        current_date,
    ) -> ReportsDashboardData:
        scores = [mark.score for mark in source.marks if mark.score is not None]
        score_counts = Counter(scores)
        event_by_id = {event.pk: event for event in source.events}
        monthly_labels, monthly_values = self._monthly_activity(
            source.participations,
            event_by_id,
            current_date,
        )
        class_stats = [
            self._dashboard_group_stat(group, source)
            for group in source.groups
        ]
        event_status_counts = Counter(event.status for event in source.events)
        marks_by_event = {}
        for event in source.events:
            event_scores = [
                mark.score
                for mark in source.marks
                if mark.event_id == event.pk and mark.score is not None
            ]
            if event_scores:
                work_name = event.work.name if event.work else 'Без работы'
                marks_by_event[work_name[:20]] = event_scores

        return ReportsDashboardData(
            total_students=source.total_students,
            total_events=len(source.events),
            total_works=source.total_works,
            total_courses=len(source.courses),
            total_marks=len(source.marks),
            average_score=(sum(scores) / len(scores) if scores else 0),
            marks_last_month=sum(
                1
                for mark in source.marks
                if mark.checked_at is not None
                and mark.checked_at >= current_date - timedelta(days=30)
            ),
            score_counts=dict(score_counts),
            events_planned=event_status_counts['planned'],
            events_completed=event_status_counts['completed'],
            events_graded=event_status_counts['graded'],
            monthly_labels=monthly_labels,
            monthly_values=monthly_values,
            class_stats=class_stats,
            class_names=[stat['name'] for stat in class_stats],
            class_avg_scores=[stat['average_score'] for stat in class_stats],
            class_completion=[stat['completion_rate'] for stat in class_stats],
            recent_events=source.events[:10],
            event_status_counts=dict(event_status_counts),
            box_data=marks_by_event,
            courses=source.courses,
        )

    @staticmethod
    def _monthly_activity(participations, event_by_id, current_date):
        labels = []
        values = []
        for index in range(6):
            month_start = current_date.replace(day=1) - timedelta(
                days=30 * index,
            )
            month_end = month_start + timedelta(days=31)
            values.append(sum(
                1
                for participation in participations
                if participation.status in ('completed', 'graded')
                and participation.event_id in event_by_id
                and month_start
                <= event_by_id[participation.event_id].planned_date
                <= month_end
            ))
            labels.append(month_start.strftime('%b %Y'))
        labels.reverse()
        values.reverse()
        return labels, values

    @staticmethod
    def _dashboard_group_stat(group_source, source):
        student_ids = set(group_source.student_ids)
        participations = [
            participation
            for participation in source.participations
            if participation.student_id in student_ids
        ]
        marks = [
            mark
            for mark in source.marks
            if mark.student_id in student_ids and mark.score is not None
        ]
        completed_count = sum(
            1
            for participation in participations
            if participation.status in ('completed', 'graded')
        )
        average_score = (
            round(sum(mark.score for mark in marks) / len(marks), 2)
            if marks
            else 0
        )
        total_participations = len(participations)
        return {
            'name': group_source.group.name,
            'students_count': group_source.group.students_count,
            'total_participations': total_participations,
            'completed_participations': completed_count,
            'average_score': average_score,
            'completion_rate': round(
                completed_count / total_participations * 100
                if total_participations > 0
                else 0,
                1,
            ),
            'id': group_source.group.pk,
            'heatmap_links': [
                {
                    'course_id': link.course_id,
                    'course_name': link.course_name,
                    'group_id': link.group_id,
                    'group_name': link.group_name,
                }
                for link in group_source.course_links
            ],
        }

    def build_events_status(
        self,
        source: EventsStatusSource,
        current_date,
    ) -> EventsStatusReportData:
        event_counts = Counter(event.status for event in source.events)
        participation_counts = Counter(source.participation_statuses)
        return EventsStatusReportData(
            events_by_status=[
                {'status': status, 'count': event_counts[status]}
                for status in sorted(event_counts)
            ],
            overdue_events=[
                event
                for event in source.events
                if event.status == 'planned'
                and event.planned_date < current_date - timedelta(days=1)
            ],
            long_reviewing=[
                event
                for event in source.events
                if event.status == 'reviewing'
                and event.actual_end is not None
                and event.actual_end < current_date - timedelta(days=7)
            ],
            completed_unchecked=[
                event
                for event in source.events
                if event.status == 'completed'
                and event.actual_end is not None
                and event.actual_end < current_date - timedelta(days=3)
            ],
            participation_stats=[
                {'status': status, 'count': participation_counts[status]}
                for status in sorted(participation_counts)
            ],
            all_events=source.events,
            courses=source.courses,
        )

    def build_student_performance(
        self,
        source: StudentPerformanceSource,
    ) -> StudentPerformanceReportData:
        students_stats = []
        for item in source.students:
            total_participations = len(item.participations)
            if total_participations == 0:
                continue
            completed_count = sum(
                1
                for participation in item.participations
                if participation.status in ('completed', 'graded')
            )
            scores = [
                mark.score
                for mark in item.marks
                if mark.score is not None
            ]
            total_points = sum(mark.points or 0 for mark in item.marks)
            total_max = sum(mark.max_points or 0 for mark in item.marks)
            students_stats.append({
                'student': item.student,
                'total_participations': total_participations,
                'completed_participations': completed_count,
                'completion_rate': round(
                    completed_count / total_participations * 100,
                    1,
                ),
                'total_marks': len(item.marks),
                'average_score': (
                    round(sum(scores) / len(scores), 2)
                    if scores
                    else 0
                ),
                'average_pct': (
                    round(total_points / total_max * 100)
                    if total_max > 0
                    else None
                ),
                'last_activity': max(
                    item.participations,
                    key=lambda participation: participation.created_at,
                ),
            })

        percentages = [
            stat['average_pct']
            for stat in students_stats
            if stat['average_pct'] is not None
        ]
        return StudentPerformanceReportData(
            students_stats=students_stats,
            groups=source.groups,
            selected_group=source.selected_group,
            summary_stats={
                'total_students': len(students_stats),
                'high_performers': sum(
                    1
                    for stat in students_stats
                    if (stat['average_pct'] or 0) >= 85
                ),
                'need_attention': sum(
                    1
                    for stat in students_stats
                    if stat['average_pct'] is not None
                    and stat['average_pct'] < 45
                ),
                'avg_completion_rate': (
                    round(
                        sum(
                            stat['completion_rate']
                            for stat in students_stats
                        ) / len(students_stats),
                        1,
                    )
                    if students_stats
                    else 0
                ),
                'avg_pct': (
                    round(sum(percentages) / len(percentages))
                    if percentages
                    else 0
                ),
            },
            courses=source.courses,
        )

    def build_work_analysis(
        self,
        source: WorkAnalysisSource,
    ) -> WorkAnalysisReportData:
        works_analysis = []
        for item in source.works:
            scores = [
                mark.score
                for mark in item.marks
                if mark.score is not None
            ]
            average_score = (
                round(sum(scores) / len(scores), 2)
                if scores
                else 0
            )
            total_points = sum(mark.points or 0 for mark in item.marks)
            total_max = sum(mark.max_points or 0 for mark in item.marks)
            average_percentage = (
                round(total_points / total_max * 100)
                if total_max > 0
                else 0
            )
            score_counts = Counter(scores)
            score_distribution = [
                {'score': score, 'count': score_counts[score]}
                for score in sorted(score_counts)
            ]

            works_analysis.append({
                'work': item.work,
                'events_count': item.events_count,
                'total_marks': len(item.marks),
                'average_score': average_score,
                'average_percentage': average_percentage,
                'score_distribution': score_distribution,
                'difficulty_assessment': self.assess_difficulty(
                    average_percentage,
                ),
            })

        return WorkAnalysisReportData(
            works_analysis=works_analysis,
            summary_stats={
                'total_works': len(works_analysis),
                'total_marks': sum(
                    work['total_marks']
                    for work in works_analysis
                ),
                'easy_works': sum(
                    1
                    for work in works_analysis
                    if work['difficulty_assessment'] == 'Легкая'
                ),
                'hard_works': sum(
                    1
                    for work in works_analysis
                    if work['difficulty_assessment'] in (
                        'Сложная',
                        'Очень сложная',
                    )
                ),
                'avg_score': (
                    round(
                        sum(
                            work['average_score']
                            for work in works_analysis
                        ) / len(works_analysis),
                        2,
                    )
                    if works_analysis
                    else 0
                ),
            },
            courses=source.courses,
        )

    @staticmethod
    def assess_difficulty(average_percentage):
        if average_percentage >= 85:
            return 'Легкая'
        if average_percentage >= 70:
            return 'Средняя'
        if average_percentage >= 50:
            return 'Сложная'
        return 'Очень сложная'
