"""Invalidate task formula diagnostics after ORM writes."""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from infrastructure.services.task_math_status_cache import (
    task_math_status_cache,
)
from tasks.models import Task


@receiver(post_save, sender=Task)
def invalidate_task_math_cache_on_save(sender, instance, **kwargs):
    task_math_status_cache.invalidate_task_cache(instance.id)
    update_fields = kwargs.get('update_fields')
    text_may_have_changed = update_fields is None or 'text' in update_fields
    if kwargs.get('created') or text_may_have_changed:
        task_math_status_cache.invalidate_all_cache()


@receiver(post_delete, sender=Task)
def invalidate_task_math_cache_on_delete(sender, instance, **kwargs):
    task_math_status_cache.invalidate_task_cache(instance.id)
    task_math_status_cache.invalidate_all_cache()
