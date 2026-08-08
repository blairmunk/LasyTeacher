"""Django read adapter for student performance reports."""

from collections import defaultdict

from core_logic.entities.report_summary import (
    StudentPerformanceItemSource,
    StudentPerformanceParticipationFact,
    StudentPerformanceSource,
)
from core_logic.entities.report_refs import ReportMarkFact
from core_logic.interfaces.student_performance_repo import (
    IStudentPerformanceRepository,
)
from infrastructure.repositories.django_report_summary_support import (
    event_scope,
    report_course_ref,
    report_group_ref,
    report_student_ref,
    student_scope,
)
from infrastructure.services.attempt_snapshot_queries import (
    latest_attempts_by_participation,
)


class DjangoStudentPerformanceRepository(IStudentPerformanceRepository):
    def get_student_performance_source(self, year, group_id):
        _, participations, courses = event_scope(year)
        groups, students = student_scope(year)
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
                    student=report_student_ref(student),
                    participations=participations_by_student[student.pk],
                    marks=marks_by_student[student.pk],
                )
                for student in students
                if participations_by_student[student.pk]
            ],
            groups=[report_group_ref(group) for group in groups],
            selected_group=(
                report_group_ref(selected_group)
                if selected_group
                else None
            ),
            courses=[
                report_course_ref(course)
                for course in courses.order_by('grade_level', 'name')
            ],
        )
