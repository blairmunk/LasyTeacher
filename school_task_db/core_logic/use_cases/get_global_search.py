"""Build global search result data."""

from dataclasses import dataclass

from core_logic.entities.core import GlobalSearchData
from core_logic.interfaces.core_repo import ICoreRepository


@dataclass(frozen=True)
class GlobalSearchRequest:
    raw_query: str = ''


class GetGlobalSearchUseCase:
    def __init__(self, core_repo: ICoreRepository):
        self.core_repo = core_repo

    def execute(self, request: GlobalSearchRequest) -> GlobalSearchData:
        raw_query = request.raw_query.strip()
        query = self._normalize_query(raw_query)

        if not query:
            return GlobalSearchData(query=raw_query)

        hex_clean = query.replace('#', '').replace('-', '').replace(' ', '').lower()
        is_hex = len(hex_clean) >= 3 and all(
            char in '0123456789abcdef'
            for char in hex_clean
        )

        results = {}
        total_found = 0
        search_mode = None

        if is_hex:
            search_mode = 'uuid'
            results = self.core_repo.search_by_uuid(hex_clean)
            total_found = self._count_results(results)

        if not is_hex or total_found == 0:
            search_mode = 'uuid+text' if is_hex else 'text'
            words = self._split_words(query)
            if words:
                results = self.core_repo.search_by_text(words)
                total_found = self._count_results(results)

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
            return [query]
        return words

    def _count_results(self, results) -> int:
        return sum(len(result) for result in results.values())

    def _pluralize_results(self, count: int) -> str:
        if 11 <= count % 100 <= 19:
            return f'{count} результатов'
        last = count % 10
        if last == 1:
            return f'{count} результат'
        if 2 <= last <= 4:
            return f'{count} результата'
        return f'{count} результатов'
