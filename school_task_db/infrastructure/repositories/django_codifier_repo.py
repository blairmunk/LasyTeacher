"""Django implementation of the codifier repository."""

from core_logic.interfaces.codifier_repo import ICodifierRepository
from codifier.models import CodifierSpec


class DjangoCodifierRepository(ICodifierRepository):
    def get_list_codifiers(self):
        return CodifierSpec.objects.prefetch_related(
            'content_entries',
            'requirements',
        )

    def get_detail_codifiers(self):
        return CodifierSpec.objects.prefetch_related(
            'content_entries',
            'requirements',
        )

    def get_content_tree(self, codifier_id: str):
        codifier = CodifierSpec.objects.get(pk=codifier_id)
        return codifier.get_content_tree()

    def get_requirements(self, codifier_id: str):
        codifier = CodifierSpec.objects.get(pk=codifier_id)
        return codifier.requirements.all()

    def get_coverage(self, codifier_id: str) -> dict:
        codifier = CodifierSpec.objects.get(pk=codifier_id)
        return codifier.get_coverage()
