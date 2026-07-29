import django.db.models.deletion
from django.db import migrations, models


def backfill_variant_tasks(apps, schema_editor):
    StudentTaskLog = apps.get_model('students', 'StudentTaskLog')
    VariantTask = apps.get_model('works', 'VariantTask')

    logs = list(
        StudentTaskLog.objects.filter(
            variant_task__isnull=True,
            variant__isnull=False,
        ).exclude(
            task__isnull=True,
        )
    )
    if not logs:
        return

    variant_ids = {log.variant_id for log in logs}
    task_ids = {log.task_id for log in logs}
    variant_task_ids = {
        (variant_task.variant_id, variant_task.task_id): variant_task.pk
        for variant_task in VariantTask.objects.filter(
            variant_id__in=variant_ids,
            task_id__in=task_ids,
        )
    }
    changed = []
    for log in logs:
        log.variant_task_id = variant_task_ids.get(
            (log.variant_id, log.task_id)
        )
        if log.variant_task_id:
            changed.append(log)
    if changed:
        StudentTaskLog.objects.bulk_update(changed, ['variant_task'])


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0003_studenttasklog'),
        ('works', '0013_varianttask_content_order_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='studenttasklog',
            name='variant_task',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='student_logs',
                to='works.varianttask',
                verbose_name='Строка задания варианта',
            ),
        ),
        migrations.RunPython(
            backfill_variant_tasks,
            migrations.RunPython.noop,
        ),
    ]
