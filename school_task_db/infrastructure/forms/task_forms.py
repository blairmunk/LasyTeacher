"""Infrastructure helpers for Django task forms."""

from dataclasses import dataclass
from typing import Any

from tasks.forms import TaskForm, TaskImageFormSet
from tasks.models import Task


@dataclass(frozen=True)
class TaskImageFormSaveResult:
    task: Any
    created_images: int = 0
    deleted_images: int = 0


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

    def save_created_images(self, image_formset, task_id):
        task = self._get_task_instance(task_id)
        image_formset.instance = task
        image_formset.save()
        created_images = len([
            image_form.instance
            for image_form in image_formset.forms
            if (
                image_form.instance.pk
                and not image_form.cleaned_data.get('DELETE', False)
            )
        ])
        return TaskImageFormSaveResult(
            task=task,
            created_images=created_images,
        )

    def save_updated_images(self, image_formset, task_id):
        task = self._get_task_instance(task_id)
        image_formset.instance = task
        saved_images = image_formset.save()
        return TaskImageFormSaveResult(
            task=task,
            created_images=len([image for image in saved_images if image.pk]),
            deleted_images=len(image_formset.deleted_objects),
        )
