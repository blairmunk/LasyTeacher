import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('document_engine', '0007_alter_printsettings_document_type'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(
            old_name='PrintSettings',
            new_name='PresentationProfile',
        ),
        migrations.AlterField(
            model_name='presentationprofile',
            name='created_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='presentation_profiles',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Создатель',
            ),
        ),
    ]
