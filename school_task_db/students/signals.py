import logging

from django.db.models.signals import post_save
from django.dispatch import receiver


logger = logging.getLogger(__name__)


@receiver(post_save, sender='events.Mark')
def update_student_task_log_on_mark_save(sender, instance, **kwargs):
    """При сохранении Mark → обновляем StudentTaskLog"""
    from .models import StudentTaskLog

    if instance.task_scores:
        try:
            count = StudentTaskLog.update_from_mark(instance)
            if count > 0:
                logger.info(
                    'StudentTaskLog: +%s records from Mark #%s',
                    count,
                    str(instance.pk)[-8:],
                )
        except Exception as e:
            logger.exception('StudentTaskLog update failed: %s', e)
