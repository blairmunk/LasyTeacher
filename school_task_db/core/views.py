from django.shortcuts import render
from django.views.generic import TemplateView
from .utils import search_by_uuid

class IndexView(TemplateView):
    template_name = 'core/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Безопасные импорты внутри метода
        try:
            from tasks.models import Task
            tasks_count = Task.objects.count()
        except ImportError:
            tasks_count = 0
            
        try:
            from works.models import Work
            works_count = Work.objects.count()
        except ImportError:
            works_count = 0
            
        try:
            from students.models import Student
            students_count = Student.objects.count()
        except ImportError:
            students_count = 0
            
        try:
            from events.models import Event
            events_count = Event.objects.count()
        except ImportError:
            events_count = 0    
        
        
        # Статистика
        context.update({
            'tasks_count': Task.objects.count(),
            'works_count': Work.objects.count(),
            'students_count': Student.objects.count(),
            'events_count': Event.objects.count(),
        })
        
        # Поиск по UUID
        search_query = self.request.GET.get('uuid_search')
        if search_query:
            context['search_results'] = {
                'tasks': search_by_uuid(Task, search_query)[:5],
                'works': search_by_uuid(Work, search_query)[:5],
                'variants': search_by_uuid(Variant, search_query)[:5],
            }
        
        return context

def global_search(request):
    """Глобальный поиск по UUID"""
    from tasks.models import Task      # Добавить импорты
    from works.models import Work, Variant
    
    query = request.GET.get('q', '')
    results = {}
    
    if query:
        results = {
            'tasks': search_by_uuid(Task, query),
            'works': search_by_uuid(Work, query), 
            'variants': search_by_uuid(Variant, query),
        }
    
    return render(request, 'core/search_results.html', {
        'query': query,
        'results': results
    })