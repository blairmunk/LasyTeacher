"""Django command adapter for task sources."""

from core_logic.entities.task import SourceCreateParams, SourceCreateResult
from core_logic.interfaces.source_command_repo import ISourceCommandRepository
from tasks.models import Source


class DjangoSourceCommandRepository(ISourceCommandRepository):
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
