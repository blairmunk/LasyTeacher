from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.db.models import Q, Count, Avg
from datetime import datetime, timedelta
from .models import (
    Task, AnalogGroup, Work, WorkAnalogGroup, Variant,
    Student, StudentGroup, Event, Mark
)
from .forms import (
    TaskForm, AnalogGroupForm, WorkForm, WorkAnalogGroupFormSet,
    VariantGenerationForm, StudentForm, StudentGroupForm, EventForm,
    MarkForm, StudentVariantAssignmentForm
)
from .forms import TaskImageFormSet

# Главная страница
def index(request):
    context = {
        'tasks_count': Task.objects.count(),
        'works_count': Work.objects.count(),
        'students_count': Student.objects.count(),
        'events_count': Event.objects.count(),
    }
    return render(request, 'task_manager/index.html', context)

# Задания
class TaskListView(ListView):
    model = Task
    template_name = 'task_manager/task_list.html'  # ИСПРАВЛЕНО
    context_object_name = 'tasks'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Task.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(text__icontains=search) |
                Q(topic__icontains=search) |
                Q(section__icontains=search)
            )
        return queryset

class TaskDetailView(DetailView):
    model = Task
    template_name = 'task_manager/task_detail.html'  # ИСПРАВЛЕНО


class TaskCreateView(CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'task_manager/task_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['image_formset'] = TaskImageFormSet(self.request.POST, self.request.FILES)
        else:
            context['image_formset'] = TaskImageFormSet()
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        image_formset = context['image_formset']
        
        if image_formset.is_valid():
            response = super().form_valid(form)
            image_formset.instance = self.object
            image_formset.save()
            messages.success(self.request, 'Задание успешно создано!')
            return response
        else:
            return self.render_to_response(self.get_context_data(form=form))


class TaskUpdateView(UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'task_manager/task_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['image_formset'] = TaskImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        else:
            context['image_formset'] = TaskImageFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        image_formset = context['image_formset']
        
        if image_formset.is_valid():
            response = super().form_valid(form)
            image_formset.save()
            messages.success(self.request, 'Задание успешно обновлено!')
            return response
        else:
            return self.render_to_response(self.get_context_data(form=form))

# Группы аналогов
class AnalogGroupListView(ListView):
    model = AnalogGroup
    template_name = 'task_manager/analoggroup_list.html'  # ИСПРАВЛЕНО
    context_object_name = 'analog_groups'
    paginate_by = 20

class AnalogGroupDetailView(DetailView):
    model = AnalogGroup
    template_name = 'task_manager/analoggroup_detail.html'  # ИСПРАВЛЕНО

# Работы
class WorkListView(ListView):
    model = Work
    template_name = 'task_manager/work_list.html'  # ИСПРАВЛЕНО
    context_object_name = 'works'
    paginate_by = 20

class WorkDetailView(DetailView):
    model = Work
    template_name = 'task_manager/work_detail.html'  # ИСПРАВЛЕНО
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['variants'] = Variant.objects.filter(work=self.object)
        context['analog_groups'] = WorkAnalogGroup.objects.filter(work=self.object)
        return context

class WorkCreateView(CreateView):
    model = Work
    form_class = WorkForm
    template_name = 'task_manager/work_form.html'  # ИСПРАВЛЕНО
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = WorkAnalogGroupFormSet(self.request.POST)
        else:
            context['formset'] = WorkAnalogGroupFormSet()
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            response = super().form_valid(form)
            formset.instance = self.object
            formset.save()
            messages.success(self.request, 'Работа успешно создана!')
            return response
        else:
            return self.render_to_response(self.get_context_data(form=form))

def generate_variants(request, work_id):
    """Генерация вариантов для работы"""
    work = get_object_or_404(Work, pk=work_id)
    
    if request.method == 'POST':
        form = VariantGenerationForm(request.POST)
        if form.is_valid():
            count = form.cleaned_data['count']
            try:
                variants = work.generate_variants(count)
                messages.success(
                    request, 
                    f'Успешно создано {len(variants)} вариантов!'
                )
                return redirect('task_manager:work-detail', pk=work.pk)  # ИСПРАВЛЕНО
            except Exception as e:
                messages.error(request, f'Ошибка при создании вариантов: {str(e)}')
    else:
        form = VariantGenerationForm()
    
    return render(request, 'task_manager/generate_variants.html', {  # ИСПРАВЛЕНО
        'work': work,
        'form': form
    })

# Варианты
class VariantListView(ListView):
    model = Variant
    template_name = 'task_manager/variant_list.html'  # ИСПРАВЛЕНО
    context_object_name = 'variants'
    paginate_by = 20

class VariantDetailView(DetailView):
    model = Variant
    template_name = 'task_manager/variant_detail.html'  # ИСПРАВЛЕНО

# Ученики
class StudentListView(ListView):
    model = Student
    template_name = 'task_manager/student_list.html'  # ИСПРАВЛЕНО
    context_object_name = 'students'
    paginate_by = 50

class StudentCreateView(CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'task_manager/student_form.html'  # ИСПРАВЛЕНО
    success_url = reverse_lazy('task_manager:student-list')  # ИСПРАВЛЕНО

# Классы
class StudentGroupListView(ListView):
    model = StudentGroup
    template_name = 'task_manager/studentgroup_list.html'  # ИСПРАВЛЕНО
    context_object_name = 'student_groups'

class StudentGroupDetailView(DetailView):
    model = StudentGroup
    template_name = 'task_manager/studentgroup_detail.html'  # ИСПРАВЛЕНО

# События
class EventListView(ListView):
    model = Event
    template_name = 'task_manager/event_list.html'  # ИСПРАВЛЕНО
    context_object_name = 'events'
    paginate_by = 20

class EventDetailView(DetailView):
    model = Event
    template_name = 'task_manager/event_detail.html'  # ИСПРАВЛЕНО
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['marks'] = Mark.objects.filter(event=self.object)
        return context

class EventCreateView(CreateView):
    model = Event
    form_class = EventForm
    template_name = 'task_manager/event_form.html'  # ИСПРАВЛЕНО

def assign_variants(request, event_id):
    """Назначение вариантов ученикам для события"""
    event = get_object_or_404(Event, pk=event_id)
    
    if request.method == 'POST':
        form = StudentVariantAssignmentForm(event, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Варианты успешно назначены!')
            return redirect('task_manager:event-detail', pk=event.pk)  # ИСПРАВЛЕНО
    else:
        form = StudentVariantAssignmentForm(event)
    
    return render(request, 'task_manager/assign_variants.html', {  # ИСПРАВЛЕНО
        'event': event,
        'form': form
    })

# Отчёты
def reports_view(request):
    """Страница отчётов"""
    current_date = datetime.now()
    
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
    
    context = {
        'students_without_marks': students_without_marks,
        'planned_events': planned_events,
        'conducted_events': conducted_events,
        'checked_events': checked_events,
        'overdue_events': overdue_events,
        'upcoming_events': upcoming_events,
        'ungraded_marks': ungraded_marks,
    }
    
    return render(request, 'task_manager/reports.html', context)  # ИСПРАВЛЕНО

# API для работы с группами аналогов
def analog_group_tasks_api(request, group_id):
    """API для получения заданий группы аналогов"""
    group = get_object_or_404(AnalogGroup, pk=group_id)
    tasks = group.tasks.all()
    
    data = {
        'group_name': group.name,
        'tasks': [
            {
                'id': task.id,
                'text': task.text[:100] + '...' if len(task.text) > 100 else task.text,
                'topic': task.topic,
                'difficulty': task.get_difficulty_display(),
            }
            for task in tasks
        ]
    }
    
    return JsonResponse(data)
