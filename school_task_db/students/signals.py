from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='events.Mark')
def update_student_task_log_on_mark_save(sender, instance, **kwargs):
    """При сохранении Mark → обновляем StudentTaskLog"""
    from .models import StudentTaskLog

    if instance.task_scores:
        try:
            count = StudentTaskLog.update_from_mark(instance)
            if count > 0:
                print(f"📝 StudentTaskLog: +{count} записей из Mark #{str(instance.pk)[-8:]}")
        except Exception as e:
            print(f"⚠️ StudentTaskLog error: {e}")
