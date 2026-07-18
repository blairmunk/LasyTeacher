"""Infrastructure helpers for Django task forms."""

from tasks.forms import TaskForm, TaskImageFormSet
from tasks.models import Task


class TaskFormAdapter:
    def _get_task_instance(self, task_id=None):
        if not task_id:
            return None
        return Task.objects.filter(pk=task_id).first()

    def build_task_form(self, data=None, task_id=None):
        instance = self._get_task_instance(task_id)
        if data is not None:
            return TaskForm(data, instance=instance)
        return TaskForm(instance=instance)

    def build_image_formset(self, data=None, files=None, instance=None):
        kwargs = {'prefix': 'images'}
        if instance is not None:
            kwargs['instance'] = instance
        if data is not None:
            return TaskImageFormSet(data, files, **kwargs)
        return TaskImageFormSet(**kwargs)

    def build_image_formset_for_task(self, data=None, files=None, task_id=None):
        return self.build_image_formset(
            data=data,
            files=files,
            instance=self._get_task_instance(task_id),
        )
