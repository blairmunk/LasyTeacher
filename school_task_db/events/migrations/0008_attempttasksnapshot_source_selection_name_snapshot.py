from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('events', '0007_attemptsnapshot_work_assessment_mode_snapshot'),
    ]

    operations = [
        migrations.AddField(
            model_name='attempttasksnapshot',
            name='source_selection_name_snapshot',
            field=models.CharField(
                blank=True,
                default='',
                max_length=200,
                verbose_name='Название блока спецификации (снимок)',
            ),
        ),
    ]
