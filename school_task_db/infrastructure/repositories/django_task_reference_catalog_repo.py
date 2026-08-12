"""Django read adapter for merged subject reference catalogs."""

from typing import List

from core_logic.entities.task import ReferenceElementOption
from core_logic.interfaces.task_reference_catalog_repo import (
    ITaskReferenceCatalogRepository,
)
from core_logic.services.reference_catalog import merge_reference_choices
from references.models import SubjectReference


class DjangoTaskReferenceCatalogRepository(ITaskReferenceCatalogRepository):
    def get_reference_element_options(
        self,
        subject: str,
        category: str,
    ) -> List[ReferenceElementOption]:
        catalogs = (
            reference.get_choices()
            for reference in SubjectReference.objects.filter(
                subject=subject,
                category=category,
                is_active=True,
            ).order_by('grade_level', 'created_at')
        )
        return [
            ReferenceElementOption(code=code, name=name)
            for code, name in merge_reference_choices(catalogs)
        ]
