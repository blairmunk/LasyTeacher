"""Django persistence adapter for importing complete codifiers."""

from codifier.models import CodifierSpec, ContentEntry, Requirement
from core_logic.entities.codifier_import import CodifierImportDefinition
from core_logic.interfaces.codifier_import_repo import (
    ICodifierImportRepository,
)


class DjangoCodifierImportRepository(ICodifierImportRepository):
    def codifier_exists(
        self,
        exam_type: str,
        year: int,
        subject: str,
    ) -> bool:
        return self._matching_codifiers(exam_type, year, subject).exists()

    def delete_codifier(
        self,
        exam_type: str,
        year: int,
        subject: str,
    ) -> int:
        deleted_count, _ = self._matching_codifiers(
            exam_type,
            year,
            subject,
        ).delete()
        return deleted_count

    def create_codifier(self, definition: CodifierImportDefinition) -> str:
        codifier = CodifierSpec.objects.create(
            name=definition.name,
            short_name=definition.short_name,
            subject=definition.subject,
            exam_type=definition.exam_type,
            year=definition.year,
            is_active=definition.is_active,
        )

        entries_by_code = {}
        for item in definition.content:
            entry = ContentEntry.objects.create(
                codifier=codifier,
                code=item.code,
                name=item.name,
                parent=entries_by_code.get(item.parent_code),
                grade_studied=item.grade_studied,
            )
            entries_by_code[item.code] = entry

        Requirement.objects.bulk_create([
            Requirement(
                codifier=codifier,
                code=item.code,
                name=item.name,
                cognitive_level=item.cognitive_level,
            )
            for item in definition.requirements
        ])
        return str(codifier)

    @staticmethod
    def _matching_codifiers(exam_type: str, year: int, subject: str):
        return CodifierSpec.objects.filter(
            exam_type=exam_type,
            year=year,
            subject=subject,
        )
