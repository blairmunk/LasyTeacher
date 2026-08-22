import django.db.models.deletion
from django.db import migrations, models


def remove_unusable_task_image_rows(apps, schema_editor):
    TaskImage = apps.get_model('tasks', 'TaskImage')
    TaskImage.objects.filter(asset__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0007_imageasset_remove_taskimage_image_taskimage_asset'),
    ]

    operations = [
        migrations.RunPython(
            remove_unusable_task_image_rows,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name='taskimage',
            name='asset',
            field=models.ForeignKey(
                help_text=(
                    'Неизменяемый файл, на который ссылается задание'
                ),
                on_delete=django.db.models.deletion.PROTECT,
                related_name='task_references',
                to='tasks.imageasset',
                verbose_name='Файл изображения',
            ),
        ),
    ]
