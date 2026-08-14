from math import ceil

from django.db import migrations, models


def rows_to_area(apps, schema_editor):
    for model_name in ('WorkAnalogGroup', 'VariantTask'):
        model = apps.get_model('works', model_name)
        for row in model.objects.all().iterator():
            row.blank_space_area_cm2 = max(
                1,
                ceil(row.blank_space_area_cm2 * 6.5),
            )
            row.save(update_fields=['blank_space_area_cm2'])


def area_to_rows(apps, schema_editor):
    for model_name in ('WorkAnalogGroup', 'VariantTask'):
        model = apps.get_model('works', model_name)
        for row in model.objects.all().iterator():
            row.blank_space_area_cm2 = max(
                1,
                round(row.blank_space_area_cm2 / 6.5),
            )
            row.save(update_fields=['blank_space_area_cm2'])


class Migration(migrations.Migration):
    dependencies = [
        ('works', '0017_varianttask_page_break_after_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='varianttask',
            old_name='blank_cells_rows',
            new_name='blank_space_area_cm2',
        ),
        migrations.RenameField(
            model_name='workanaloggroup',
            old_name='blank_cells_rows',
            new_name='blank_space_area_cm2',
        ),
        migrations.RunPython(rows_to_area, area_to_rows),
        migrations.AlterField(
            model_name='varianttask',
            name='blank_space_area_cm2',
            field=models.PositiveIntegerField(
                default=40,
                verbose_name='Площадь поля для ответа, см²',
            ),
        ),
        migrations.AlterField(
            model_name='workanaloggroup',
            name='blank_space_area_cm2',
            field=models.PositiveIntegerField(
                default=40,
                verbose_name='Площадь поля для ответа, см²',
            ),
        ),
    ]
