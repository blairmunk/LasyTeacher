"""Infrastructure helpers for Django codifier screens."""


class CodifierFormAdapter:
    def codifier_list_context(self, list_data):
        return {
            'codifiers': list_data.codifiers,
        }

    def codifier_detail_context(self, detail):
        return {
            'codifier': detail.codifier,
            'content_tree': detail.content_tree,
            'requirements': detail.requirements,
            'coverage': detail.coverage,
        }
