"""Shared Django queries for student learning repositories."""

from core_logic.entities.student import StudentDetail
from events.models import EventParticipation
from infrastructure.services.django_captured_task_result_queries import (
    latest_assessable_task_results,
)
from task_groups.models import TaskGroup


def student_detail(student) -> StudentDetail:
    return StudentDetail(
        pk=str(student.pk),
        first_name=student.first_name,
        last_name=student.last_name,
        middle_name=student.middle_name,
        email=student.email,
        short_uuid=student.get_short_uuid(),
        full_name=student.get_full_name(),
        short_name=student.get_short_name(),
    )


def latest_task_history(student_ids):
    participation_ids = EventParticipation.objects.filter(
        student_id__in=student_ids,
    ).values_list('pk', flat=True)
    return latest_assessable_task_results(participation_ids)


def first_analog_groups(task_ids):
    groups = {}
    for membership in TaskGroup.objects.filter(
        task_id__in=set(task_ids),
    ).select_related('group').order_by('pk'):
        groups.setdefault(str(membership.task_id), membership.group)
    return groups


def result_percentage(result):
    if not result.max_points or result.max_points <= 0:
        return None
    return round(result.points / result.max_points * 100, 1)


def result_is_correct(result):
    percentage = result_percentage(result)
    return percentage >= 70 if percentage is not None else None
