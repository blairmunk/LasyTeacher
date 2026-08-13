"""Django read adapter for the codifier catalog."""

from core_logic.entities.codifier import CodifierListItem
from core_logic.interfaces.codifier_catalog_repo import (
    ICodifierCatalogRepository,
)
from codifier.models import CodifierSpec


class DjangoCodifierCatalogRepository(ICodifierCatalogRepository):
    def get_list_codifiers(self):
        return tuple(
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
        )
