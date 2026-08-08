"""Map Django review models to core read references."""

from core_logic.entities.review import (
    ReviewCourseRef,
    ReviewEventRef,
    ReviewMarkRef,
    ReviewParticipationRef,
    ReviewSessionRef,
    ReviewStudentRef,
    ReviewVariantRef,
    ReviewWorkRef,
    ReviewWorkScanRef,
)


def review_event_ref(event) -> ReviewEventRef:
    return ReviewEventRef(
        pk=str(event.pk),
        name=event.name,
        planned_date=event.planned_date,
        status=event.status,
        work=(
            ReviewWorkRef(
                pk=str(event.work.pk),
                name=event.work.name,
                work_type=event.work.work_type,
                work_type_display=event.work.get_work_type_display(),
            )
            if event.work_id
            else None
        ),
        course=(
            ReviewCourseRef(
                pk=str(event.course.pk),
                name=event.course.name,
            )
            if event.course_id
            else None
        ),
    )


def review_student_ref(student) -> ReviewStudentRef:
    return ReviewStudentRef(
        pk=str(student.pk),
        last_name=student.last_name,
        first_name=student.first_name,
        middle_name=student.middle_name,
    )


def review_variant_ref(variant, task_counts=None) -> ReviewVariantRef:
    task_counts = task_counts or {}
    return ReviewVariantRef(
        pk=str(variant.pk),
        number=variant.number,
        tasks_count=task_counts.get(variant.pk, 0),
    )


def review_participation_ref(
    participation,
    task_counts=None,
) -> ReviewParticipationRef:
    variant = participation.variant
    return ReviewParticipationRef(
        pk=str(participation.pk),
        student=review_student_ref(participation.student),
        event=review_event_ref(participation.event),
        variant=(
            review_variant_ref(variant, task_counts=task_counts)
            if variant
            else None
        ),
    )


def review_mark_ref(mark) -> ReviewMarkRef:
    work_scan = None
    if mark.work_scan:
        work_scan = ReviewWorkScanRef(
            name=mark.work_scan.name,
            url=mark.work_scan.url,
        )
    return ReviewMarkRef(
        pk=str(mark.pk),
        score=mark.score,
        points=mark.points,
        max_points=mark.max_points,
        teacher_comment=mark.teacher_comment,
        mistakes_analysis=mark.mistakes_analysis,
        recommendations=mark.recommendations,
        work_scan=work_scan,
        task_scores=mark.task_scores or {},
    )


def review_session_ref(session) -> ReviewSessionRef:
    return ReviewSessionRef(
        pk=str(session.pk),
        event=review_event_ref(session.event),
        total_participations=session.total_participations,
        checked_participations=session.checked_participations,
        started_at=session.started_at,
        finished_at=session.finished_at,
    )

