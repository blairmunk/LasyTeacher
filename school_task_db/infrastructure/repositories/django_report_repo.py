"""Django implementation of report repository."""

from collections import defaultdict
from datetime import timedelta

from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone

from core_logic.entities.report import (
    EventsStatusReportData,
    HeatmapCourseOverviewData,
    HeatmapCourseTimelineData,
    HeatmapOverviewData,
    HeatmapTopicMatrixData,
    ReportsDashboardData,
    StudentPerformanceReportData,
    WorkAnalysisReportData,
)
from core_logic.interfaces.report_repo import IReportRepository
from curriculum.models import Course, CourseAssignment, Topic
from events.models import Event, EventParticipation, Mark
from students.models import Student, StudentGroup
from tasks.models import Task
from works.models import Variant, Work


class DjangoReportRepository(IReportRepository):
    def get_heatmap_course_overview(self, course_id, group_id):
        course = get_object_or_404(Course, pk=course_id)
        course_groups = course.student_groups.all().order_by('name')

        if group_id:
            selected_group = get_object_or_404(StudentGroup, pk=group_id)
            students = list(
                selected_group.students.all().order_by('last_name', 'first_name'),
            )
        elif course_groups.exists():
            students = list(
                Student.objects.filter(
                    studentgroup__in=course_groups,
                ).distinct().order_by('last_name', 'first_name'),
            )
            selected_group = None
        else:
            students = list(Student.objects.all().order_by('last_name', 'first_name'))
            selected_group = None

        course_works = [
            assignment.work
            for assignment in CourseAssignment.objects.filter(
                course=course,
            ).select_related('work')
        ]

        return HeatmapCourseOverviewData(
            course=course,
            groups=course_groups,
            selected_group=selected_group,
            students=students,
            course_works=course_works,
            courses=Course.objects.filter(is_active=True).order_by(
                'grade_level',
                'name',
            ),
            active_course_pk=course.pk,
        )

    def get_heatmap_overview(self, group_id):
        groups = StudentGroup.objects.all().order_by('name')
        if group_id:
            selected_group = get_object_or_404(StudentGroup, pk=group_id)
            students = list(
                selected_group.students.all().order_by('last_name', 'first_name'),
            )
        else:
            selected_group = None
            students = list(Student.objects.all().order_by('last_name', 'first_name'))

        sections = list(
            Topic.objects.filter(subject='Физика')
            .values_list('section', flat=True)
            .distinct()
            .order_by('section'),
        )

        return HeatmapOverviewData(
            groups=groups,
            selected_group=selected_group,
            students=students,
            sections=sections,
            courses=Course.objects.filter(is_active=True).order_by(
                'grade_level',
                'name',
            ),
        )

    def get_heatmap_topic_matrix(self, student_ids, section_filter=''):
        students = list(
            Student.objects.filter(pk__in=student_ids).order_by(
                'last_name',
                'first_name',
            ),
        )
        marks = Mark.objects.filter(
            participation__student__in=students,
        ).select_related('participation__student')

        all_task_ids = set()
        for mark in marks:
            if mark.task_scores:
                all_task_ids.update(mark.task_scores.keys())

        if not all_task_ids:
            return HeatmapTopicMatrixData(columns=[], rows=[], col_averages=[])

        tasks_qs = Task.objects.filter(pk__in=all_task_ids).select_related(
            'topic',
            'subtopic',
        )
        task_map = {str(task.pk): task for task in tasks_qs}
        aggregated = defaultdict(lambda: {'points': 0, 'max_points': 0})

        for mark in marks:
            student_id = mark.participation.student_id
            if not mark.task_scores:
                continue
            seen = set()
            for task_id, scores in mark.task_scores.items():
                if task_id in seen:
                    continue
                seen.add(task_id)

                task = task_map.get(task_id)
                if not task or not task.topic:
                    continue
                if section_filter and task.topic.section != section_filter:
                    continue

                key = (student_id, task.topic_id)
                aggregated[key]['points'] += scores.get('points', 0)
                aggregated[key]['max_points'] += scores.get('max_points', 0)

        topic_ids = {topic_id for _, topic_id in aggregated.keys()}
        columns = list(
            Topic.objects.filter(pk__in=topic_ids).order_by(
                'section',
                'order',
                'name',
            ),
        )
        rows = self._build_heatmap_rows(students, columns, aggregated)
        col_averages = self._build_heatmap_col_averages(
            students,
            columns,
            aggregated,
        )

        return HeatmapTopicMatrixData(
            columns=columns,
            rows=rows,
            col_averages=col_averages,
        )

    def get_heatmap_course_topic_matrix(self, student_ids, work_ids):
        students = list(
            Student.objects.filter(pk__in=student_ids).order_by(
                'last_name',
                'first_name',
            ),
        )
        course_task_ids = self._get_variant_task_ids(work_ids)
        marks = Mark.objects.filter(
            participation__student__in=students,
            participation__event__work_id__in=work_ids,
        ).select_related('participation__student')

        all_task_ids = set()
        for mark in marks:
            if mark.task_scores:
                all_task_ids.update(mark.task_scores.keys())

        relevant_task_ids = (
            all_task_ids & course_task_ids
            if course_task_ids
            else all_task_ids
        )
        if not relevant_task_ids:
            return HeatmapTopicMatrixData(columns=[], rows=[], col_averages=[])

        tasks_qs = Task.objects.filter(pk__in=relevant_task_ids).select_related(
            'topic',
            'subtopic',
        )
        task_map = {str(task.pk): task for task in tasks_qs}
        aggregated = defaultdict(lambda: {'points': 0, 'max_points': 0})

        for mark in marks:
            student_id = mark.participation.student_id
            if not mark.task_scores:
                continue
            seen = set()
            for task_id, scores in mark.task_scores.items():
                if task_id in seen:
                    continue
                seen.add(task_id)

                task = task_map.get(task_id)
                if not task or not task.topic:
                    continue

                key = (student_id, task.topic_id)
                aggregated[key]['points'] += scores.get('points', 0)
                aggregated[key]['max_points'] += scores.get('max_points', 0)

        topic_ids = {topic_id for _, topic_id in aggregated.keys()}
        columns = list(
            Topic.objects.filter(pk__in=topic_ids).order_by(
                'section',
                'order',
                'name',
            ),
        )
        rows = self._build_heatmap_rows(students, columns, aggregated)
        col_averages = self._build_heatmap_col_averages(
            students,
            columns,
            aggregated,
        )

        return HeatmapTopicMatrixData(
            columns=columns,
            rows=rows,
            col_averages=col_averages,
        )

    def get_heatmap_course_timeline(self, student_ids, work_ids):
        events = Event.objects.filter(
            work_id__in=work_ids,
            status='graded',
        ).order_by('planned_date')

        dates = []
        averages = []
        labels = []

        for event in events:
            marks = Mark.objects.filter(
                participation__event=event,
                participation__student_id__in=student_ids,
            )
            if not marks.exists():
                continue

            total_points = 0
            total_max = 0
            for mark in marks:
                if not mark.task_scores:
                    continue
                seen = set()
                for task_id, scores in mark.task_scores.items():
                    if task_id in seen:
                        continue
                    seen.add(task_id)
                    total_points += scores.get('points', 0)
                    total_max += scores.get('max_points', 0)

            if total_max > 0:
                dates.append(event.planned_date.strftime('%Y-%m-%d'))
                averages.append(round(total_points / total_max * 100))
                labels.append(event.name)

        return HeatmapCourseTimelineData(
            dates=dates,
            averages=averages,
            labels=labels,
        )

    def get_reports_dashboard(self, year, current_date):
        current_date = current_date or timezone.now()
        events, participations, courses = self._get_event_scope(year)
        marks = self._get_marks_scope(year)
        groups, students = self._get_student_scope(year)

        average_score = marks.aggregate(avg_score=Avg('score'))['avg_score'] or 0
        score_counts = {
            item['score']: item['count']
            for item in marks.exclude(score__isnull=True).values('score').annotate(
                count=Count('score'),
            )
        }
        monthly_labels, monthly_values = self._get_monthly_activity(
            participations,
            current_date,
        )
        (
            class_stats,
            class_names,
            class_avg_scores,
            class_completion,
        ) = self._get_class_stats(groups, participations, marks, year)

        return ReportsDashboardData(
            total_students=students.count(),
            total_events=events.count(),
            total_works=Work.objects.count(),
            total_courses=courses.count(),
            total_marks=marks.count(),
            average_score=average_score,
            marks_last_month=marks.filter(
                checked_at__gte=current_date - timedelta(days=30),
            ).count(),
            score_counts=score_counts,
            events_planned=events.filter(status='planned').count(),
            events_completed=events.filter(status='completed').count(),
            events_graded=events.filter(status='graded').count(),
            monthly_labels=monthly_labels,
            monthly_values=monthly_values,
            class_stats=class_stats,
            class_names=class_names,
            class_avg_scores=class_avg_scores,
            class_completion=class_completion,
            recent_events=events.select_related(
                'work',
                'course',
            ).order_by('-planned_date')[:10],
            event_status_counts=self._get_event_status_counts(events),
            box_data=self._get_box_data(events, marks),
            courses=courses.order_by('grade_level', 'name'),
        )

    def get_events_status_report(self, year, current_date):
        events, participations, courses = self._get_event_scope(year)

        events_by_status = list(
            events.values('status').annotate(
                count=Count('id'),
            ).order_by('status'),
        )
        participation_stats = list(
            participations.values('status').annotate(
                count=Count('id'),
            ).order_by('status'),
        )

        return EventsStatusReportData(
            events_by_status=events_by_status,
            overdue_events=events.filter(
                status='planned',
                planned_date__lt=current_date - timedelta(days=1),
            ).select_related('work'),
            long_reviewing=events.filter(
                status='reviewing',
                actual_end__lt=current_date - timedelta(days=7),
            ).select_related('work'),
            completed_unchecked=events.filter(
                status='completed',
                actual_end__lt=current_date - timedelta(days=3),
            ).select_related('work'),
            participation_stats=participation_stats,
            all_events=events.select_related('work').order_by('-planned_date'),
            courses=courses.order_by('grade_level', 'name'),
        )

    def get_work_analysis_report(self, year):
        events, _, courses = self._get_event_scope(year)
        marks = self._get_marks_scope(year)

        works_analysis = []
        for work in Work.objects.all():
            work_events = events.filter(work=work)
            work_marks = marks.filter(
                participation__event__work=work,
                score__isnull=False,
            )

            if work_events.count() == 0:
                continue

            avg_score = work_marks.aggregate(avg=Avg('score'))['avg'] or 0
            avg_pct = self._average_task_score_percentage(work_marks)
            score_distribution = list(
                work_marks.values('score').annotate(
                    count=Count('id'),
                ).order_by('score'),
            )

            works_analysis.append({
                'work': work,
                'events_count': work_events.count(),
                'total_marks': work_marks.count(),
                'average_score': round(avg_score, 2),
                'average_percentage': avg_pct,
                'score_distribution': score_distribution,
                'difficulty_assessment': self._assess_difficulty(avg_pct),
            })

        return WorkAnalysisReportData(
            works_analysis=works_analysis,
            summary_stats={
                'total_works': len(works_analysis),
                'total_marks': sum(w['total_marks'] for w in works_analysis),
                'easy_works': sum(
                    1 for w in works_analysis
                    if w['difficulty_assessment'] == 'Легкая'
                ),
                'hard_works': sum(
                    1 for w in works_analysis
                    if w['difficulty_assessment'] in ('Сложная', 'Очень сложная')
                ),
                'avg_score': round(
                    sum(w['average_score'] for w in works_analysis)
                    / len(works_analysis),
                    2,
                ) if works_analysis else 0,
            },
            courses=courses.order_by('grade_level', 'name'),
        )

    def get_student_performance_report(self, year, group_id):
        _, participations, courses = self._get_event_scope(year)
        marks = self._get_marks_scope(year)
        groups, students = self._get_student_scope(year)
        groups = groups.order_by('name')

        selected_group = None
        if group_id:
            selected_group = groups.filter(pk=group_id).first()
            if selected_group:
                students = selected_group.students.all()

        students_stats = []
        for student in students.order_by('last_name', 'first_name'):
            student_participations = participations.filter(student=student)
            total_participations = student_participations.count()
            if total_participations == 0:
                continue

            completed_count = student_participations.filter(
                status__in=['completed', 'graded'],
            ).count()
            student_marks = marks.filter(participation__student=student)
            avg_score = student_marks.aggregate(avg=Avg('score'))['avg'] or 0
            avg_pct = self._average_task_score_percentage(
                student_marks,
                default=None,
            )
            completion_rate = round(
                completed_count / total_participations * 100,
                1,
            )

            students_stats.append({
                'student': student,
                'total_participations': total_participations,
                'completed_participations': completed_count,
                'completion_rate': completion_rate,
                'total_marks': student_marks.count(),
                'average_score': round(avg_score, 2) if avg_score else 0,
                'average_pct': avg_pct,
                'last_activity': student_participations.order_by(
                    '-created_at',
                ).first(),
            })

        return StudentPerformanceReportData(
            students_stats=students_stats,
            groups=groups,
            selected_group=selected_group,
            summary_stats={
                'total_students': len(students_stats),
                'high_performers': sum(
                    1 for stat in students_stats
                    if (stat['average_pct'] or 0) >= 85
                ),
                'need_attention': sum(
                    1 for stat in students_stats
                    if stat['average_pct'] is not None
                    and stat['average_pct'] < 45
                ),
                'avg_completion_rate': round(
                    sum(stat['completion_rate'] for stat in students_stats)
                    / len(students_stats),
                    1,
                ) if students_stats else 0,
                'avg_pct': round(
                    sum(
                        stat['average_pct'] for stat in students_stats
                        if stat['average_pct'] is not None
                    ) / max(
                        sum(
                            1 for stat in students_stats
                            if stat['average_pct'] is not None
                        ),
                        1,
                    ),
                ),
            },
            courses=courses.order_by('grade_level', 'name'),
        )

    def _get_event_scope(self, year):
        if year:
            date_range = (year.start_date, year.end_date)
            events = Event.objects.filter(planned_date__range=date_range)
            participations = EventParticipation.objects.filter(
                event__planned_date__range=date_range,
            )
            courses = Course.objects.filter(year=year, is_active=True)
        else:
            events = Event.objects.all()
            participations = EventParticipation.objects.all()
            courses = Course.objects.filter(is_active=True)

        return events, participations, courses

    def _get_student_scope(self, year):
        if year:
            return (
                StudentGroup.objects.filter(academic_year=year),
                Student.objects.filter(
                    studentgroup__academic_year=year,
                ).distinct(),
            )
        return StudentGroup.objects.all(), Student.objects.all()

    def _get_marks_scope(self, year):
        if year:
            date_range = (year.start_date, year.end_date)
            return Mark.objects.filter(
                participation__event__planned_date__range=date_range,
            )
        return Mark.objects.all()

    def _get_monthly_activity(self, participations, current_date):
        monthly_labels = []
        monthly_values = []
        for i in range(6):
            month_start = current_date.replace(day=1) - timedelta(days=30 * i)
            month_end = month_start + timedelta(days=31)
            count = participations.filter(
                event__planned_date__range=[month_start, month_end],
                status__in=['completed', 'graded'],
            ).count()
            monthly_labels.append(month_start.strftime('%b %Y'))
            monthly_values.append(count)

        monthly_labels.reverse()
        monthly_values.reverse()
        return monthly_labels, monthly_values

    def _get_class_stats(self, groups, participations, marks, year):
        class_stats = []
        class_names = []
        class_avg_scores = []
        class_completion = []

        for student_group in groups:
            student_ids = list(student_group.students.values_list('id', flat=True))
            group_participations = participations.filter(
                student__id__in=student_ids,
            )
            completed = group_participations.filter(
                status__in=['completed', 'graded'],
            )
            class_marks = marks.filter(
                participation__student__id__in=student_ids,
                score__isnull=False,
            )
            avg_score = class_marks.aggregate(avg=Avg('score'))['avg'] or 0
            total_participations = group_participations.count()
            completed_count = completed.count()
            completion_rate = round(
                completed_count / total_participations * 100
                if total_participations > 0 else 0,
                1,
            )
            heatmap_links = self._get_heatmap_links(student_group, year)

            class_stats.append({
                'name': student_group.name,
                'students_count': student_group.students.count(),
                'total_participations': total_participations,
                'completed_participations': completed_count,
                'average_score': round(avg_score, 2) if avg_score else 0,
                'completion_rate': completion_rate,
                'id': str(student_group.id),
                'heatmap_links': heatmap_links,
            })
            class_names.append(student_group.name)
            class_avg_scores.append(round(avg_score, 2))
            class_completion.append(completion_rate)

        return class_stats, class_names, class_avg_scores, class_completion

    def _get_heatmap_links(self, student_group, year):
        heatmap_links = []
        linked_courses = student_group.courses.all()
        if year:
            linked_courses = linked_courses.filter(year=year)
        for course in linked_courses:
            heatmap_links.append({
                'course_id': str(course.pk),
                'course_name': course.name,
                'group_id': str(student_group.pk),
                'group_name': student_group.name,
            })
        return heatmap_links

    def _get_event_status_counts(self, events):
        return {
            item['status']: item['count']
            for item in events.values('status').annotate(
                count=Count('id'),
            )
        }

    def _get_box_data(self, events, marks):
        box_data = {}
        for event in events.select_related('work'):
            work_name = event.work.name if event.work else 'Без работы'
            short_name = work_name[:20]
            scores = list(
                marks.filter(
                    participation__event=event,
                    score__isnull=False,
                ).values_list('score', flat=True),
            )
            if scores:
                box_data[short_name] = scores
        return box_data

    def _get_variant_task_ids(self, work_ids):
        task_ids = set()
        variants = Variant.objects.filter(
            work_id__in=work_ids,
        ).prefetch_related('tasks')
        for variant in variants:
            for task in variant.tasks.all():
                task_ids.add(str(task.pk))
        return task_ids

    def _build_heatmap_rows(self, students, columns, aggregated):
        rows = []
        for student in students:
            cells = []
            total_points = 0
            total_max = 0
            for topic in columns:
                data = aggregated.get((student.id, topic.id))
                if data and data['max_points'] > 0:
                    pct = round(data['points'] / data['max_points'] * 100)
                    total_points += data['points']
                    total_max += data['max_points']
                    cells.append({
                        'pct': pct,
                        'points': data['points'],
                        'max_points': data['max_points'],
                        'css': self._color_class(pct),
                        'topic': topic,
                    })
                else:
                    cells.append({
                        'pct': None,
                        'css': 'no-data',
                        'topic': topic,
                    })

            avg = round(total_points / total_max * 100) if total_max > 0 else None
            rows.append({
                'student': student,
                'cells': cells,
                'avg': avg,
                'avg_css': self._color_class(avg) if avg is not None else 'no-data',
            })
        return rows

    def _build_heatmap_col_averages(self, students, columns, aggregated):
        col_averages = []
        for topic in columns:
            points = sum(
                aggregated.get((student.id, topic.id), {}).get('points', 0)
                for student in students
            )
            max_points = sum(
                aggregated.get((student.id, topic.id), {}).get('max_points', 0)
                for student in students
            )
            avg = round(points / max_points * 100) if max_points > 0 else None
            col_averages.append({
                'pct': avg,
                'css': self._color_class(avg) if avg is not None else 'no-data',
            })
        return col_averages

    def _color_class(self, pct):
        if pct is None:
            return 'no-data'
        if pct >= 95:
            return 'perfect'
        if pct >= 85:
            return 'excellent'
        if pct >= 70:
            return 'good'
        if pct >= 60:
            return 'moderate'
        if pct >= 45:
            return 'warning'
        return 'danger'

    def _average_task_score_percentage(self, marks, default=0):
        total_points = 0
        total_max = 0
        for mark in marks:
            if not mark.task_scores:
                continue
            for scores in mark.task_scores.values():
                total_points += scores.get('points', 0)
                total_max += scores.get('max_points', 0)
        return round(total_points / total_max * 100) if total_max > 0 else default

    def _assess_difficulty(self, avg_pct):
        if avg_pct >= 85:
            return 'Легкая'
        if avg_pct >= 70:
            return 'Средняя'
        if avg_pct >= 50:
            return 'Сложная'
        return 'Очень сложная'
