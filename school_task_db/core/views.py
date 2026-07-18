from django.shortcuts import render
from django.views.generic import TemplateView
from infrastructure.container import container


class IndexView(TemplateView):
    template_name = 'core/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        summary = container.get_dashboard_summary_use_case().execute()
        context['tasks_count'] = summary.tasks_count
        context['works_count'] = summary.works_count
        context['variants_count'] = summary.variants_count
        context['orphan_variants_count'] = summary.orphan_variants_count
        context['students_count'] = summary.students_count
        context['events_count'] = summary.events_count
        context['groups_count'] = summary.groups_count
        return context


def global_search(request):
    """Глобальный поиск: UUID + текст"""
    search_data = container.get_global_search_use_case().execute(
        container.core_form_adapter.global_search_request_from_query(
            request.GET,
        ),
    )
    return render(request, 'core/search_results.html', {
        'query': search_data.query,
        'results': search_data.results,
        'total_found': search_data.total_found,
        'search_mode': search_data.search_mode,
        'found_text': search_data.found_text,
    })
