"""Django-backed source lookup for document rendering."""

from works.models import Work


class DjangoDocumentSourceProvider:
    def get_work_source(self, work_id):
        return Work.objects.get(pk=work_id)
