from django.shortcuts import render
from django.views.generic import TemplateView
from datetime import datetime, timedelta

class ReportsDashboardView(TemplateView):
    template_name = 'reports/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_date = datetime.now()
        
        # Импорты внутри метода для избежания циклических импортов
        from students.models import Student
        from events.models import Event, Mark
        
        # Ученики без оценок
        students_without_marks = Student.objects.filter(mark__isnull=True).distinct()
        
        # События со статусами
        planned_events = Event.objects.filter(status='planned')
        conducted_events = Event.objects.filter(status='conducted')
        checked_events = Event.objects.filter(status='checked')
        
        # Просроченные события
        overdue_events = Event.objects.filter(
            date__lt=current_date,
            status='planned'
        )
        
        # Грядущие события
        upcoming_events = Event.objects.filter(
            date__gte=current_date,
            date__lte=current_date + timedelta(days=7),
            status='planned'
        )
        
        # Неоценённые работы
        ungraded_marks = Mark.objects.filter(score__isnull=True)
        
        context.update({
            'students_without_marks': students_without_marks,
            'planned_events': planned_events,
            'conducted_events': conducted_events,
            'checked_events': checked_events,
            'overdue_events': overdue_events,
            'upcoming_events': upcoming_events,
            'ungraded_marks': ungraded_marks,
        })
        
        return context
