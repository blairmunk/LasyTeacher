from django.db import migrations


def shift_difficulty_up(apps, schema_editor):
    """Сдвигаем: 5→6, 4→5, 3→4. Порядок важен — сверху вниз!"""
    Task = apps.get_model('tasks', 'Task')
    Task.objects.filter(difficulty=5).update(difficulty=6)
    Task.objects.filter(difficulty=4).update(difficulty=5)
    Task.objects.filter(difficulty=3).update(difficulty=4)


def shift_difficulty_down(apps, schema_editor):
    """Откат: 4→3, 5→4, 6→5"""
    Task = apps.get_model('tasks', 'Task')
    Task.objects.filter(difficulty=4).update(difficulty=3)
    Task.objects.filter(difficulty=5).update(difficulty=4)
    Task.objects.filter(difficulty=6).update(difficulty=5)


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0003_source_task_grade_task_is_verified_and_more'),  # замени на реальную последнюю миграцию
    ]

    operations = [
        migrations.RunPython(shift_difficulty_up, shift_difficulty_down),
    ]
