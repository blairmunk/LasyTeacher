"""Infrastructure helpers for Django task forms."""

from dataclasses import dataclass
from typing import Any

from tasks.forms import TaskImageFormSet


@dataclass(frozen=True)
class TaskImageFormSaveResult:
    task: Any
    created_images: int = 0
    deleted_images: int = 0


class TaskFormAdapter:
    def build_image_formset(self, data=None, files=None, instance=None):
        kwargs = {'prefix': 'images'}
        if instance is not None:
            kwargs['instance'] = instance
        if data is not None:
            return TaskImageFormSet(data, files, **kwargs)
        return TaskImageFormSet(**kwargs)

    def save_created_task_with_images(self, form, image_formset):
        task = form.save()
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

    def save_updated_task_with_images(self, form, image_formset):
        task = form.save()
        saved_images = image_formset.save()
        return TaskImageFormSaveResult(
            task=task,
            created_images=len([image for image in saved_images if image.pk]),
            deleted_images=len(image_formset.deleted_objects),
        )
