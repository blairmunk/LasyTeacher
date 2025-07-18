from django.shortcuts import render
from django.views.generic import TemplateView

class GenerateView(TemplateView):
    """Представление для генерации документов"""
    template_name = 'latex_generator/generate.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Генерация LaTeX документов'
        return context

class StatusView(TemplateView):
    """Представление статуса генерации"""
    template_name = 'latex_generator/status.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Статус генерации'
        return context
