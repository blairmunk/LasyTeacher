"""Pure event screen calculations."""

from typing import List

from core_logic.entities.event import (
    EventDetailData,
    EventListData,
    EventParticipationRow,
    EventStatusStep,
    EventStatusTransition,
    EventVariantRef,
)


class EventService:
    STATUS_FLOW = [
        ('planned', 'Запланировано', 'secondary'),
        ('in_progress', 'Выполняется', 'primary'),
        ('completed', 'Завершено', 'info'),
        ('reviewing', 'На проверке', 'warning'),
        ('graded', 'Проверено', 'success'),
        ('closed', 'Закрыто', 'dark'),
    ]

    TRANSITIONS = {
        'planned': [
            EventStatusTransition('completed', 'Отметить как завершённое', 'info', 'fa-check'),
        ],
        'in_progress': [
            EventStatusTransition('completed', 'Завершить', 'info', 'fa-check'),
        ],
        'completed': [
            EventStatusTransition('reviewing', 'Начать проверку', 'warning', 'fa-clipboard-check'),
        ],
        'reviewing': [
            EventStatusTransition('graded', 'Завершить проверку', 'success', 'fa-check-circle'),
        ],
        'graded': [
            EventStatusTransition('closed', 'Закрыть событие', 'dark', 'fa-lock'),
        ],
        'closed': [
            EventStatusTransition('graded', 'Вернуть на проверку', 'warning', 'fa-undo'),
        ],
    }

    def build_list_data(self, events: List[object]) -> EventListData:
        return EventListData(
            events=events,
            planned_events=[
                event for event in events
                if event.status in ('planned', 'in_progress')
            ],
            active_events=[
                event for event in events
                if event.status in ('completed', 'reviewing')
            ],
            graded_events=[
                event for event in events
                if event.status == 'graded'
            ],
        )

    def build_detail_data(
        self,
        status: str,
        has_work: bool,
        participations: List[EventParticipationRow],
        available_variants: List[EventVariantRef],
    ) -> EventDetailData:
        active_participations = [
            participation
            for participation in participations
            if participation.status != 'absent'
        ]
        has_participants = len(active_participations) > 0
        some_variants_assigned = any(
            participation.variant is not None
            for participation in active_participations
        )
        all_variants_assigned = (
            has_participants
            and all(
                participation.variant is not None
                for participation in active_participations
            )
        )
        can_review = (
            has_participants
            and some_variants_assigned
            and status in ('completed', 'reviewing', 'graded')
        )

        return EventDetailData(
            participations=participations,
            some_variants_assigned=some_variants_assigned,
            all_variants_assigned=all_variants_assigned,
            can_review=can_review,
            status_color=self.status_color(status),
            status_steps=self.status_steps(status),
            available_variants=available_variants if has_work else [],
            status_transitions=self.TRANSITIONS.get(status, []),
        )

    def status_color(self, status: str) -> str:
        return {
            code: color
            for code, _, color in self.STATUS_FLOW
        }.get(status, 'secondary')

    def status_steps(self, status: str) -> List[EventStatusStep]:
        steps = []
        current_found = False
        for code, label, color in self.STATUS_FLOW:
            is_current = code == status
            if is_current:
                current_found = True
            passed = not current_found
            steps.append(
                EventStatusStep(
                    code=code,
                    label=label,
                    color=color if (passed or is_current) else 'light',
                    current=is_current,
                    passed=passed,
                )
            )
        return steps
