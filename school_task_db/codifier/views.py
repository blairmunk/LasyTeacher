# codifier/views.py

from django.views.generic import ListView, DetailView

from infrastructure.container import container
from .models import CodifierSpec


class CodifierListView(ListView):
    model = CodifierSpec
    template_name = 'codifier/list.html'
    context_object_name = 'codifiers'

    def get_queryset(self):
        return container.get_codifier_list_use_case().execute().codifiers


class CodifierDetailView(DetailView):
    model = CodifierSpec
    template_name = 'codifier/detail.html'
    context_object_name = 'codifier'

    def get_queryset(self):
        return container.get_codifier_detail_use_case().get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        detail = container.get_codifier_detail_use_case().execute(
            str(self.object.pk),
        )
        context['content_tree'] = detail.content_tree
        context['requirements'] = detail.requirements
        context['coverage'] = detail.coverage
        return context
