# codifier/views.py

from django.http import Http404
from django.views.generic import TemplateView

from infrastructure.container import container


class CodifierListView(TemplateView):
    template_name = 'codifier/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['codifiers'] = (
            container.get_codifier_list_use_case().execute().codifiers
        )
        return context


class CodifierDetailView(TemplateView):
    template_name = 'codifier/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        detail = container.get_codifier_detail_use_case().execute(
            str(self.kwargs['pk']),
        )
        if detail.codifier is None:
            raise Http404('Кодификатор не найден')
        context['codifier'] = detail.codifier
        context['content_tree'] = detail.content_tree
        context['requirements'] = detail.requirements
        context['coverage'] = detail.coverage
        return context
