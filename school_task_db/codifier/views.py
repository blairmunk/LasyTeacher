# codifier/views.py

from django.views.generic import ListView, DetailView
from .models import CodifierSpec, ContentEntry


class CodifierListView(ListView):
    model = CodifierSpec
    template_name = 'codifier/list.html'
    context_object_name = 'codifiers'


class CodifierDetailView(DetailView):
    model = CodifierSpec
    template_name = 'codifier/detail.html'
    context_object_name = 'codifier'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        spec = self.object
        context['content_tree'] = spec.get_content_tree()
        context['requirements'] = spec.requirements.all()
        context['coverage'] = spec.get_coverage()
        return context
