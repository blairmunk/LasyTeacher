from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('codifier', '0002_contententry_subtopic_alter_contententry_topic'),
        ('tasks', '0005_alter_task_difficulty'),
    ]

    operations = [
        migrations.AddField(
            model_name='contententry',
            name='tasks',
            field=models.ManyToManyField(
                blank=True,
                related_name='codifier_content_entries',
                to='tasks.task',
                verbose_name='Задания',
            ),
        ),
    ]
