"""Django implementation of report repository."""

from collections import defaultdict

from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404

from core_logic.entities.report import (
    EventsStatusSource,
    DashboardCourseGroupRef,
    DashboardGroupSource,
    DashboardMarkFact,
    DashboardParticipationFact,
    HeatmapCourseOverviewData,
    HeatmapCourseTimelineData,
    HeatmapDrilldownOverviewData,
    HeatmapDetailScoreFact,
    HeatmapMatrixSource,
    HeatmapOverviewData,
    HeatmapScoreFact,
    HeatmapStudentDetailSource,
    HeatmapSubtopicDetailSource,
    HeatmapTopicMatrixData,
    JournalData,
    JournalSelectData,
    ReportsDashboardSource,
    ReportAnalogGroupRef,
    ReportActivityRef,
    ReportCourseRef,
    ReportEventRef,
    ReportGroupRef,
    ReportHeatmapColumnRef,
    ReportMarkFact,
    ReportStudentRef,
    ReportTaskRef,
    ReportTaskUsageRef,
    ReportVariantRef,
    ReportWorkRef,
    StudentPerformanceItemSource,
    StudentPerformanceParticipationFact,
    StudentPerformanceSource,
    TaskDBHealthData,
    WorkAnalysisItemSource,
    WorkAnalysisSource,
)
from core_logic.interfaces.report_repo import IReportRepository
from curriculum.models import Course, CourseAssignment, SubTopic, Topic
from events.models import Event, EventParticipation, Mark
from students.models import Student, StudentGroup, StudentTaskLog
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
        event_refs = {
            event.id: self._report_event_ref(event)
            for event in events
        }
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
        all_rows = self._build_journal_rows(
            students,
            events,
            part_lookup,
            mark_lookup,
            event_refs,
        )
        rows = (
            [row for row in all_rows if row['debts'] > 0]
            if show_debts_only
            else all_rows
        )

        return JournalData(
            course=course,
            group=group,
            events=[event_refs[event.id] for event in events],
            event_stats=self._build_journal_event_stats(
                events,
                all_rows,
                event_refs,
            ),
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
                'items': [
                    self._report_variant_ref(variant)
                    for variant in orphan_variants.order_by('-created_at')[:10]
                ],
            },
            empty_groups={
                'count': empty_groups.count(),
                'items': [
                    self._report_analog_group_ref(group)
                    for group in empty_groups.order_by('name')[:20]
                ],
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
                'items': [
                    self._report_analog_group_ref(group)
                    for group in fragile_groups.order_by('name')[:20]
                ],
            },
            works_no_variants={
                'count': works_no_variants.count(),
                'items': [
                    self._report_work_ref(work)
                    for work in works_no_variants[:10]
                ],
            },
            works_no_spec={
                'count': works_no_spec.count(),
                'items': [
                    self._report_work_ref(work)
                    for work in works_no_spec[:10]
                ],
            },
            type_dist=self._build_task_type_distribution(total_tasks),
            most_used_tasks=[
                self._report_task_usage_ref(task)
                for task in Task.objects.annotate(
                    variant_count=Count('varianttask'),
                ).filter(variant_count__gt=0).order_by('-variant_count')[:10]
            ],
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

    def get_heatmap_topic_matrix_source(self, student_ids, section_filter=''):
        students = list(
            Student.objects.filter(pk__in=student_ids).order_by(
                'last_name',
                'first_name',
            ),
        )
        task_logs = StudentTaskLog.objects.filter(
            student__in=students,
            topic__isnull=False,
        ).select_related('topic')
        if section_filter:
            task_logs = task_logs.filter(topic__section=section_filter)

        topic_ids = set(task_logs.values_list('topic_id', flat=True))
        topics = list(
            Topic.objects.filter(pk__in=topic_ids).order_by(
                'section',
                'order',
                'name',
            ),
        )
        return HeatmapMatrixSource(
            students=[
                self._report_student_ref(student)
                for student in students
            ],
            columns=[
                ReportHeatmapColumnRef(
                    pk=str(topic.pk),
                    name=topic.name,
                    section=topic.section,
                )
                for topic in topics
            ],
            scores=[
                HeatmapScoreFact(
                    student_id=str(task_log.student_id),
                    column_id=str(task_log.topic_id),
                    points=task_log.points or 0,
                    max_points=task_log.max_points or 0,
                )
                for task_log in task_logs
            ],
        )

    def get_heatmap_course_topic_matrix_source(self, student_ids, work_ids):
        students = list(
            Student.objects.filter(pk__in=student_ids).order_by(
                'last_name',
                'first_name',
            ),
        )
        task_logs = StudentTaskLog.objects.filter(
            student__in=students,
            event__work_id__in=work_ids,
            topic__isnull=False,
        ).select_related('topic')

        topic_ids = set(task_logs.values_list('topic_id', flat=True))
        topics = list(
            Topic.objects.filter(pk__in=topic_ids).order_by(
                'section',
                'order',
                'name',
            ),
        )
        return HeatmapMatrixSource(
            students=[
                self._report_student_ref(student)
                for student in students
            ],
            columns=[
                ReportHeatmapColumnRef(
                    pk=str(topic.pk),
                    name=topic.name,
                    section=topic.section,
                )
                for topic in topics
            ],
            scores=[
                HeatmapScoreFact(
                    student_id=str(task_log.student_id),
                    column_id=str(task_log.topic_id),
                    points=task_log.points or 0,
                    max_points=task_log.max_points or 0,
                )
                for task_log in task_logs
            ],
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

            totals = marks.aggregate(
                total_points=Sum('points'),
                total_max=Sum('max_points'),
            )
            total_points = totals['total_points'] or 0
            total_max = totals['total_max'] or 0

            if total_max > 0:
                dates.append(event.planned_date.strftime('%Y-%m-%d'))
                averages.append(round(total_points / total_max * 100))
                labels.append(event.name)

        return HeatmapCourseTimelineData(
            dates=dates,
            averages=averages,
            labels=labels,
        )

    def get_heatmap_subtopic_matrix_source(self, student_ids, topic_id):
        topic = get_object_or_404(Topic, pk=topic_id)
        students = list(
            Student.objects.filter(pk__in=student_ids).order_by(
                'last_name',
                'first_name',
            ),
        )
        task_logs = StudentTaskLog.objects.filter(
            student__in=students,
            topic=topic,
            subtopic__isnull=False,
        ).select_related('subtopic')

        subtopic_ids = set(task_logs.values_list('subtopic_id', flat=True))
        subtopics = list(
            SubTopic.objects.filter(pk__in=subtopic_ids).order_by(
                'order',
                'name',
            ),
        )
        return HeatmapMatrixSource(
            students=[
                self._report_student_ref(student)
                for student in students
            ],
            columns=[
                ReportHeatmapColumnRef(
                    pk=str(subtopic.pk),
                    name=subtopic.name,
                )
                for subtopic in subtopics
            ],
            scores=[
                HeatmapScoreFact(
                    student_id=str(task_log.student_id),
                    column_id=str(task_log.subtopic_id),
                    points=task_log.points or 0,
                    max_points=task_log.max_points or 0,
                )
                for task_log in task_logs
            ],
        )

    def get_heatmap_subtopic_detail_source(self, subtopic_id, group_id):
        subtopic = get_object_or_404(SubTopic, pk=subtopic_id)
        topic = subtopic.topic
        group_models = list(StudentGroup.objects.all().order_by('name'))
        if group_id:
            selected_group_model = get_object_or_404(StudentGroup, pk=group_id)
            students = list(
                selected_group_model.students.all().order_by(
                    'last_name',
                    'first_name',
                ),
            )
        else:
            selected_group_model = None
            students = list(Student.objects.all().order_by('last_name', 'first_name'))

        task_logs = StudentTaskLog.objects.filter(
            student__in=students,
            subtopic=subtopic,
        ).select_related('task', 'event')
        task_ids = set(task_logs.values_list('task_id', flat=True))
        task_models = list(
            Task.objects.filter(pk__in=task_ids).order_by(
                'difficulty',
                'text',
            ),
        )

        return HeatmapSubtopicDetailSource(
            subtopic=ReportHeatmapColumnRef(
                pk=str(subtopic.pk),
                name=subtopic.name,
            ),
            topic=ReportHeatmapColumnRef(
                pk=str(topic.pk),
                name=topic.name,
                section=topic.section,
            ),
            groups=[
                ReportGroupRef(
                    pk=str(group.pk),
                    name=group.name,
                    students_count=group.students.count(),
                )
                for group in group_models
            ],
            selected_group=(
                ReportGroupRef(
                    pk=str(selected_group_model.pk),
                    name=selected_group_model.name,
                    students_count=selected_group_model.students.count(),
                )
                if selected_group_model
                else None
            ),
            students=[
                self._report_student_ref(student)
                for student in students
            ],
            tasks=[
                ReportTaskRef(
                    pk=str(task.pk),
                    text=task.text,
                    difficulty=task.difficulty,
                    difficulty_display=task.get_difficulty_display(),
                )
                for task in task_models
            ],
            scores=[
                HeatmapDetailScoreFact(
                    student_id=str(task_log.student_id),
                    task_id=str(task_log.task_id),
                    subtopic_id=str(task_log.subtopic_id),
                    points=task_log.points or 0,
                    max_points=task_log.max_points or 0,
                    event=(
                        ReportActivityRef(
                            pk=str(task_log.event.pk),
                            name=task_log.event.name,
                            planned_date=task_log.event.planned_date,
                        )
                        if task_log.event
                        else None
                    ),
                )
                for task_log in task_logs
            ],
            courses=[
                ReportCourseRef(
                    pk=str(course.pk),
                    name=course.name,
                )
                for course in Course.objects.filter(is_active=True).order_by(
                    'grade_level',
                    'name',
                )
            ],
        )

    def get_heatmap_student_detail_source(
        self,
        topic_id,
        student_id,
        subtopic_id=None,
    ):
        topic = get_object_or_404(Topic, pk=topic_id)
        student = get_object_or_404(Student, pk=student_id)
        selected_subtopic_model = None
        if subtopic_id:
            selected_subtopic_model = SubTopic.objects.filter(
                pk=subtopic_id,
                topic=topic,
            ).first()

        task_logs = list(
            StudentTaskLog.objects.filter(
                student=student,
                topic=topic,
            ).select_related('task', 'event', 'subtopic'),
        )
        task_ids = {task_log.task_id for task_log in task_logs}
        task_models = list(
            Task.objects.filter(pk__in=task_ids).order_by(
                'difficulty',
                'text',
            ),
        )
        subtopic_models = list(
            SubTopic.objects.filter(topic=topic).order_by('order', 'name'),
        )

        return HeatmapStudentDetailSource(
            topic=ReportHeatmapColumnRef(
                pk=str(topic.pk),
                name=topic.name,
                section=topic.section,
            ),
            student=self._report_student_ref(student),
            selected_subtopic=(
                ReportHeatmapColumnRef(
                    pk=str(selected_subtopic_model.pk),
                    name=selected_subtopic_model.name,
                )
                if selected_subtopic_model
                else None
            ),
            subtopics=[
                ReportHeatmapColumnRef(
                    pk=str(subtopic.pk),
                    name=subtopic.name,
                )
                for subtopic in subtopic_models
            ],
            tasks=[
                ReportTaskRef(
                    pk=str(task.pk),
                    text=task.text,
                    difficulty=task.difficulty,
                    difficulty_display=task.get_difficulty_display(),
                )
                for task in task_models
            ],
            scores=[
                HeatmapDetailScoreFact(
                    student_id=str(task_log.student_id),
                    task_id=str(task_log.task_id),
                    subtopic_id=str(task_log.subtopic_id or ''),
                    points=task_log.points or 0,
                    max_points=task_log.max_points or 0,
                    event=(
                        ReportActivityRef(
                            pk=str(task_log.event.pk),
                            name=task_log.event.name,
                            planned_date=task_log.event.planned_date,
                        )
                        if task_log.event
                        else None
                    ),
                )
                for task_log in task_logs
            ],
            courses=[
                ReportCourseRef(
                    pk=str(course.pk),
                    name=course.name,
                )
                for course in Course.objects.filter(is_active=True).order_by(
                    'grade_level',
                    'name',
                )
            ],
        )

    def get_reports_dashboard_source(self, year):
        events, participations, courses = self._get_event_scope(year)
        marks = self._get_marks_scope(year)
        groups, students = self._get_student_scope(year)
        event_rows = list(
            events.select_related('work').order_by('-planned_date')
        )
        course_rows = list(courses.order_by('grade_level', 'name'))
        return ReportsDashboardSource(
            total_students=students.count(),
            total_works=Work.objects.count(),
            events=[
                self._report_event_ref(event)
                for event in event_rows
            ],
            participations=[
                DashboardParticipationFact(
                    student_id=str(participation.student_id),
                    event_id=str(participation.event_id),
                    status=participation.status,
                )
                for participation in participations.only(
                    'student_id',
                    'event_id',
                    'status',
                )
            ],
            marks=[
                DashboardMarkFact(
                    student_id=str(mark.participation.student_id),
                    event_id=str(mark.participation.event_id),
                    score=mark.score,
                    checked_at=mark.checked_at,
                )
                for mark in marks.select_related('participation')
            ],
            groups=[
                self._dashboard_group_source(group, year)
                for group in groups.order_by('name')
            ],
            courses=[
                ReportCourseRef(pk=str(course.pk), name=course.name)
                for course in course_rows
            ],
        )

    def _dashboard_group_source(self, group, year):
        linked_courses = group.courses.all()
        if year:
            linked_courses = linked_courses.filter(year_id=year.pk)
        return DashboardGroupSource(
            group=ReportGroupRef(
                pk=str(group.pk),
                name=group.name,
                students_count=group.students.count(),
            ),
            student_ids=[
                str(student_id)
                for student_id in group.students.values_list('pk', flat=True)
            ],
            course_links=[
                DashboardCourseGroupRef(
                    course_id=str(course.pk),
                    course_name=course.name,
                    group_id=str(group.pk),
                    group_name=group.name,
                )
                for course in linked_courses
            ],
        )

    def get_events_status_source(self, year):
        events, participations, courses = self._get_event_scope(year)
        return EventsStatusSource(
            events=[
                self._report_event_ref(event)
                for event in events.select_related('work').order_by('-planned_date')
            ],
            participation_statuses=list(
                participations.values_list('status', flat=True)
            ),
            courses=[
                ReportCourseRef(pk=str(course.pk), name=course.name)
                for course in courses.order_by('grade_level', 'name')
            ],
        )

    def get_work_analysis_source(self, year):
        events, _, courses = self._get_event_scope(year)
        marks = self._get_marks_scope(year)

        work_sources = []
        for work in Work.objects.all():
            work_events = events.filter(work=work)
            work_marks = marks.filter(
                participation__event__work=work,
                score__isnull=False,
            )

            if work_events.count() == 0:
                continue

            work_sources.append(
                WorkAnalysisItemSource(
                    work=self._report_work_ref(work),
                    events_count=work_events.count(),
                    marks=[
                        ReportMarkFact(
                            score=mark.score,
                            points=mark.points,
                            max_points=mark.max_points,
                        )
                        for mark in work_marks
                    ],
                ),
            )

        return WorkAnalysisSource(
            works=work_sources,
            courses=[
                ReportCourseRef(pk=str(course.pk), name=course.name)
                for course in courses.order_by('grade_level', 'name')
            ],
        )

    def get_student_performance_source(self, year, group_id):
        _, participations, courses = self._get_event_scope(year)
        marks = self._get_marks_scope(year)
        groups, students = self._get_student_scope(year)
        groups = groups.order_by('name')

        selected_group = None
        if group_id:
            selected_group = groups.filter(pk=group_id).first()
            if selected_group:
                students = selected_group.students.all()

        students = list(students.order_by('last_name', 'first_name'))
        student_ids = [student.pk for student in students]
        participations_by_student = defaultdict(list)
        for participation in participations.filter(
            student_id__in=student_ids,
        ).only('student_id', 'status', 'created_at'):
            participations_by_student[participation.student_id].append(
                StudentPerformanceParticipationFact(
                    status=participation.status,
                    created_at=participation.created_at,
                )
            )
        marks_by_student = defaultdict(list)
        for mark in marks.filter(
            participation__student_id__in=student_ids,
        ).select_related('participation'):
            marks_by_student[mark.participation.student_id].append(
                ReportMarkFact(
                    score=mark.score,
                    points=mark.points,
                    max_points=mark.max_points,
                )
            )

        return StudentPerformanceSource(
            students=[
                StudentPerformanceItemSource(
                    student=self._report_student_ref(student),
                    participations=participations_by_student[student.pk],
                    marks=marks_by_student[student.pk],
                )
                for student in students
                if participations_by_student[student.pk]
            ],
            groups=[
                ReportGroupRef(
                    pk=str(group.pk),
                    name=group.name,
                    students_count=group.students.count(),
                )
                for group in groups
            ],
            selected_group=(
                ReportGroupRef(
                    pk=str(selected_group.pk),
                    name=selected_group.name,
                    students_count=selected_group.students.count(),
                )
                if selected_group
                else None
            ),
            courses=[
                ReportCourseRef(pk=str(course.pk), name=course.name)
                for course in courses.order_by('grade_level', 'name')
            ],
        )

    def _get_event_scope(self, year):
        if year:
            date_range = (year.start_date, year.end_date)
            events = Event.objects.filter(planned_date__range=date_range)
            participations = EventParticipation.objects.filter(
                event__planned_date__range=date_range,
            )
            courses = Course.objects.filter(year_id=year.pk, is_active=True)
        else:
            events = Event.objects.all()
            participations = EventParticipation.objects.all()
            courses = Course.objects.filter(is_active=True)

        return events, participations, courses

    def _get_student_scope(self, year):
        if year:
            return (
                StudentGroup.objects.filter(academic_year_id=year.pk),
                Student.objects.filter(
                    studentgroup__academic_year_id=year.pk,
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

    def _build_journal_rows(
        self,
        students,
        events,
        part_lookup,
        mark_lookup,
        event_refs,
    ):
        rows = []
        for student in students:
            cells = []
            total_score = 0
            score_count = 0
            debts = 0

            for event in events:
                participation = part_lookup.get((student.id, event.id))
                mark = mark_lookup.get(participation.id) if participation else None
                cell = self._build_journal_cell(
                    event_refs[event.id],
                    participation,
                    mark,
                )

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

    def _report_student_ref(self, student):
        return ReportStudentRef(
            pk=str(student.pk),
            full_name=student.get_full_name(),
            short_name=student.get_short_name(),
        )

    def _report_event_ref(self, event):
        return ReportEventRef(
            pk=str(event.pk),
            name=event.name,
            status=event.status,
            status_display=event.get_status_display(),
            planned_date=event.planned_date,
            actual_end=event.actual_end,
            location=event.location,
            work=self._report_work_ref(event.work),
            participants_count=event.get_participants_count(),
            graded_count=event.get_graded_count(),
            progress_percentage=event.get_progress_percentage(),
        )

    def _report_work_ref(self, work):
        variant_count = getattr(work, 'variant_count', None)
        if variant_count is None:
            variant_count = work.variant_set.count()
        return ReportWorkRef(
            pk=str(work.pk),
            name=work.name,
            work_type=work.work_type,
            work_type_display=work.get_work_type_display(),
            duration=work.duration,
            variant_count=variant_count,
        )

    def _report_variant_ref(self, variant):
        return ReportVariantRef(
            pk=str(variant.pk),
            short_uuid=variant.get_short_uuid(),
            number=variant.number,
            work_name_snapshot=variant.work_name_snapshot,
        )

    def _report_analog_group_ref(self, group):
        return ReportAnalogGroupRef(
            pk=str(group.pk),
            name=group.name,
        )

    def _report_task_usage_ref(self, task):
        return ReportTaskUsageRef(
            pk=str(task.pk),
            short_uuid=task.get_short_uuid(),
            text=task.text,
            variant_count=task.variant_count,
        )

    def _journal_score_css(self, score):
        if score >= 5:
            return 'journal-5'
        if score == 4:
            return 'journal-4'
        if score == 3:
            return 'journal-3'
        return 'journal-2'

    def _build_journal_event_stats(self, events, rows, event_refs):
        event_stats = []
        for event in events:
            graded = 0
            absent = 0
            missing = 0
            total = 0
            for row in rows:
                for cell in row['cells']:
                    if cell['event'].pk != str(event.pk):
                        continue
                    total += 1
                    if cell['status'] == 'graded':
                        graded += 1
                    elif cell['status'] == 'absent':
                        absent += 1
                    elif cell['status'] == 'missing':
                        missing += 1
            event_stats.append({
                'event': event_refs[event.id],
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
                    'work': self._report_work_ref(work_group.work),
                    'group': self._report_analog_group_ref(work_group.analog_group),
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

    def _average_mark_percentage(self, marks, default=0):
        totals = marks.aggregate(
            total_points=Sum('points'),
            total_max=Sum('max_points'),
        )
        total_points = totals['total_points'] or 0
        total_max = totals['total_max'] or 0
        return round(total_points / total_max * 100) if total_max > 0 else default
