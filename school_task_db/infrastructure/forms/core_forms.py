"""Infrastructure helpers for Django core forms and query params."""

from core_logic.use_cases.get_global_search import GlobalSearchRequest


class CoreFormAdapter:
    def global_search_request_from_query(self, query):
        return GlobalSearchRequest(raw_query=query.get('q', ''))
