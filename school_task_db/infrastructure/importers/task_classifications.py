"""Resolve portable task classification references against codifiers."""

from codifier.models import ContentEntry, Requirement


class TaskClassificationImporter:
    def __init__(self, runtime):
        self.runtime = runtime

    def apply(self, task, task_data):
        self._apply_relation(
            task,
            task_data,
            field_name='codifier_content_entries',
            model=ContentEntry,
            relation=task.codifier_content_entries,
        )
        self._apply_relation(
            task,
            task_data,
            field_name='codifier_requirements',
            model=Requirement,
            relation=task.codifier_requirements,
        )

    def _apply_relation(
        self,
        task,
        task_data,
        *,
        field_name,
        model,
        relation,
    ):
        if field_name not in task_data:
            return
        resolved = []
        for reference in task_data[field_name]:
            item = self._resolve(model, reference)
            if item is None:
                reference_values = (
                    reference
                    if isinstance(reference, dict)
                    else {}
                )
                self.runtime.log_warning(
                    'Не найдена классификация задания '
                    f'{reference_values.get("subject", "?")} '
                    f'{reference_values.get("exam_type", "?")} '
                    f'{reference_values.get("year", "?")} '
                    f'{reference_values.get("code", "?")}',
                    context={
                        'task_id': str(task.pk),
                        'field': field_name,
                    },
                )
                continue
            resolved.append(item)
        relation.set(resolved)

    @staticmethod
    def _resolve(model, reference):
        if not isinstance(reference, dict):
            return None
        return model.objects.filter(
            codifier__subject=reference.get('subject', ''),
            codifier__exam_type=reference.get('exam_type', ''),
            codifier__year=reference.get('year'),
            code=reference.get('code', ''),
        ).first()
