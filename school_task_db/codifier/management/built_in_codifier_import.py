"""Shared CLI adapter for importing bundled codifier definitions."""

from django.core.management.base import BaseCommand

from core_logic.entities.codifier_import import (
    CodifierImportContentItem,
    CodifierImportDefinition,
    CodifierImportRequirementItem,
    ImportCodifierRequest,
)
from infrastructure.container import container


def build_codifier_definition(
    *,
    name,
    short_name,
    subject,
    exam_type,
    year,
    content_data,
    requirements_data,
):
    return CodifierImportDefinition(
        name=name,
        short_name=short_name,
        subject=subject,
        exam_type=exam_type,
        year=year,
        content=tuple(
            CodifierImportContentItem(
                code=code,
                name=item_name,
                parent_code=parent_code or '',
                grade_studied=grade_studied,
            )
            for code, item_name, parent_code, grade_studied in content_data
        ),
        requirements=tuple(
            CodifierImportRequirementItem(
                code=code,
                name=item_name,
                cognitive_level=cognitive_level,
            )
            for code, item_name, cognitive_level in requirements_data
        ),
    )


class BuiltInCodifierImportCommand(BaseCommand):
    definition = None

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help=(
                f'Удалить существующий кодификатор '
                f'{self.definition.short_name} перед загрузкой'
            ),
        )

    def handle(self, *args, **options):
        result = container.import_codifier_use_case().execute(
            ImportCodifierRequest(
                definition=self.definition,
                clear_existing=options['clear'],
            ),
        )
        if result.deleted_count:
            self.stdout.write(self.style.WARNING(
                f'Удалён кодификатор {self.definition.short_name} '
                f'({result.deleted_count} объектов)',
            ))
        if result.status == 'already_exists':
            self.stdout.write(self.style.ERROR(
                f'Кодификатор {self.definition.short_name} уже существует. '
                'Используйте --clear для перезагрузки.',
            ))
            return

        self.stdout.write(f'✅ Создан: {result.display_name}')
        self.stdout.write(
            f'   📋 Элементов содержания: {result.content_count}',
        )
        self.stdout.write(f'   📝 Требований: {result.requirements_count}')
        self.stdout.write(self.style.SUCCESS(
            f'\n🎉 Кодификатор {self.definition.short_name} загружен: '
            f'{result.content_count} элементов, '
            f'{result.requirements_count} требований',
        ))
