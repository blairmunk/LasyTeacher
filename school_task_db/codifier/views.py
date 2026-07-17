# codifier/views.py

from django.http import Http404
from django.views.generic import ListView, TemplateView

from infrastructure.container import container
from .models import CodifierSpec


class CodifierListView(ListView):
    model = CodifierSpec
    template_name = 'codifier/list.html'
    context_object_name = 'codifiers'

    def get_queryset(self):
        return container.get_codifier_list_use_case().execute().codifiers


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
