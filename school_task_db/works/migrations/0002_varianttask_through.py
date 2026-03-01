from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('works', '0001_initial'),
        ('tasks', '0001_initial'),
    ]

    operations = [
        # 1. Добавить order в WorkAnalogGroup
        migrations.AddField(
            model_name='workanaloggroup',
            name='order',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Порядок следования задания в работе',
                verbose_name='Порядок в работе',
            ),
        ),

        # 2. Обновить Meta WorkAnalogGroup
        migrations.AlterModelOptions(
            name='workanaloggroup',
            options={
                'ordering': ['order', 'pk'],
                'verbose_name': 'Группа заданий в работе',
                'verbose_name_plural': 'Группы заданий в работе',
            },
        ),

        # 3. Создать модель VariantTask
        migrations.CreateModel(
            name='VariantTask',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4, editable=False,
                    primary_key=True, serialize=False,
                )),
                ('created_at', models.DateTimeField(
                    auto_now_add=True, verbose_name='Дата создания',
                )),
                ('updated_at', models.DateTimeField(
                    auto_now=True, verbose_name='Дата обновления',
                )),
                ('order', models.PositiveIntegerField(
                    default=0, verbose_name='№ задания в варианте',
                )),
                ('task', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='tasks.task', verbose_name='Задание',
                )),
                ('variant', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    to='works.variant', verbose_name='Вариант',
                )),
            ],
            options={
                'verbose_name': 'Задание в варианте',
                'verbose_name_plural': 'Задания в варианте',
                'ordering': ['order'],
                'unique_together': {('variant', 'task')},
            },
        ),

        # 4. Удалить старую M2M (без through)
        migrations.RemoveField(
            model_name='variant',
            name='tasks',
        ),

        # 5. Добавить новую M2M с through
        migrations.AddField(
            model_name='variant',
            name='tasks',
            field=models.ManyToManyField(
                through='works.VariantTask',
                to='tasks.task',
                verbose_name='Задания',
            ),
        ),
    ]
