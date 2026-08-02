"""Django read model for printable student grade digests."""

from django.db.models import Q

from core_logic.entities.student_digest import (
    StudentDigestEntryFact,
    StudentDigestGroupRef,
    StudentDigestSource,
    StudentDigestStudentRef,
    StudentDigestStudentSource,
)
from core_logic.interfaces.student_digest_repo import IStudentDigestRepository
from core_logic.value_objects.task_scores import resolve_task_score_record
from events.models import EventParticipation
from students.models import StudentGroup
from works.models import VariantTask


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
        participations = list(
            EventParticipation.objects.filter(
                student_id__in=student_ids,
                event__planned_date__date__gte=start_date,
                event__planned_date__date__lte=end_date,
            ).filter(
                # Keep assessed work and explicit absences only.
                Q(status='absent') | Q(mark__score__isnull=False)
            ).select_related(
                'student',
                'event',
                'event__work',
                'event__course',
                'variant',
                'mark',
            ).order_by('event__planned_date')
        )
        variant_tasks = self._variant_tasks_by_variant(participations)
        entries_by_student = {student.pk: [] for student in students}
        for participation in participations:
            entries_by_student[participation.student_id].append(
                self._entry(participation, variant_tasks)
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

    def _entry(self, participation, variant_tasks):
        mark = getattr(participation, 'mark', None)
        tasks = variant_tasks.get(participation.variant_id, [])
        failed_topics = []
        task_comments = []
        if mark:
            for variant_task in tasks:
                if not variant_task.is_assessable:
                    continue
                record = resolve_task_score_record(
                    mark.task_scores,
                    variant_task_id=str(variant_task.pk),
                    task_id=str(variant_task.task_id),
                )
                if record is None:
                    continue
                points = self._number(record.points)
                max_points = self._number(record.max_points)
                if points is None or not max_points or points >= max_points:
                    continue
                topic_label = variant_task.task.topic.name
                if variant_task.task.subtopic_id:
                    topic_label += f': {variant_task.task.subtopic.name}'
                failed_topics.append(topic_label)
                if record.comment:
                    task_comments.append(record.comment.strip())

        event = participation.event
        subject = event.course.subject if event.course_id else ''
        if not subject and tasks:
            subject = tasks[0].task.topic.subject
        return StudentDigestEntryFact(
            event_id=str(event.pk),
            event_name=event.name,
            work_name=event.work.name,
            subject=subject,
            planned_date=event.planned_date.date(),
            status=participation.status,
            score=mark.score if mark else None,
            points=self._number(mark.points) if mark else None,
            max_points=self._number(mark.max_points) if mark else None,
            teacher_comment=mark.teacher_comment if mark else '',
            mistakes_analysis=mark.mistakes_analysis if mark else '',
            recommendations=mark.recommendations if mark else '',
            needs_attention=mark.needs_attention if mark else False,
            failed_topics=tuple(dict.fromkeys(failed_topics)),
            task_comments=tuple(dict.fromkeys(task_comments)),
        )

    @staticmethod
    def _variant_tasks_by_variant(participations):
        variant_ids = {
            item.variant_id for item in participations if item.variant_id
        }
        result = {variant_id: [] for variant_id in variant_ids}
        for variant_task in VariantTask.objects.filter(
            variant_id__in=variant_ids,
        ).select_related('task', 'task__topic', 'task__subtopic'):
            result[variant_task.variant_id].append(variant_task)
        return result

    @staticmethod
    def _number(value):
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None
