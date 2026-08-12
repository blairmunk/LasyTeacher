"""Django implementation of the task source repository."""

from django.db.models import Count

from core_logic.entities.task import (
    SourceCreateParams,
    SourceCreateResult,
    SourceListItem,
)
from core_logic.interfaces.source_catalog_repo import ISourceCatalogRepository
from core_logic.interfaces.source_command_repo import ISourceCommandRepository
from tasks.models import Source


class DjangoSourceRepository(
    ISourceCatalogRepository,
    ISourceCommandRepository,
):
    def get_source_list_sources(self):
        return [
            SourceListItem(
                pk=str(source.pk),
                name=source.name,
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
        ]

    def create_source(self, params: SourceCreateParams) -> SourceCreateResult:
        source = Source.objects.create(
            name=params.name,
            short_name=params.short_name,
            source_type=params.source_type,
            author=params.author,
            year=params.year,
            url=params.url,
            isbn=params.isbn,
            notes=params.notes,
        )
        return SourceCreateResult(
            pk=str(source.pk),
            display_name=str(source),
        )
