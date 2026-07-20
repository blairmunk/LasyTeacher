"""Django-backed source lookup for document rendering."""

from works.models import Variant, Work


class DjangoDocumentSourceProvider:
    def get_work_source(self, work_id):
        return Work.objects.get(pk=work_id)

    def get_remedial_source(self, variant_id):
        return Variant.objects.get(pk=variant_id)
