"""Build global search result data."""

from dataclasses import dataclass

from core_logic.entities.core import GlobalSearchData, GlobalSearchResults
from core_logic.interfaces.global_search_repo import IGlobalSearchRepository
from core_logic.value_objects.short_uuid import (
    is_uuid_search_fragment,
    normalize_uuid_fragment,
)


@dataclass(frozen=True)
class GlobalSearchRequest:
    raw_query: str = ''


class GetGlobalSearchUseCase:
    def __init__(self, core_repo: IGlobalSearchRepository):
        self.core_repo = core_repo

    def execute(self, request: GlobalSearchRequest) -> GlobalSearchData:
        raw_query = request.raw_query.strip()
        query = self._normalize_query(raw_query)

        if not query:
            return GlobalSearchData(query=raw_query)

        uuid_fragment = normalize_uuid_fragment(query)
        is_uuid = is_uuid_search_fragment(uuid_fragment)

        results = GlobalSearchResults()
        total_found = 0
        search_mode = None

        if is_uuid:
            search_mode = 'uuid'
            results = self.core_repo.search_by_uuid(uuid_fragment)
            total_found = results.total_count

        if not is_uuid or total_found == 0:
            search_mode = 'uuid+text' if is_uuid else 'text'
            words = self._split_words(query)
            if words:
                results = self.core_repo.search_by_text(words)
                total_found = results.total_count

        return GlobalSearchData(
            query=raw_query,
            results=results,
            total_found=total_found,
            search_mode=search_mode,
            found_text=self._pluralize_results(total_found),
        )

    def _normalize_query(self, raw_query: str) -> str:
        query = raw_query.replace('"', '').replace("'", '')
        query = query.replace('«', '').replace('»', '')
        return query.replace('(', ' ').replace(')', ' ').strip()

    def _split_words(self, query: str):
        words = [word for word in query.split() if len(word) >= 2]
        if not words and len(query) >= 2:
            return (query,)
        return tuple(words)

    def _pluralize_results(self, count: int) -> str:
        if 11 <= count % 100 <= 19:
            return f'{count} результатов'
        last = count % 10
        if last == 1:
            return f'{count} результат'
        if 2 <= last <= 4:
            return f'{count} результата'
        return f'{count} результатов'
