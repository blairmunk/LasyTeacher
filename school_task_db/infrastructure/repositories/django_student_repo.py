"""Django implementation of the student repository."""

from typing import List

from core_logic.entities.student import TaskResult
from core_logic.interfaces.student_repo import IStudentRepository
from events.models import EventParticipation, Mark
from task_groups.models import TaskGroup


class DjangoStudentRepository(IStudentRepository):
    def get_task_results_for_event(
        self,
        student_id: str,
        event_id: str,
    ) -> List[TaskResult]:
        participation = EventParticipation.objects.filter(
            student_id=student_id,
            event_id=event_id,
        ).first()
        if not participation:
            return []

        mark = Mark.objects.filter(participation=participation).first()
        if not mark or not mark.task_scores:
            return []

        results = []
        task_groups = {
            str(tg.task_id): tg
            for tg in TaskGroup.objects.filter(
                task_id__in=mark.task_scores.keys()
            ).select_related('group')
        }

        for task_id, score_data in mark.task_scores.items():
            if not isinstance(score_data, dict):
                continue

            task_group = task_groups.get(str(task_id))
            results.append(
                TaskResult(
                    task_id=str(task_id),
                    points=score_data.get('points'),
                    max_points=score_data.get('max_points'),
                    group_id=str(task_group.group_id) if task_group else None,
                    group_name=task_group.group.name if task_group else '',
                )
            )

        return results

