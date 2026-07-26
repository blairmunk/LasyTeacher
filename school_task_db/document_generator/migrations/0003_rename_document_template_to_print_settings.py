import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('document_generator', '0002_alter_documenttemplate_options_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(
            old_name='DocumentTemplate',
            new_name='PrintSettings',
        ),
        migrations.RenameField(
            model_name='printsettings',
            old_name='template_type',
            new_name='document_type',
        ),
        migrations.AlterModelOptions(
            name='printsettings',
            options={
                'ordering': ['-is_default', 'document_type', 'name'],
                'verbose_name': 'Профиль печати',
                'verbose_name_plural': 'Профили печати',
            },
        ),
        migrations.AlterField(
            model_name='printsettings',
            name='created_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='print_settings_profiles',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Создатель',
            ),
        ),
    ]
