"""Django implementation of the event repository."""

import datetime as dt
from typing import Dict, List, Optional

from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from core_logic.entities.event import (
    EventEntity,
    EventMarkRef,
    EventParticipationRef,
    EventParticipationRow,
    EventStudentRef,
    EventVariantAssignmentResult,
    EventVariantRef,
    EventWorkScanRef,
    MarkEntity,
    ParticipationMarkData,
    StudentSummary,
    VariantSummary,
)
from core_logic.interfaces.event_repo import (
    CreateEventParams,
    GradeParticipationParams,
    GradeParticipationResult,
    IEventRepository,
)
from core_logic.services.grading_service import GradingService
from events.models import Event, EventParticipation, Mark
from works.models import Variant


class DjangoEventRepository(IEventRepository):
    def __init__(self, grading_service=None):
        self.grading_service = grading_service or GradingService()

    def get_list_events(self):
        return list(
            Event.objects.select_related(
                'work',
                'course',
            ).annotate(
                participant_count=Count('eventparticipation'),
            ).order_by('-planned_date')
        )

    def get_detail_participations(self, event_id: str):
        participations = EventParticipation.objects.filter(
            event_id=event_id,
        ).select_related(
            'student',
            'variant',
        ).order_by('student__last_name', 'student__first_name')

        marks = {
            mark.participation_id: mark
            for mark in Mark.objects.filter(
                participation_id__in=[p.pk for p in participations]
            )
        }

        rows = []
        for participation in participations:
            mark = marks.get(participation.pk)
            rows.append(
                EventParticipationRow(
                    pk=str(participation.pk),
                    status=participation.status,
                    student=EventStudentRef(
                        pk=str(participation.student.pk),
                        last_name=participation.student.last_name,
                        first_name=participation.student.first_name,
                        middle_name=participation.student.middle_name,
                    ),
                    variant=(
                        EventVariantRef(
                            pk=str(participation.variant.pk),
                            number=participation.variant.number,
                        )
                        if participation.variant
                        else None
                    ),
                    mark_obj=self._event_mark_ref(mark) if mark else None,
                )
            )
        return rows

    def get_available_variants(self, event_id: str):
        event = Event.objects.select_related('work').filter(pk=event_id).first()
        if not event or not event.work_id:
            return []

        return [
            EventVariantRef(pk=str(variant.pk), number=variant.number)
            for variant in Variant.objects.filter(work=event.work).order_by('number')
        ]

    def get_event_status(self, event_id: str) -> Optional[str]:
        return Event.objects.filter(pk=event_id).values_list(
            'status',
            flat=True,
        ).first()

    def add_participants(self, event_id: str, student_ids: List[str]) -> int:
        created_count = 0
        with transaction.atomic():
            for student_id in student_ids:
                _, created = EventParticipation.objects.get_or_create(
                    event_id=event_id,
                    student_id=student_id,
                    defaults={'status': 'assigned'},
                )
                if created:
                    created_count += 1
        return created_count

    def assign_variants(
        self,
        event_id: str,
        assignments: Dict[str, str],
    ) -> int:
        assigned_count = 0
        with transaction.atomic():
            participations = EventParticipation.objects.filter(
                event_id=event_id,
                pk__in=assignments.keys(),
            )
            for participation in participations:
                variant_id = assignments.get(str(participation.pk))
                if not variant_id:
                    continue
                participation.variant_id = variant_id
                participation.save()
                assigned_count += 1
        return assigned_count

    def assign_variant(
        self,
        event_id: str,
        participation_id: str,
        variant_id: str,
    ) -> EventVariantAssignmentResult:
        participation = EventParticipation.objects.select_related(
            'student',
        ).get(pk=participation_id, event_id=event_id)
        variant = Variant.objects.get(pk=variant_id)

        participation.variant = variant
        participation.save()

        return EventVariantAssignmentResult(
            variant_number=variant.number,
            student_last_name=participation.student.last_name,
            student_first_name=participation.student.first_name,
        )

    def set_event_status(self, event_id: str, status: str) -> None:
        Event.objects.filter(pk=event_id).update(status=status)

    def get_by_id(self, event_id: str) -> Optional[EventEntity]:
        event = Event.objects.select_related('work', 'course').filter(
            pk=event_id
        ).first()
        if not event:
            return None

        return EventEntity(
            id=str(event.pk),
            name=event.name,
            work_id=str(event.work_id),
            work_name=event.work.name,
            status=event.status,
            status_display=event.get_status_display(),
            course_id=str(event.course_id) if event.course_id else None,
            course_name=event.course.name if event.course else '',
            planned_date=event.planned_date,
            location=event.location,
            description=event.description,
            short_uuid=event.get_short_uuid(),
            work_type=event.work.work_type,
            work_type_display=event.work.get_work_type_display(),
            work_variant_count=event.work.variant_set.count(),
        )

    def get_participation_ref(self, participation_id: str):
        participation = EventParticipation.objects.filter(
            pk=participation_id,
        ).first()
        if not participation:
            return None
        return EventParticipationRef(
            id=str(participation.pk),
            event_id=str(participation.event_id),
        )

    def get_student_mark(
        self,
        event_id: str,
        student_id: str,
    ) -> Optional[MarkEntity]:
        mark = Mark.objects.filter(
            participation__event_id=event_id,
            participation__student_id=student_id,
        ).first()
        if not mark:
            return None

        return MarkEntity(
            student_id=str(student_id),
            event_id=str(event_id),
            score=mark.score,
        )

    def get_participation_marks(self, event_id: str):
        participations = EventParticipation.objects.filter(
            event_id=event_id
        ).select_related('student', 'variant').order_by(
            'student__last_name',
            'student__first_name',
        )

        marks = {
            mark.participation_id: mark
            for mark in Mark.objects.filter(
                participation_id__in=[p.pk for p in participations]
            )
        }

        result = []
        for participation in participations:
            student = participation.student
            variant = participation.variant
            mark = marks.get(participation.pk)
            result.append(
                ParticipationMarkData(
                    student=StudentSummary(
                        id=str(student.pk),
                        full_name=student.get_full_name(),
                    ),
                    variant=(
                        VariantSummary(
                            id=str(variant.pk),
                            number=variant.number,
                        )
                        if variant
                        else None
                    ),
                    score=mark.score if mark else None,
                    points=mark.points if mark else None,
                    max_points=mark.max_points if mark else None,
                    task_scores=mark.task_scores if mark else {},
                )
            )
        return result

    def create_event(self, params: CreateEventParams) -> str:
        planned_date = self._parse_planned_date(params.date)
        event = Event.objects.create(
            name=params.name,
            work_id=params.work_id,
            planned_date=planned_date,
            status='planned',
            course_id=params.course_id,
            description=params.description,
        )
        return str(event.pk)

    def create_participation(
        self,
        event_id: str,
        student_id: str,
        variant_id: str,
    ) -> str:
        participation = EventParticipation.objects.create(
            event_id=event_id,
            student_id=student_id,
            variant_id=variant_id,
            status='assigned',
        )
        return str(participation.pk)

    def grade_participation(
        self,
        params: GradeParticipationParams,
    ) -> GradeParticipationResult:
        with transaction.atomic():
            participation = EventParticipation.objects.select_related(
                'student',
                'event',
            ).get(pk=params.participation_id)
            mark, _ = Mark.objects.get_or_create(participation=participation)

            mark.score = params.score
            mark.points = params.points
            mark.max_points = params.max_points
            mark.teacher_comment = params.teacher_comment
            mark.mistakes_analysis = params.mistakes_analysis
            mark.recommendations = params.recommendations
            mark.checked_at = timezone.now()
            mark.checked_by = params.checked_by
            mark.is_retake = params.is_retake
            mark.is_excellent = params.is_excellent
            mark.needs_attention = params.needs_attention
            if params.task_scores is not None:
                mark.task_scores = params.task_scores
            if params.work_scan is not None:
                if mark.work_scan:
                    mark.work_scan.delete(save=False)
                mark.work_scan = params.work_scan
            mark.save()

            participation.status = 'graded'
            participation.graded_at = timezone.now()
            participation.save()

            event = participation.event
            if params.sync_event_status:
                active_count = event.eventparticipation_set.exclude(
                    status='absent',
                ).count()
                graded_count = event.eventparticipation_set.exclude(
                    status='absent',
                ).filter(status='graded').count()
                event.status = self.grading_service.next_event_status(
                    current_status=event.status,
                    active_participants=active_count,
                    graded_participants=graded_count,
                )
                event.save()

            student = participation.student
            return GradeParticipationResult(
                mark_id=str(mark.pk),
                participation_id=str(participation.pk),
                event_id=str(event.pk),
                student_name=f'{student.last_name} {student.first_name}',
                score=mark.score,
                event_status=event.status,
            )

    def _event_mark_ref(self, mark: Mark) -> EventMarkRef:
        work_scan = None
        if mark.work_scan:
            work_scan = EventWorkScanRef(url=mark.work_scan.url)
        return EventMarkRef(score=mark.score, work_scan=work_scan)

    @staticmethod
    def _parse_planned_date(date_value: Optional[str]):
        if date_value:
            try:
                date_obj = dt.datetime.strptime(date_value, '%Y-%m-%d').date()
            except ValueError:
                date_obj = timezone.now().date()
        else:
            date_obj = timezone.now().date()

        return timezone.make_aware(
            dt.datetime.combine(date_obj, dt.time(9, 0))
        )
