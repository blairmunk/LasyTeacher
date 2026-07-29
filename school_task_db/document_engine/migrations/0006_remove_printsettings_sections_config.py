from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            'document_generator',
            '0005_remove_legacy_theory_sections',
        ),
    ]

    operations = [
        migrations.RemoveField(
            model_name='printsettings',
            name='sections_config',
        ),
    ]
