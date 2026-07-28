from django.db import migrations


def remove_legacy_theory_sections(apps, schema_editor):
    print_settings_model = apps.get_model(
        'document_generator',
        'PrintSettings',
    )
    for print_settings in print_settings_model.objects.all().iterator():
        config = print_settings.sections_config
        sections = (
            config.get('sections')
            if isinstance(config, dict)
            else config
        )
        if not isinstance(sections, list):
            continue

        filtered_sections = [
            section
            for section in sections
            if not (
                isinstance(section, dict)
                and (
                    section.get('type')
                    or section.get('section_type')
                ) == 'theory'
            )
        ]
        if len(filtered_sections) == len(sections):
            continue

        if isinstance(config, dict):
            updated_config = dict(config)
            updated_config['sections'] = filtered_sections
        else:
            updated_config = filtered_sections
        print_settings_model.objects.filter(pk=print_settings.pk).update(
            sections_config=updated_config,
        )


class Migration(migrations.Migration):

    dependencies = [
        (
            'document_generator',
            '0004_alter_printsettings_options_and_more',
        ),
    ]

    operations = [
        migrations.RunPython(
            remove_legacy_theory_sections,
            migrations.RunPython.noop,
        ),
    ]
