"""Django read adapter for the task source catalog."""

from django.db.models import Count

from core_logic.entities.task import SourceListItem
from core_logic.interfaces.source_catalog_repo import ISourceCatalogRepository
from tasks.models import Source


class DjangoSourceCatalogRepository(ISourceCatalogRepository):
    def get_source_list_sources(self):
        return tuple(
            SourceListItem(
                pk=str(source.pk),
                name=source.name,
                short_uuid=source.get_short_uuid(),
                short_name=source.short_name,
                source_type_display=source.get_source_type_display(),
                author=source.author,
                year=source.year,
                url=source.url,
                task_count=source.task_count,
            )
            for source in Source.objects.annotate(
                task_count=Count('task'),
            ).order_by('name')
        )
