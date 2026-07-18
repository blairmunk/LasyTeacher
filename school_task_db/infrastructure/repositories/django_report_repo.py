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
    HeatmapDrilldownOverviewData,
    HeatmapOverviewData,
    HeatmapStudentDetailData,
    HeatmapSubtopicDetailData,
    HeatmapSubtopicMatrixData,
    HeatmapTopicMatrixData,
    JournalData,
    JournalSelectData,
    ReportsDashboardData,
    ReportCourseRef,
    ReportGroupRef,
    ReportStudentRef,
    StudentPerformanceReportData,
    TaskDBHealthData,
    WorkAnalysisReportData,
)
from core_logic.interfaces.report_repo import IReportRepository
from curriculum.models import Course, CourseAssignment, SubTopic, Topic
from events.models import Event, EventParticipation, Mark
from students.models import Student, StudentGroup
from tasks.models import Task
from task_groups.models import AnalogGroup, TaskGroup
from works.models import Variant, Work, WorkAnalogGroup


class DjangoReportRepository(IReportRepository):
    def get_journal_select(self, year):
        _, _, courses = self._get_event_scope(year)
        groups, _ = self._get_student_scope(year)
        courses = courses.order_by('grade_level', 'name')
        groups = groups.order_by('name')
        available_groups = list(groups)

        journal_links = []
        for course in courses:
            for group in course.student_groups.all():
                if group in available_groups:
                    event_count = Event.objects.filter(
                        course=course,
                        eventparticipation__student__in=group.students.all(),
                    ).distinct().count()
                    journal_links.append({
                        'course': ReportCourseRef(
                            pk=str(course.pk),
                            name=course.name,
                        ),
                        'group': ReportGroupRef(
                            pk=str(group.pk),
                            name=group.name,
                            students_count=group.students.count(),
                        ),
                        'event_count': event_count,
                    })

        return JournalSelectData(
            journal_links=journal_links,
            groups=groups,
            courses=courses,
        )

    def get_journal(self, course_id, group_id, year, show_debts_only):
        course = get_object_or_404(Course, pk=course_id)
        group = get_object_or_404(StudentGroup, pk=group_id)
        students = group.students.all().order_by('last_name', 'first_name')
        student_ids = list(students.values_list('id', flat=True))

        events = Event.objects.filter(
            course=course,
            eventparticipation__student__in=student_ids,
        ).distinct().select_related('work').order_by('planned_date')
        participations = EventParticipation.objects.filter(
            event__in=events,
            student_id__in=student_ids,
        ).select_related('student', 'event', 'variant')
        marks = Mark.objects.filter(
            participation__in=participations,
        ).select_related('participation')

        part_lookup = {
            (participation.student_id, participation.event_id): participation
            for participation in participations
        }
        mark_lookup = {
            mark.participation_id: mark
            for mark in marks
        }
        all_rows = self._build_journal_rows(students, events, part_lookup, mark_lookup)
        rows = (
            [row for row in all_rows if row['debts'] > 0]
            if show_debts_only
            else all_rows
        )

        return JournalData(
            course=course,
            group=group,
            events=events,
            event_stats=self._build_journal_event_stats(events, all_rows),
            rows=rows,
            all_rows_count=len(all_rows),
            show_debts_only=show_debts_only,
            total_debts=sum(row['debts'] for row in all_rows),
            students_with_debts=sum(1 for row in all_rows if row['debts'] > 0),
            courses=self._get_event_scope(year)[2].order_by('grade_level', 'name'),
        )

    def get_task_db_health(self):
        total_tasks = Task.objects.count()
        total_groups_qs = AnalogGroup.objects.annotate(task_count=Count('taskgroup'))
        total_works = Work.objects.count()
        total_variants = Variant.objects.count()
        orphan_variants = Variant.objects.filter(work__isnull=True)
        empty_groups = total_groups_qs.filter(task_count=0)
        coverage_issues = self._build_coverage_issues()
        tasks_in_groups = set(TaskGroup.objects.values_list('task_id', flat=True))
        ungrouped_count = Task.objects.exclude(id__in=tasks_in_groups).count()
        fragile_groups = total_groups_qs.filter(task_count=1)
        works_no_variants = Work.objects.annotate(
            variant_count=Count('variant'),
        ).filter(variant_count=0)
        works_no_spec = Work.objects.annotate(
            spec_count=Count('workanaloggroup'),
        ).filter(spec_count=0)
        unverified_count = Task.objects.filter(is_verified=False).count()
        no_source_count = Task.objects.filter(source__isnull=True).count()
        no_grade_count = Task.objects.filter(grade__isnull=True).count()

        health_source = {
            'orphan_variants': orphan_variants.count(),
            'empty_groups': empty_groups.count(),
            'coverage_issues': len(coverage_issues),
            'ungrouped_tasks': ungrouped_count,
            'fragile_groups': fragile_groups.count(),
            'works_no_variants': works_no_variants.count(),
            'works_no_spec': works_no_spec.count(),
        }

        return TaskDBHealthData(
            stats={
                'total_tasks': total_tasks,
                'total_groups': total_groups_qs.count(),
                'total_works': total_works,
                'total_variants': total_variants,
            },
            orphan_variants={
                'count': orphan_variants.count(),
                'items': orphan_variants.order_by('-created_at')[:10],
            },
            empty_groups={
                'count': empty_groups.count(),
                'items': empty_groups.order_by('name')[:20],
            },
            coverage_issues={
                'count': len(coverage_issues),
                'items': coverage_issues[:20],
            },
            difficulty_dist=self._build_difficulty_distribution(total_tasks),
            ungrouped_tasks={
                'count': ungrouped_count,
                'pct': self._pct(ungrouped_count, total_tasks),
            },
            fragile_groups={
                'count': fragile_groups.count(),
                'items': fragile_groups.order_by('name')[:20],
            },
            works_no_variants={
                'count': works_no_variants.count(),
                'items': works_no_variants[:10],
            },
            works_no_spec={
                'count': works_no_spec.count(),
                'items': works_no_spec[:10],
            },
            type_dist=self._build_task_type_distribution(total_tasks),
            most_used_tasks=Task.objects.annotate(
                variant_count=Count('varianttask'),
            ).filter(variant_count__gt=0).order_by('-variant_count')[:10],
            group_sizes=list(
                total_groups_qs.values('task_count').annotate(
                    group_count=Count('id'),
                ).order_by('task_count'),
            ),
            unverified_tasks={
                'count': unverified_count,
                'pct': self._pct(unverified_count, total_tasks),
            },
            no_source_tasks={
                'count': no_source_count,
                'pct': self._pct(no_source_count, total_tasks),
            },
            no_grade_tasks={
                'count': no_grade_count,
                'pct': self._pct(no_grade_count, total_tasks),
            },
            health=self._build_health_summary(health_source),
            courses=Course.objects.filter(is_active=True).order_by(
                'grade_level',
                'name',
            ),
        )

    def get_heatmap_drilldown_overview(self, topic_id, group_id):
        topic = get_object_or_404(Topic, pk=topic_id)
        groups = StudentGroup.objects.all().order_by('name')
        if group_id:
            selected_group = get_object_or_404(StudentGroup, pk=group_id)
            students = list(
                selected_group.students.all().order_by('last_name', 'first_name'),
            )
        else:
            selected_group = None
            students = list(Student.objects.all().order_by('last_name', 'first_name'))

        return HeatmapDrilldownOverviewData(
            topic=topic,
            groups=groups,
            selected_group=selected_group,
            students=students,
            courses=Course.objects.filter(is_active=True).order_by(
                'grade_level',
                'name',
            ),
        )

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

    def get_heatmap_subtopic_matrix(self, student_ids, topic_id):
        topic = get_object_or_404(Topic, pk=topic_id)
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
            return HeatmapSubtopicMatrixData(
                columns=[],
                rows=[],
                col_averages=[],
            )

        tasks_qs = Task.objects.filter(
            pk__in=all_task_ids,
            topic=topic,
        ).select_related('subtopic')
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
                if not task:
                    continue

                col_key = (
                    task.subtopic_id
                    if task.subtopic_id
                    else f'topic_{task.topic_id}'
                )
                key = (student_id, col_key)
                aggregated[key]['points'] += scores.get('points', 0)
                aggregated[key]['max_points'] += scores.get('max_points', 0)

        subtopic_ids = {
            col_key for _, col_key in aggregated.keys()
            if not str(col_key).startswith('topic_')
        }
        columns = list(
            SubTopic.objects.filter(pk__in=subtopic_ids).order_by(
                'order',
                'name',
            ),
        )
        rows = self._build_subtopic_heatmap_rows(students, columns, aggregated)
        col_averages = self._build_subtopic_heatmap_col_averages(
            students,
            columns,
            aggregated,
        )

        return HeatmapSubtopicMatrixData(
            columns=columns,
            rows=rows,
            col_averages=col_averages,
        )

    def get_heatmap_subtopic_detail(self, subtopic_id, group_id):
        subtopic = get_object_or_404(SubTopic, pk=subtopic_id)
        topic = subtopic.topic
        groups = StudentGroup.objects.all().order_by('name')
        if group_id:
            selected_group = get_object_or_404(StudentGroup, pk=group_id)
            students = list(
                selected_group.students.all().order_by('last_name', 'first_name'),
            )
        else:
            selected_group = None
            students = list(Student.objects.all().order_by('last_name', 'first_name'))

        marks = Mark.objects.filter(
            participation__student__in=students,
        ).select_related('participation__student', 'participation__event')

        all_task_ids = set()
        for mark in marks:
            if mark.task_scores:
                all_task_ids.update(mark.task_scores.keys())

        tasks_qs = Task.objects.filter(
            pk__in=all_task_ids,
            subtopic=subtopic,
        )
        task_map = {str(task.pk): task for task in tasks_qs}
        student_agg = defaultdict(
            lambda: {'points': 0, 'max_points': 0, 'events': set()},
        )
        task_agg = defaultdict(lambda: {'points': 0, 'max_points': 0, 'count': 0})

        for mark in marks:
            if not mark.task_scores:
                continue
            student_id = mark.participation.student_id
            event_name = mark.participation.event.name
            seen = set()
            for task_id, scores in mark.task_scores.items():
                if task_id in seen:
                    continue
                seen.add(task_id)

                task = task_map.get(task_id)
                if not task:
                    continue

                points = scores.get('points', 0)
                max_points = scores.get('max_points', 0)
                student_agg[student_id]['points'] += points
                student_agg[student_id]['max_points'] += max_points
                student_agg[student_id]['events'].add(event_name)
                task_agg[task.id]['points'] += points
                task_agg[task.id]['max_points'] += max_points
                task_agg[task.id]['count'] += 1

        student_rows = self._build_subtopic_detail_student_rows(
            students,
            student_agg,
        )
        task_rows = self._build_subtopic_detail_task_rows(tasks_qs, task_agg)
        total_points = sum(data['points'] for data in student_agg.values())
        total_max = sum(data['max_points'] for data in student_agg.values())
        overall_pct = round(total_points / total_max * 100) if total_max > 0 else None

        return HeatmapSubtopicDetailData(
            subtopic=subtopic,
            topic=topic,
            groups=groups,
            selected_group=selected_group,
            student_rows=student_rows,
            task_rows=task_rows,
            overall_pct=overall_pct,
            overall_css=self._color_class(overall_pct) if overall_pct else 'no-data',
            total_students=len(students),
            students_with_data=sum(
                1 for row in student_rows
                if row['pct'] is not None
            ),
            courses=Course.objects.filter(is_active=True).order_by(
                'grade_level',
                'name',
            ),
        )

    def get_heatmap_student_detail(self, topic_id, student_id, subtopic_id=None):
        topic = get_object_or_404(Topic, pk=topic_id)
        student = get_object_or_404(Student, pk=student_id)
        selected_subtopic = None
        if subtopic_id:
            selected_subtopic = SubTopic.objects.filter(pk=subtopic_id).first()

        marks = Mark.objects.filter(
            participation__student=student,
        ).select_related(
            'participation__event',
            'participation__variant',
        )
        task_map = self._get_task_map_for_marks(marks, topic)
        details = self._build_student_heatmap_details(
            marks,
            task_map,
            selected_subtopic,
        )
        subtopic_summary = self._build_student_subtopic_summary(
            marks,
            task_map,
            topic,
            selected_subtopic,
        )

        return HeatmapStudentDetailData(
            topic=topic,
            student=student,
            selected_subtopic=selected_subtopic,
            details=details,
            subtopic_summary=subtopic_summary,
            courses=Course.objects.filter(is_active=True).order_by(
                'grade_level',
                'name',
            ),
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
                'student': ReportStudentRef(
                    pk=str(student.pk),
                    full_name=student.get_full_name(),
                    short_name=student.get_short_name(),
                ),
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

    def _get_task_map_for_marks(self, marks, topic):
        task_ids = set()
        for mark in marks:
            if mark.task_scores:
                task_ids.update(mark.task_scores.keys())

        tasks = Task.objects.filter(
            pk__in=task_ids,
            topic=topic,
        ).select_related('subtopic')
        return {str(task.pk): task for task in tasks}

    def _build_student_heatmap_details(
        self,
        marks,
        task_map,
        selected_subtopic,
    ):
        details = []
        for mark in marks:
            if not mark.task_scores:
                continue
            event = mark.participation.event
            seen = set()
            for task_id, scores in mark.task_scores.items():
                if task_id in seen:
                    continue
                seen.add(task_id)

                task = task_map.get(task_id)
                if not task:
                    continue
                if selected_subtopic and task.subtopic_id != selected_subtopic.id:
                    continue

                points = scores.get('points', 0)
                max_points = scores.get('max_points', 0)
                pct = round(points / max_points * 100) if max_points > 0 else 0
                details.append({
                    'event': event,
                    'task': task,
                    'subtopic': task.subtopic,
                    'points': points,
                    'max_points': max_points,
                    'pct': pct,
                    'css': self._color_class(pct),
                })

        details.sort(key=lambda detail: (
            detail['subtopic'].name if detail['subtopic'] else '',
            detail['event'].planned_date,
        ))
        return details

    def _build_student_subtopic_summary(
        self,
        marks,
        task_map,
        topic,
        selected_subtopic,
    ):
        aggregated = defaultdict(lambda: {'points': 0, 'max_points': 0})
        for mark in marks:
            if not mark.task_scores:
                continue
            seen = set()
            for task_id, scores in mark.task_scores.items():
                if task_id in seen:
                    continue
                seen.add(task_id)
                task = task_map.get(task_id)
                if not task or not task.subtopic:
                    continue
                aggregated[task.subtopic.id]['points'] += scores.get('points', 0)
                aggregated[task.subtopic.id]['max_points'] += scores.get(
                    'max_points',
                    0,
                )

        summary = []
        for subtopic in SubTopic.objects.filter(topic=topic).order_by('order'):
            data = aggregated.get(subtopic.id)
            is_selected = (
                selected_subtopic
                and subtopic.id == selected_subtopic.id
            )
            if data and data['max_points'] > 0:
                pct = round(data['points'] / data['max_points'] * 100)
                summary.append({
                    'subtopic': subtopic,
                    'points': data['points'],
                    'max_points': data['max_points'],
                    'pct': pct,
                    'css': self._color_class(pct),
                    'is_selected': is_selected,
                })
            else:
                summary.append({
                    'subtopic': subtopic,
                    'pct': None,
                    'css': 'no-data',
                    'is_selected': is_selected,
                })
        return summary

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

    def _build_subtopic_heatmap_rows(self, students, columns, aggregated):
        rows = []
        for student in students:
            cells = []
            total_points = 0
            total_max = 0
            for subtopic in columns:
                data = aggregated.get((student.id, subtopic.id))
                if data and data['max_points'] > 0:
                    pct = round(data['points'] / data['max_points'] * 100)
                    total_points += data['points']
                    total_max += data['max_points']
                    cells.append({
                        'pct': pct,
                        'points': data['points'],
                        'max_points': data['max_points'],
                        'css': self._color_class(pct),
                        'subtopic': subtopic,
                    })
                else:
                    cells.append({
                        'pct': None,
                        'css': 'no-data',
                        'subtopic': subtopic,
                    })

            avg = round(total_points / total_max * 100) if total_max > 0 else None
            rows.append({
                'student': student,
                'cells': cells,
                'avg': avg,
                'avg_css': self._color_class(avg) if avg is not None else 'no-data',
            })
        return rows

    def _build_subtopic_heatmap_col_averages(self, students, columns, aggregated):
        col_averages = []
        for subtopic in columns:
            points = sum(
                aggregated.get((student.id, subtopic.id), {}).get('points', 0)
                for student in students
            )
            max_points = sum(
                aggregated.get((student.id, subtopic.id), {}).get('max_points', 0)
                for student in students
            )
            avg = round(points / max_points * 100) if max_points > 0 else None
            col_averages.append({
                'pct': avg,
                'css': self._color_class(avg) if avg is not None else 'no-data',
            })
        return col_averages

    def _build_subtopic_detail_student_rows(
        self,
        students,
        student_agg,
    ):
        rows = []
        for student in students:
            data = student_agg.get(student.id)
            if data and data['max_points'] > 0:
                pct = round(data['points'] / data['max_points'] * 100)
                rows.append({
                    'student': student,
                    'points': data['points'],
                    'max_points': data['max_points'],
                    'pct': pct,
                    'css': self._color_class(pct),
                    'events': sorted(data['events']),
                })
            else:
                rows.append({
                    'student': student,
                    'pct': None,
                    'css': 'no-data',
                    'events': [],
                })
        return rows

    def _build_subtopic_detail_task_rows(self, tasks_qs, task_agg):
        rows = []
        for task in tasks_qs.order_by('difficulty', 'text'):
            data = task_agg.get(task.id)
            if data and data['max_points'] > 0:
                avg_pct = round(data['points'] / data['max_points'] * 100)
                rows.append({
                    'task': task,
                    'avg_pct': avg_pct,
                    'css': self._color_class(avg_pct),
                    'students_count': data['count'],
                    'total_points': data['points'],
                    'total_max': data['max_points'],
                })
        return rows

    def _build_journal_rows(self, students, events, part_lookup, mark_lookup):
        rows = []
        for student in students:
            cells = []
            total_score = 0
            score_count = 0
            debts = 0

            for event in events:
                participation = part_lookup.get((student.id, event.id))
                mark = mark_lookup.get(participation.id) if participation else None
                cell = self._build_journal_cell(event, participation, mark)

                if cell['status'] == 'graded':
                    total_score += mark.score
                    score_count += 1
                if cell['status'] in ('absent', 'missing'):
                    debts += 1

                cells.append(cell)

            avg_score = (
                round(total_score / score_count, 1)
                if score_count > 0
                else None
            )
            rows.append({
                'student': student,
                'cells': cells,
                'avg_score': avg_score,
                'score_count': score_count,
                'debts': debts,
            })
        return rows

    def _build_journal_cell(self, event, participation, mark):
        cell = {
            'event': event,
            'participation': participation,
            'mark': mark,
            'score': None,
            'status': 'missing',
            'css_class': '',
            'display': '',
            'variant': participation.variant if participation else None,
        }

        if not participation:
            cell['css_class'] = 'journal-missing'
            return cell

        if participation.status == 'absent':
            cell['status'] = 'absent'
            cell['display'] = 'Н'
            cell['css_class'] = 'journal-absent'
        elif mark and mark.score is not None:
            cell['status'] = 'graded'
            cell['score'] = mark.score
            cell['display'] = str(mark.score)
            cell['css_class'] = self._journal_score_css(mark.score)
        elif participation.status in ('assigned', 'started'):
            cell['status'] = 'in_progress'
            cell['display'] = '…'
            cell['css_class'] = 'journal-progress'
        elif participation.status == 'completed':
            cell['status'] = 'completed'
            cell['display'] = '✓'
            cell['css_class'] = 'journal-completed'
        else:
            cell['status'] = 'assigned'
            cell['display'] = '–'

        return cell

    def _journal_score_css(self, score):
        if score >= 5:
            return 'journal-5'
        if score == 4:
            return 'journal-4'
        if score == 3:
            return 'journal-3'
        return 'journal-2'

    def _build_journal_event_stats(self, events, rows):
        event_stats = []
        for event in events:
            graded = 0
            absent = 0
            missing = 0
            total = 0
            for row in rows:
                for cell in row['cells']:
                    if cell['event'].id != event.id:
                        continue
                    total += 1
                    if cell['status'] == 'graded':
                        graded += 1
                    elif cell['status'] == 'absent':
                        absent += 1
                    elif cell['status'] == 'missing':
                        missing += 1
            event_stats.append({
                'event': event,
                'graded': graded,
                'absent': absent,
                'missing': missing,
                'total': total,
            })
        return event_stats

    def _build_coverage_issues(self):
        coverage_issues = []
        for work_group in WorkAnalogGroup.objects.select_related(
            'work',
            'analog_group',
        ).annotate(
            available=Count('analog_group__taskgroup'),
        ):
            if work_group.available < work_group.count:
                coverage_issues.append({
                    'work': work_group.work,
                    'group': work_group.analog_group,
                    'needed': work_group.count,
                    'available': work_group.available,
                    'deficit': work_group.count - work_group.available,
                })
        return coverage_issues

    def _build_difficulty_distribution(self, total_tasks):
        distribution = []
        for item in Task.objects.values('difficulty').annotate(
            count=Count('id'),
        ).order_by('difficulty'):
            difficulty = item['difficulty'] or 0
            count = item['count']
            distribution.append({
                'difficulty': difficulty,
                'count': count,
                'pct': self._pct(count, total_tasks),
            })
        return distribution

    def _build_task_type_distribution(self, total_tasks):
        distribution = list(
            Task.objects.values('task_type').annotate(
                count=Count('id'),
            ).order_by('-count'),
        )
        type_labels = (
            dict(Task.TASK_TYPE_CHOICES)
            if hasattr(Task, 'TASK_TYPE_CHOICES')
            else {}
        )
        for item in distribution:
            item['pct'] = self._pct(item['count'], total_tasks)
            item['label'] = type_labels.get(
                item['task_type'],
                item['task_type'] or '—',
            )
        return distribution

    def _build_health_summary(self, source):
        issues = sum(source.values())
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

    def _issues_text(self, issues):
        if 11 <= issues % 100 <= 19:
            return f'{issues} замечаний'
        if issues % 10 == 1:
            return f'{issues} замечание'
        if 2 <= issues % 10 <= 4:
            return f'{issues} замечания'
        return f'{issues} замечаний'

    def _pct(self, value, total):
        return round(value / total * 100, 1) if total else 0

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
