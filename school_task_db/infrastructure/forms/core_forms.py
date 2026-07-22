"""Infrastructure helpers for Django core forms and query params."""

from core_logic.entities.task import TaskExportFilters
from core_logic.entities.task_import import (
    TaskImportExecutionSubmissionRequest,
    TaskImportFileRequest,
)
from core_logic.use_cases.export_tasks import ExportTasksRequest
from core_logic.use_cases.get_global_search import GlobalSearchRequest


class CoreFormAdapter:
    def dashboard_summary_context(self, summary):
        return {
            'tasks_count': summary.tasks_count,
            'works_count': summary.works_count,
            'variants_count': summary.variants_count,
            'orphan_variants_count': summary.orphan_variants_count,
            'students_count': summary.students_count,
            'events_count': summary.events_count,
            'groups_count': summary.groups_count,
        }

    def global_search_request_from_query(self, query):
        return GlobalSearchRequest(raw_query=query.get('q', ''))

    def global_search_context(self, search_data):
        return {
            'query': search_data.query,
            'results': search_data.results,
            'total_found': search_data.total_found,
            'search_mode': search_data.search_mode,
            'found_text': search_data.found_text,
        }

    def task_import_file_request_from_upload(self, uploaded_file):
        return TaskImportFileRequest(
            filename=uploaded_file.name,
            file_size=uploaded_file.size,
            content=uploaded_file.read(),
        )

    def task_import_execution_submission_from_upload(self, uploaded_file, post_data):
        return TaskImportExecutionSubmissionRequest(
            filename=uploaded_file.name,
            file_size=uploaded_file.size,
            content=uploaded_file.read(),
            form_data=self._post_lists(post_data),
        )

    def export_tasks_request_from_query(self, query, export_date):
        return ExportTasksRequest(
            filters=TaskExportFilters(
                topic_id=query.get('topic', ''),
                subject=query.get('subject', ''),
                grade=query.get('grade', ''),
            ),
            export_date=export_date,
        )

    def _post_lists(self, post_data):
        return {
            key: post_data.getlist(key)
            for key in post_data
        }
