from django.shortcuts import render
from django.views.generic import TemplateView
from infrastructure.container import container


class IndexView(TemplateView):
    template_name = 'core/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        summary = container.get_dashboard_summary_use_case().execute()
        context.update(container.core_form_adapter.dashboard_summary_context(summary))
        return context


def global_search(request):
    """Глобальный поиск: UUID + текст"""
    search_data = container.get_global_search_use_case().execute(
        container.core_form_adapter.global_search_request_from_query(
            request.GET,
        ),
    )
    return render(
        request,
        'core/search_results.html',
        container.core_form_adapter.global_search_context(search_data),
    )
