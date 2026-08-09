"""Django read model for printable student grade digests."""

from core_logic.entities.student_digest import (
    StudentDigestEntryFact,
    StudentDigestGroupRef,
    StudentDigestSource,
    StudentDigestStudentRef,
    StudentDigestStudentSource,
    StudentDigestTaskResultFact,
)
from core_logic.interfaces.student_digest_repo import IStudentDigestRepository
from core_logic.value_objects.attempt_status import (
    resolve_historical_participation_status,
)
from events.models import EventParticipation
from infrastructure.services.django_attempt_snapshot_queries import (
    latest_attempts_by_participation,
)
from infrastructure.services.django_captured_task_result_queries import (
    captured_task_result_snapshot,
)
from students.models import StudentGroup


class DjangoStudentDigestRepository(IStudentDigestRepository):
    def get_digest_groups(self, year):
        groups = StudentGroup.objects.all().order_by('name')
        if year:
            groups = groups.filter(academic_year_id=year.pk)
        return tuple(
            StudentDigestGroupRef(pk=str(group.pk), name=group.name)
            for group in groups
        )

    def get_student_digest_source(self, group_id, start_date, end_date):
        group = StudentGroup.objects.filter(pk=group_id).first()
        if group is None:
            return None
        students = list(
            group.students.all().order_by('last_name', 'first_name')
        )
        student_ids = [student.pk for student in students]
        all_participations = list(
            EventParticipation.objects.filter(
                student_id__in=student_ids,
                event__planned_date__date__gte=start_date,
                event__planned_date__date__lte=end_date,
            ).select_related(
                'student',
                'event',
                'event__work',
                'event__course',
            ).order_by('event__planned_date')
        )
        attempts = latest_attempts_by_participation(
            participation.pk for participation in all_participations
        )
        participations = [
            participation
            for participation in all_participations
            if participation.status == 'absent'
            or (
                participation.pk in attempts
                and attempts[participation.pk].score is not None
            )
        ]
        entries_by_student = {student.pk: [] for student in students}
        for participation in participations:
            entries_by_student[participation.student_id].append(
                self._entry(
                    participation,
                    attempts.get(participation.pk),
                )
            )
        return StudentDigestSource(
            group=StudentDigestGroupRef(pk=str(group.pk), name=group.name),
            students=tuple(
                StudentDigestStudentSource(
                    student=StudentDigestStudentRef(
                        pk=str(student.pk),
                        full_name=student.get_full_name(),
                    ),
                    entries=tuple(entries_by_student[student.pk]),
                )
                for student in students
            ),
        )

    def _entry(self, participation, attempt):
        task_results = (
            attempt.captured_task_results if attempt is not None else ()
        )
        task_result_facts = []
        if attempt:
            for task_result in task_results:
                captured = captured_task_result_snapshot(task_result)
                if captured is None:
                    continue
                task_result_facts.append(
                    StudentDigestTaskResultFact(
                        topic_name=captured.task.topic_name,
                        subtopic_name=captured.task.subtopic_name,
                        subject=captured.task.subject,
                        points=self._number(captured.points),
                        max_points=self._number(captured.max_points),
                        comment=captured.comment,
                        is_assessable=captured.is_assessable,
                    )
                )

        event = participation.event
        subject = next(
            (
                result.subject
                for result in task_result_facts
                if result.subject
            ),
            '',
        )
        if not subject and event.course_id:
            subject = event.course.subject
        return StudentDigestEntryFact(
            event_id=str(event.pk),
            event_name=(
                attempt.event_name_snapshot if attempt else event.name
            ),
            work_name=(
                attempt.work_name_snapshot if attempt else event.work.name
            ),
            subject=subject,
            planned_date=(
                attempt.event_date_snapshot.date()
                if attempt
                else event.planned_date.date()
            ),
            status=resolve_historical_participation_status(
                participation.status,
                has_attempt=attempt is not None,
            ),
            score=attempt.score if attempt else None,
            points=self._number(attempt.points) if attempt else None,
            max_points=self._number(attempt.max_points) if attempt else None,
            teacher_comment=attempt.teacher_comment if attempt else '',
            mistakes_analysis=attempt.mistakes_analysis if attempt else '',
            recommendations=attempt.recommendations if attempt else '',
            needs_attention=attempt.needs_attention if attempt else False,
            task_results=tuple(task_result_facts),
        )

    @staticmethod
    def _number(value):
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None
