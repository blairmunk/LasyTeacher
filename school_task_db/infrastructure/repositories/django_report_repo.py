"""Django implementation of heatmap report repository."""

from django.shortcuts import get_object_or_404

from core_logic.entities.report import (
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
    ReportActivityRef,
    ReportCourseRef,
    ReportGroupRef,
    ReportHeatmapColumnRef,
    ReportStudentRef,
    ReportTaskRef,
    ReportWorkRef,
)
from core_logic.interfaces.report_repo import IHeatmapRepository
from curriculum.models import Course, CourseAssignment, SubTopic, Topic
from events.models import Event, EventParticipation
from infrastructure.services.attempt_snapshot_queries import (
    latest_attempts_by_participation,
)
from infrastructure.services.captured_task_result_queries import (
    latest_assessable_task_results,
)
from students.models import Student, StudentGroup


class DjangoReportRepository(IHeatmapRepository):
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
        task_results = self._latest_attempt_task_results(student_ids)
        topic_sections = self._topic_sections(task_results)
        topic_orders = self._topic_orders(task_results)
        columns = {}
        scores = []
        for result in task_results:
            topic_id = result.task.topic_id
            section = (
                result.task.topic_section
                or topic_sections.get(topic_id, '')
            )
            if not topic_id or (section_filter and section != section_filter):
                continue
            columns.setdefault(
                topic_id,
                ReportHeatmapColumnRef(
                    pk=topic_id,
                    name=result.task.topic_name,
                    section=section,
                ),
            )
            scores.append(HeatmapScoreFact(
                student_id=result.student_id,
                column_id=topic_id,
                points=result.points,
                max_points=result.max_points,
            ))
        return HeatmapMatrixSource(
            students=[
                self._report_student_ref(student)
                for student in students
            ],
            columns=sorted(
                columns.values(),
                key=lambda item: (
                    item.section,
                    topic_orders.get(item.pk, 0),
                    item.name,
                    item.pk,
                ),
            ),
            scores=scores,
        )

    def get_heatmap_course_topic_matrix_source(self, student_ids, work_ids):
        students = list(
            Student.objects.filter(pk__in=student_ids).order_by(
                'last_name',
                'first_name',
            ),
        )
        task_results = self._latest_attempt_task_results(
            student_ids,
            work_ids=work_ids,
        )
        topic_sections = self._topic_sections(task_results)
        topic_orders = self._topic_orders(task_results)
        columns = {}
        scores = []
        for result in task_results:
            topic_id = result.task.topic_id
            if not topic_id:
                continue
            section = (
                result.task.topic_section
                or topic_sections.get(topic_id, '')
            )
            columns.setdefault(
                topic_id,
                ReportHeatmapColumnRef(
                    pk=topic_id,
                    name=result.task.topic_name,
                    section=section,
                ),
            )
            scores.append(HeatmapScoreFact(
                student_id=result.student_id,
                column_id=topic_id,
                points=result.points,
                max_points=result.max_points,
            ))
        return HeatmapMatrixSource(
            students=[
                self._report_student_ref(student)
                for student in students
            ],
            columns=sorted(
                columns.values(),
                key=lambda item: (
                    item.section,
                    topic_orders.get(item.pk, 0),
                    item.name,
                    item.pk,
                ),
            ),
            scores=scores,
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
        task_results = self._latest_attempt_task_results(student_ids)
        subtopic_orders = self._subtopic_orders(task_results)
        columns = {}
        scores = []
        for result in task_results:
            if result.task.topic_id != str(topic.pk):
                continue
            subtopic_id = result.task.subtopic_id
            if not subtopic_id:
                continue
            columns.setdefault(
                subtopic_id,
                ReportHeatmapColumnRef(
                    pk=subtopic_id,
                    name=result.task.subtopic_name,
                ),
            )
            scores.append(HeatmapScoreFact(
                student_id=result.student_id,
                column_id=subtopic_id,
                points=result.points,
                max_points=result.max_points,
            ))
        return HeatmapMatrixSource(
            students=[
                self._report_student_ref(student)
                for student in students
            ],
            columns=sorted(
                columns.values(),
                key=lambda item: (
                    subtopic_orders.get(item.pk, 0),
                    item.name,
                    item.pk,
                ),
            ),
            scores=scores,
        )

    def _latest_attempt_task_results(self, student_ids, work_ids=None):
        participations = EventParticipation.objects.filter(
            student_id__in=student_ids,
        ).only('pk')
        if work_ids is not None:
            participations = participations.filter(
                event__work_id__in=work_ids,
            )
        participation_ids = list(
            participations.values_list('pk', flat=True)
        )
        return latest_assessable_task_results(participation_ids)

    @staticmethod
    def _topic_sections(task_results):
        topic_ids = {
            result.task.topic_id
            for result in task_results
            if result.task.topic_id and not result.task.topic_section
        }
        return {
            str(topic.pk): topic.section
            for topic in Topic.objects.filter(pk__in=topic_ids)
        }

    @staticmethod
    def _topic_orders(task_results):
        topic_ids = {
            result.task.topic_id
            for result in task_results
            if result.task.topic_id
        }
        return {
            str(topic.pk): topic.order
            for topic in Topic.objects.filter(pk__in=topic_ids)
        }

    @staticmethod
    def _subtopic_orders(task_results):
        subtopic_ids = {
            result.task.subtopic_id
            for result in task_results
            if result.task.subtopic_id
        }
        return {
            str(subtopic.pk): subtopic.order
            for subtopic in SubTopic.objects.filter(pk__in=subtopic_ids)
        }

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

        task_results = [
            result
            for result in self._latest_attempt_task_results(
                [student.pk for student in students],
            )
            if result.task.subtopic_id == str(subtopic.pk)
        ]
        task_refs = {}
        for result in task_results:
            task_refs.setdefault(
                result.task.task_id,
                self._report_snapshot_task_ref(result.task),
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
            tasks=sorted(
                task_refs.values(),
                key=lambda task: (task.difficulty, task.text, task.pk),
            ),
            scores=[
                HeatmapDetailScoreFact(
                    student_id=result.student_id,
                    task_id=result.task.task_id,
                    subtopic_id=result.task.subtopic_id,
                    points=result.points,
                    max_points=result.max_points,
                    event=ReportActivityRef(
                        pk=result.event_id,
                        name=result.event_name,
                        planned_date=result.event_date,
                    ),
                )
                for result in task_results
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

        task_results = [
            result
            for result in self._latest_attempt_task_results([student.pk])
            if result.task.topic_id == str(topic.pk)
        ]
        task_refs = {}
        for result in task_results:
            task_refs.setdefault(
                result.task.task_id,
                self._report_snapshot_task_ref(result.task),
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
            tasks=sorted(
                task_refs.values(),
                key=lambda task: (task.difficulty, task.text, task.pk),
            ),
            scores=[
                HeatmapDetailScoreFact(
                    student_id=result.student_id,
                    task_id=result.task.task_id,
                    subtopic_id=result.task.subtopic_id,
                    points=result.points,
                    max_points=result.max_points,
                    event=ReportActivityRef(
                        pk=result.event_id,
                        name=result.event_name,
                        planned_date=result.event_date,
                    ),
                )
                for result in task_results
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

    @staticmethod
    def _report_snapshot_task_ref(task):
        return ReportTaskRef(
            pk=task.task_id,
            text=task.text,
            difficulty=task.difficulty,
            difficulty_display=(
                task.difficulty_display or str(task.difficulty)
            ),
        )

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

    @staticmethod
    def _report_work_ref(work):
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
