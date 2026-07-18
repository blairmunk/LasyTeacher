"""Django implementation of the codifier repository."""

from core_logic.entities.codifier import (
    CodifierContentEntry,
    CodifierDetailSpec,
    CodifierListItem,
    CodifierObjectRef,
    CodifierRequirement,
    CodifierSiblingCode,
)
from core_logic.interfaces.codifier_repo import ICodifierRepository
from codifier.models import CodifierSpec


class DjangoCodifierRepository(ICodifierRepository):
    def get_list_codifiers(self):
        return [
            CodifierListItem(
                pk=str(codifier.pk),
                short_name=codifier.short_name,
                name=codifier.name,
                exam_type=codifier.exam_type,
                is_active=codifier.is_active,
                content_entries_count=codifier.content_entries.count(),
                requirements_count=codifier.requirements.count(),
            )
            for codifier in CodifierSpec.objects.prefetch_related(
                'content_entries',
                'requirements',
            )
        ]

    def get_codifier(self, codifier_id: str):
        codifier = CodifierSpec.objects.prefetch_related(
            'content_entries',
            'requirements',
        ).filter(pk=codifier_id).first()
        if codifier is None:
            return None

        return CodifierDetailSpec(
            pk=str(codifier.pk),
            short_name=codifier.short_name,
            name=codifier.name,
            content_entries_count=codifier.content_entries.count(),
        )

    def get_content_tree(self, codifier_id: str):
        codifier = CodifierSpec.objects.get(pk=codifier_id)
        return [
            self._build_content_entry(entry)
            for entry in codifier.get_content_tree()
        ]

    def get_requirements(self, codifier_id: str):
        codifier = CodifierSpec.objects.get(pk=codifier_id)
        return [
            CodifierRequirement(
                code=requirement.code,
                name=requirement.name,
                cognitive_level=requirement.cognitive_level,
                cognitive_level_display=(
                    requirement.get_cognitive_level_display()
                    if requirement.cognitive_level
                    else ''
                ),
                task_count=requirement.get_task_count(),
            )
            for requirement in codifier.requirements.all()
        ]

    def get_coverage(self, codifier_id: str) -> dict:
        codifier = CodifierSpec.objects.get(pk=codifier_id)
        return codifier.get_coverage()

    def _build_content_entry(self, entry):
        return CodifierContentEntry(
            code=entry.code,
            name=entry.name,
            topic=(
                CodifierObjectRef(name=entry.topic.name)
                if entry.topic
                else None
            ),
            subtopic=(
                CodifierObjectRef(name=entry.subtopic.name)
                if entry.subtopic
                else None
            ),
            grade_studied=entry.grade_studied,
            task_count=entry.get_task_count(),
            sibling_codes=[
                CodifierSiblingCode(
                    codifier=CodifierObjectRef(
                        short_name=sibling.codifier.short_name,
                    ),
                    code=sibling.code,
                )
                for sibling in entry.get_sibling_codes()
            ],
            children=[
                self._build_content_entry(child)
                for child in entry.get_sorted_children()
            ],
        )
