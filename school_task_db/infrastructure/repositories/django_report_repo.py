"""Django implementation of report repository."""

from collections import defaultdict

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

from core_logic.entities.report import (
    EventsStatusSource,
    DashboardCourseGroupRef,
    DashboardGroupSource,
    DashboardMarkFact,
    DashboardParticipationFact,
    HeatmapCourseOverviewData,
    HeatmapCourseTimelineSource,
    HeatmapDrilldownOverviewData,
    HeatmapDetailScoreFact,
    HeatmapMatrixSource,
    HeatmapOverviewData,
    HeatmapScoreFact,
    HeatmapStudentDetailSource,
    HeatmapSubtopicDetailSource,
    HeatmapTimelineEventRef,
    HeatmapTimelineMarkFact,
    JournalEntryFact,
    JournalParticipationRef,
    JournalSelectData,
    JournalSource,
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
    TaskCoverageFact,
    TaskDBHealthSource,
    TaskDistributionFact,
    TaskGroupSizeFact,
    WorkAnalysisItemSource,
    WorkAnalysisSource,
)
from core_logic.interfaces.report_repo import IReportRepository
from core_logic.services.event_service import EventService
from curriculum.models import Course, CourseAssignment, SubTopic, Topic
from events.models import Event, EventParticipation
from infrastructure.services.attempt_snapshot_queries import (
    latest_attempts_by_participation,
)
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
            groups=[
                ReportGroupRef(
                    pk=str(group.pk),
                    name=group.name,
                    students_count=group.students.count(),
                )
                for group in groups
            ],
            courses=[
                ReportCourseRef(pk=str(course.pk), name=course.name)
                for course in courses
            ],
        )

    def get_journal_source(self, course_id, group_id, year):
        course = get_object_or_404(Course, pk=course_id)
        group = get_object_or_404(StudentGroup, pk=group_id)
        students = list(
            group.students.all().order_by('last_name', 'first_name')
        )
        student_ids = [student.id for student in students]

        event_ids = Event.objects.filter(
            course=course,
            eventparticipation__student__in=student_ids,
        ).values_list('pk', flat=True).distinct()
        events = self._event_summary_queryset(
            Event.objects.filter(pk__in=event_ids),
        ).order_by('planned_date')
        event_refs = {
            event.id: self._report_event_ref(event)
            for event in events
        }
        participations = list(
            EventParticipation.objects.filter(
                event__in=events,
                student_id__in=student_ids,
            ).select_related('student', 'event', 'variant')
        )
        attempts = latest_attempts_by_participation(
            (participation.pk for participation in participations),
            include_task_results=False,
        )
        entries = []
        for participation in participations:
            attempt = attempts.get(participation.id)
            entries.append(JournalEntryFact(
                student_id=str(participation.student_id),
                event_id=str(participation.event_id),
                participation=JournalParticipationRef(
                    pk=str(participation.pk),
                    status=participation.status,
                ),
                mark=(
                    ReportMarkFact(
                        score=attempt.score,
                        points=attempt.points,
                        max_points=attempt.max_points,
                    )
                    if attempt
                    else None
                ),
                variant=(
                    self._report_variant_ref(participation.variant)
                    if participation.variant
                    else None
                ),
            ))

        return JournalSource(
            course=ReportCourseRef(pk=str(course.pk), name=course.name),
            group=ReportGroupRef(
                pk=str(group.pk),
                name=group.name,
                students_count=len(students),
            ),
            students=[self._report_student_ref(student) for student in students],
            events=[event_refs[event.id] for event in events],
            entries=entries,
            courses=[
                ReportCourseRef(pk=str(item.pk), name=item.name)
                for item in self._get_event_scope(year)[2].order_by(
                    'grade_level',
                    'name',
                )
            ],
        )

    def get_task_db_health_source(self):
        total_tasks = Task.objects.count()
        group_records = list(
            AnalogGroup.objects.annotate(
                task_count=Count('taskgroup'),
            ).order_by('name'),
        )
        total_works = Work.objects.count()
        total_variants = Variant.objects.count()
        orphan_variants = Variant.objects.filter(work__isnull=True)
        tasks_in_groups = set(TaskGroup.objects.values_list('task_id', flat=True))
        ungrouped_count = Task.objects.exclude(id__in=tasks_in_groups).count()
        works_no_variants = Work.objects.annotate(
            variant_count=Count('variant'),
        ).filter(variant_count=0)
        works_no_spec = Work.objects.annotate(
            spec_count=Count('workanaloggroup'),
        ).filter(spec_count=0)
        unverified_count = Task.objects.filter(is_verified=False).count()
        no_source_count = Task.objects.filter(source__isnull=True).count()
        no_grade_count = Task.objects.filter(grade__isnull=True).count()

        type_labels = dict(getattr(Task, 'TASK_TYPE_CHOICES', ()))
        return TaskDBHealthSource(
            total_tasks=total_tasks,
            total_works=total_works,
            total_variants=total_variants,
            orphan_variants_count=orphan_variants.count(),
            orphan_variant_samples=[
                self._report_variant_ref(variant)
                for variant in orphan_variants.order_by('-created_at')[:10]
            ],
            group_sizes=[
                TaskGroupSizeFact(
                    group=self._report_analog_group_ref(group),
                    task_count=group.task_count,
                )
                for group in group_records
            ],
            coverage=[
                TaskCoverageFact(
                    work=self._report_work_ref(work_group.work),
                    group=self._report_analog_group_ref(
                        work_group.analog_group,
                    ),
                    needed=work_group.count,
                    available=work_group.available,
                )
                for work_group in WorkAnalogGroup.objects.select_related(
                    'work',
                    'analog_group',
                ).annotate(available=Count('analog_group__taskgroup'))
            ],
            ungrouped_tasks_count=ungrouped_count,
            works_no_variants_count=works_no_variants.count(),
            works_no_variant_samples=[
                self._report_work_ref(work)
                for work in works_no_variants[:10]
            ],
            works_no_spec_count=works_no_spec.count(),
            works_no_spec_samples=[
                self._report_work_ref(work)
                for work in works_no_spec[:10]
            ],
            difficulty_counts=[
                TaskDistributionFact(
                    key=item['difficulty'],
                    count=item['count'],
                )
                for item in Task.objects.values('difficulty').annotate(
                    count=Count('id'),
                ).order_by('difficulty')
            ],
            type_counts=[
                TaskDistributionFact(
                    key=item['task_type'],
                    count=item['count'],
                    label=type_labels.get(
                        item['task_type'],
                        item['task_type'] or '—',
                    ),
                )
                for item in Task.objects.values('task_type').annotate(
                    count=Count('id'),
                ).order_by('-count')
            ],
            most_used_tasks=[
                self._report_task_usage_ref(task)
                for task in Task.objects.annotate(
                    variant_count=Count('varianttask'),
                ).filter(variant_count__gt=0).order_by('-variant_count')[:10]
            ],
            unverified_tasks_count=unverified_count,
            no_source_tasks_count=no_source_count,
            no_grade_tasks_count=no_grade_count,
            courses=[
                ReportCourseRef(pk=str(course.pk), name=course.name)
                for course in Course.objects.filter(is_active=True).order_by(
                    'grade_level',
                    'name',
                )
            ],
        )

    def get_heatmap_drilldown_overview(self, topic_id, group_id):
        topic = get_object_or_404(Topic, pk=topic_id)
        groups = list(StudentGroup.objects.all().order_by('name'))
        if group_id:
            selected_group = get_object_or_404(StudentGroup, pk=group_id)
            students = list(
                selected_group.students.all().order_by('last_name', 'first_name'),
            )
        else:
            selected_group = None
            students = list(Student.objects.all().order_by('last_name', 'first_name'))

        return HeatmapDrilldownOverviewData(
            topic=self._report_heatmap_column_ref(topic),
            groups=[self._report_group_ref(group) for group in groups],
            selected_group=(
                self._report_group_ref(selected_group)
                if selected_group
                else None
            ),
            students=[self._report_student_ref(student) for student in students],
            courses=self._active_course_refs(),
        )

    def get_heatmap_course_overview(self, course_id, group_id):
        course = get_object_or_404(Course, pk=course_id)
        course_groups = list(course.student_groups.all().order_by('name'))

        if group_id:
            selected_group = get_object_or_404(StudentGroup, pk=group_id)
            students = list(
                selected_group.students.all().order_by('last_name', 'first_name'),
            )
        elif course_groups:
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
            course=self._report_course_ref(course),
            groups=[self._report_group_ref(group) for group in course_groups],
            selected_group=(
                self._report_group_ref(selected_group)
                if selected_group
                else None
            ),
            students=[self._report_student_ref(student) for student in students],
            course_works=[self._report_work_ref(work) for work in course_works],
            courses=self._active_course_refs(),
            active_course_pk=str(course.pk),
        )

    def get_heatmap_overview(self, group_id):
        groups = list(StudentGroup.objects.all().order_by('name'))
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
            groups=[self._report_group_ref(group) for group in groups],
            selected_group=(
                self._report_group_ref(selected_group)
                if selected_group
                else None
            ),
            students=[self._report_student_ref(student) for student in students],
            sections=sections,
            courses=self._active_course_refs(),
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

    def get_heatmap_course_timeline_source(self, student_ids, work_ids):
        events = list(Event.objects.filter(
            work_id__in=work_ids,
            status='graded',
        ).order_by('planned_date'))
        participations = list(
            EventParticipation.objects.filter(
                event__in=events,
                student_id__in=student_ids,
            ).only('pk', 'event_id')
        )
        attempts = latest_attempts_by_participation(
            (participation.pk for participation in participations),
            include_task_results=False,
        )

        return HeatmapCourseTimelineSource(
            events=[
                HeatmapTimelineEventRef(
                    pk=str(event.pk),
                    name=event.name,
                    planned_date=event.planned_date,
                )
                for event in events
            ],
            marks=[
                HeatmapTimelineMarkFact(
                    event_id=str(participation.event_id),
                    points=attempt.points or 0,
                    max_points=attempt.max_points or 0,
                )
                for participation in participations
                if (attempt := attempts.get(participation.pk)) is not None
            ],
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
        groups, students = self._get_student_scope(year)
        event_rows = list(
            self._event_summary_queryset(events).order_by('-planned_date')
        )
        participation_rows = list(
            participations.only(
                'pk',
                'student_id',
                'event_id',
                'status',
            )
        )
        attempts = latest_attempts_by_participation(
            (participation.pk for participation in participation_rows),
            include_task_results=False,
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
                for participation in participation_rows
            ],
            marks=[
                DashboardMarkFact(
                    student_id=str(participation.student_id),
                    event_id=str(participation.event_id),
                    score=attempt.score,
                    checked_at=attempt.checked_at_snapshot,
                )
                for participation in participation_rows
                if (attempt := attempts.get(participation.pk)) is not None
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
                for event in self._event_summary_queryset(events).order_by(
                    '-planned_date',
                )
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
        events, participations, courses = self._get_event_scope(year)
        scoped_participations = list(
            participations.select_related('event').only(
                'pk',
                'event_id',
                'event__work_id',
            )
        )
        attempts = latest_attempts_by_participation(
            (participation.pk for participation in scoped_participations),
            include_task_results=False,
        )
        attempts_by_work = defaultdict(list)
        for participation in scoped_participations:
            attempt = attempts.get(participation.pk)
            if attempt is not None and attempt.score is not None:
                attempts_by_work[participation.event.work_id].append(
                    attempt,
                )

        work_sources = []
        for work in Work.objects.all():
            work_events = list(
                self._event_summary_queryset(
                    events.filter(work=work),
                ).order_by('-planned_date')
            )
            if not work_events:
                continue

            work_sources.append(
                WorkAnalysisItemSource(
                    work=self._report_work_ref(work),
                    events_count=len(work_events),
                    marks=[
                        ReportMarkFact(
                            score=attempt.score,
                            points=attempt.points,
                            max_points=attempt.max_points,
                        )
                        for attempt in attempts_by_work[work.pk]
                    ],
                    events=[
                        self._report_event_ref(event)
                        for event in work_events
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
        groups, students = self._get_student_scope(year)
        groups = groups.order_by('name')

        selected_group = None
        if group_id:
            selected_group = groups.filter(pk=group_id).first()
            if selected_group:
                students = selected_group.students.all()

        students = list(students.order_by('last_name', 'first_name'))
        student_ids = [student.pk for student in students]
        scoped_participations = list(
            participations.filter(
                student_id__in=student_ids,
            ).only('pk', 'student_id', 'status', 'created_at')
        )
        attempts = latest_attempts_by_participation(
            (participation.pk for participation in scoped_participations),
            include_task_results=False,
        )
        participations_by_student = defaultdict(list)
        marks_by_student = defaultdict(list)
        for participation in scoped_participations:
            participations_by_student[participation.student_id].append(
                StudentPerformanceParticipationFact(
                    status=participation.status,
                    created_at=participation.created_at,
                )
            )
            attempt = attempts.get(participation.pk)
            if attempt is None or attempt.score is None:
                continue
            marks_by_student[participation.student_id].append(
                ReportMarkFact(
                    score=attempt.score,
                    points=attempt.points,
                    max_points=attempt.max_points,
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

    def _report_student_ref(self, student):
        return ReportStudentRef(
            pk=str(student.pk),
            full_name=student.get_full_name(),
            short_name=student.get_short_name(),
            last_name=student.last_name,
            first_name=student.first_name,
        )

    def _report_group_ref(self, group):
        return ReportGroupRef(
            pk=str(group.pk),
            name=group.name,
            students_count=group.students.count(),
        )

    def _report_course_ref(self, course):
        return ReportCourseRef(pk=str(course.pk), name=course.name)

    def _active_course_refs(self):
        return [
            self._report_course_ref(course)
            for course in Course.objects.filter(is_active=True).order_by(
                'grade_level',
                'name',
            )
        ]

    def _report_heatmap_column_ref(self, item):
        return ReportHeatmapColumnRef(
            pk=str(item.pk),
            name=item.name,
            section=getattr(item, 'section', ''),
        )

    def _report_event_ref(self, event):
        progress_percentage = EventService.progress_percentage(
            event.participants_count_value,
            event.completed_count_value,
        )
        return ReportEventRef(
            pk=str(event.pk),
            name=event.name,
            status=event.status,
            status_display=event.get_status_display(),
            planned_date=event.planned_date,
            actual_end=event.actual_end,
            location=event.location,
            work=self._report_work_ref(event.work),
            participants_count=event.participants_count_value,
            graded_count=event.graded_count_value,
            progress_percentage=progress_percentage,
        )

    @staticmethod
    def _event_summary_queryset(queryset):
        return queryset.select_related('work').annotate(
            participants_count_value=Count(
                'eventparticipation',
                distinct=True,
            ),
            completed_count_value=Count(
                'eventparticipation',
                filter=Q(
                    eventparticipation__status__in=('completed', 'graded'),
                ),
                distinct=True,
            ),
            graded_count_value=Count(
                'eventparticipation',
                filter=Q(eventparticipation__status='graded'),
                distinct=True,
            ),
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
