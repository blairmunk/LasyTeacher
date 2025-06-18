from django.views.generic import TemplateView

class IndexView(TemplateView):
    template_name = 'core/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Импорты внутри метода чтобы избежать циклических импортов
        from tasks.models import Task
        from works.models import Work
        from students.models import Student
        from events.models import Event
        
        context.update({
            'tasks_count': Task.objects.count(),
            'works_count': Work.objects.count(),
            'students_count': Student.objects.count(),
            'events_count': Event.objects.count(),
        })
        return context
