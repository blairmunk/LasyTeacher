"""Django implementation of the review repository."""

from typing import List

from django.db.models import Count, Q

from core_logic.entities.review import (
    EventReviewParticipationRow,
    ReviewCommentRef,
    ReviewCourseRef,
    ReviewEventRef,
    ReviewEventProgress,
    ReviewMarkRef,
    ReviewParticipationRef,
    ReviewParticipationStatusChange,
    ReviewSaveNavigation,
    ReviewSessionRef,
    ReviewStudentRef,
    ReviewTaskRef,
    ReviewTopicRef,
    ReviewVariantRef,
    ReviewVariantTaskRef,
    ReviewWorkRef,
    ReviewWorkScanRef,
)
from core_logic.interfaces.review_repo import IReviewRepository
from events.models import Event, EventParticipation, Mark
from review.models import ReviewComment, ReviewSession
from works.models import Variant, VariantTask


class DjangoReviewRepository(IReviewRepository):
    def get_dashboard_events(self) -> List[ReviewEventProgress]:
        events = Event.objects.annotate(
            total_participants=Count('eventparticipation'),
            graded_participants=Count(
                'eventparticipation',
                filter=Q(eventparticipation__status='graded'),
            ),
            absent_participants=Count(
                'eventparticipation',
                filter=Q(eventparticipation__status='absent'),
            ),
        ).filter(
            total_participants__gt=0,
        ).select_related(
            'work',
            'course',
        ).order_by('-planned_date')

        result = []
        for event in events:
            active = event.total_participants - event.absent_participants
            progress = (
                round(event.graded_participants / active * 100, 1)
                if active > 0
                else 100.0
            )
            result.append(
                ReviewEventProgress(
                    event=self._event_ref(event),
                    total_participants=event.total_participants,
                    graded_participants=event.graded_participants,
                    absent_participants=event.absent_participants,
                    active_participants=active,
                    progress_percentage=progress,
                    remaining=active - event.graded_participants,
                )
            )
        return result

    def get_event_review_participations(
        self,
        event_id: str,
    ) -> List[EventReviewParticipationRow]:
        participations = EventParticipation.objects.filter(
            event_id=event_id,
        ).select_related(
            'student',
            'variant',
            'event',
        ).order_by('student__last_name', 'student__first_name')

        marks = {
            mark.participation_id: mark
            for mark in Mark.objects.filter(
                participation_id__in=[p.pk for p in participations]
            )
        }
        task_counts = self._variant_task_counts(
            [p.variant_id for p in participations if p.variant_id]
        )

        result = []
        for participation in participations:
            mark = marks.get(participation.pk)
            mark_ref = self._mark_ref(mark) if mark else None
            result.append(
                EventReviewParticipationRow(
                    participation=self._participation_ref(
                        participation,
                        task_counts=task_counts,
                    ),
                    mark=mark_ref,
                    has_mark=mark is not None and mark.score is not None,
                    is_absent=participation.status == 'absent',
                    student=self._student_ref(participation.student),
                    variant=(
                        self._variant_ref(
                            participation.variant,
                            task_counts=task_counts,
                        )
                        if participation.variant
                        else None
                    ),
                )
            )
        return result

    def get_available_variants(self, event_id: str) -> List[ReviewVariantRef]:
        event = Event.objects.select_related('work').filter(pk=event_id).first()
        if not event or not event.work_id:
            return []

        variants = Variant.objects.filter(work=event.work).order_by('number')
        task_counts = self._variant_task_counts([variant.pk for variant in variants])
        return [
            self._variant_ref(variant, task_counts=task_counts)
            for variant in variants
        ]

    def get_participation(self, participation_id: str) -> ReviewParticipationRef:
        participation = EventParticipation.objects.select_related(
            'student',
            'variant',
            'event',
            'event__work',
        ).get(pk=participation_id)
        return self._participation_ref(participation)

    def get_variant_tasks(self, participation_id: str) -> List[ReviewVariantTaskRef]:
        participation = EventParticipation.objects.select_related(
            'variant',
        ).get(pk=participation_id)
        if not participation.variant:
            return []

        variant_tasks = VariantTask.objects.filter(
            variant=participation.variant,
            is_assessable=True,
        ).select_related(
            'task',
            'task__topic',
        ).order_by('order')

        return [
            ReviewVariantTaskRef(
                task=ReviewTaskRef(
                    id=str(variant_task.task.pk),
                    text=variant_task.task.text,
                    answer=variant_task.task.answer,
                    short_solution=variant_task.task.short_solution,
                    difficulty=variant_task.task.difficulty,
                    topic=(
                        ReviewTopicRef(
                            pk=str(variant_task.task.topic.pk),
                            name=variant_task.task.topic.name,
                        )
                        if variant_task.task.topic
                        else None
                    ),
                ),
                weight=variant_task.max_points or variant_task.weight,
            )
            for variant_task in variant_tasks
        ]

    def get_or_create_mark(
        self,
        participation_id: str,
        default_max_points: int,
    ) -> ReviewMarkRef:
        mark, _ = Mark.objects.get_or_create(
            participation_id=participation_id,
            defaults={'max_points': default_max_points},
        )
        return self._mark_ref(mark)

    def get_review_participations(self, event_id: str) -> List[ReviewParticipationRef]:
        participations = EventParticipation.objects.filter(
            event_id=event_id,
        ).exclude(
            status='absent',
        ).select_related(
            'student',
            'variant',
            'event',
        ).order_by(
            'student__last_name',
            'student__first_name',
        )
        task_counts = self._variant_task_counts(
            [p.variant_id for p in participations if p.variant_id]
        )
        return [
            self._participation_ref(participation, task_counts=task_counts)
            for participation in participations
        ]

    def get_typical_comments(self, limit: int = 10) -> List[ReviewCommentRef]:
        return [
            ReviewCommentRef(text=comment.text)
            for comment in ReviewComment.objects.filter(
                is_active=True,
            ).order_by('-usage_count')[:limit]
        ]

    def finalize_event(self, event_id: str) -> ReviewEventRef:
        event = Event.objects.select_related('work', 'course').get(pk=event_id)
        event.status = 'graded'
        event.save()
        return self._event_ref(event)

    def toggle_absent(self, participation_id: str) -> ReviewParticipationStatusChange:
        participation = EventParticipation.objects.select_related(
            'student',
            'event',
        ).get(pk=participation_id)

        if participation.status == 'absent':
            participation.status = 'assigned'
            is_absent = False
        else:
            participation.status = 'absent'
            is_absent = True
        participation.save()

        return ReviewParticipationStatusChange(
            participation_id=str(participation.pk),
            event_id=str(participation.event.pk),
            student_last_name=participation.student.last_name,
            status=participation.status,
            is_absent=is_absent,
        )

    def get_save_navigation(self, participation_id: str) -> ReviewSaveNavigation:
        participation = EventParticipation.objects.select_related('event').get(
            pk=participation_id,
        )
        participations = list(
            EventParticipation.objects.filter(
                event=participation.event,
            ).exclude(
                status='absent',
            ).select_related(
                'student',
                'event',
                'variant',
            ).order_by('student__last_name', 'student__first_name')
        )

        current_index = self._participation_index(
            participations=participations,
            participation_id=participation_id,
        )
        next_participation = self._next_ungraded_participation(
            participations=participations,
            current_index=current_index,
        )
        if next_participation is None and current_index + 1 < len(participations):
            next_participation = participations[current_index + 1]

        return ReviewSaveNavigation(
            event_id=str(participation.event.pk),
            next_participation=(
                self._participation_ref(next_participation)
                if next_participation
                else None
            ),
            all_checked=next_participation is None,
        )

    def get_recent_sessions(
        self,
        reviewer_id: str,
        limit: int = 5,
    ) -> List[ReviewSessionRef]:
        sessions = ReviewSession.objects.filter(
            reviewer_id=reviewer_id,
        ).select_related(
            'event',
            'event__work',
            'event__course',
        ).order_by('-started_at')[:limit]
        return [self._session_ref(session) for session in sessions]

    def sync_review_session(
        self,
        reviewer_id: str,
        event_id: str,
        total_participations: int,
        checked_participations: int,
    ) -> ReviewSessionRef:
        session, _ = ReviewSession.objects.select_related(
            'event',
            'event__work',
            'event__course',
        ).get_or_create(
            reviewer_id=reviewer_id,
            event_id=event_id,
            defaults={
                'total_participations': total_participations,
                'checked_participations': checked_participations,
            },
        )
        session.total_participations = total_participations
        session.checked_participations = checked_participations
        session.save()
        return self._session_ref(session)

    def _participation_ref(self, participation, task_counts=None) -> ReviewParticipationRef:
        student = participation.student
        event = participation.event
        variant = participation.variant
        return ReviewParticipationRef(
            pk=str(participation.pk),
            student=self._student_ref(student),
            event=self._event_ref(event),
            variant=(
                self._variant_ref(variant, task_counts=task_counts)
                if variant
                else None
            ),
        )

    def _event_ref(self, event) -> ReviewEventRef:
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

    def _student_ref(self, student) -> ReviewStudentRef:
        return ReviewStudentRef(
            pk=str(student.pk),
            last_name=student.last_name,
            first_name=student.first_name,
            middle_name=student.middle_name,
        )

    def _variant_ref(self, variant, task_counts=None) -> ReviewVariantRef:
        task_counts = task_counts or {}
        return ReviewVariantRef(
            pk=str(variant.pk),
            number=variant.number,
            tasks_count=task_counts.get(variant.pk, 0),
        )

    def _mark_ref(self, mark: Mark) -> ReviewMarkRef:
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
            work_scan=work_scan,
            task_scores=mark.task_scores or {},
        )

    def _session_ref(self, session: ReviewSession) -> ReviewSessionRef:
        return ReviewSessionRef(
            pk=str(session.pk),
            event=self._event_ref(session.event),
            total_participations=session.total_participations,
            checked_participations=session.checked_participations,
            started_at=session.started_at,
            finished_at=session.finished_at,
        )

    def _variant_task_counts(self, variant_ids) -> dict:
        variant_ids = [variant_id for variant_id in variant_ids if variant_id]
        if not variant_ids:
            return {}

        rows = VariantTask.objects.filter(
            variant_id__in=variant_ids,
        ).values('variant_id').annotate(total=Count('id'))
        return {row['variant_id']: row['total'] for row in rows}

    @staticmethod
    def _participation_index(participations, participation_id: str) -> int:
        try:
            return next(
                index
                for index, participation in enumerate(participations)
                if str(participation.pk) == str(participation_id)
            )
        except StopIteration:
            return -1

    @staticmethod
    def _next_ungraded_participation(participations, current_index: int):
        if current_index < 0:
            start_index = 0
        else:
            start_index = current_index + 1

        participation_ids = [
            participation.pk
            for participation in participations[start_index:]
        ]
        graded_ids = set(
            Mark.objects.filter(
                participation_id__in=participation_ids,
                score__isnull=False,
            ).values_list('participation_id', flat=True)
        )
        for participation in participations[start_index:]:
            if participation.pk not in graded_ids:
                return participation
        return None
