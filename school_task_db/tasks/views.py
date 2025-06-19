# tasks/views.py (ИСПРАВЛЕННАЯ ВЕРСИЯ)
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q

# ИСПРАВИТЬ ИМПОРТ - убрать TaskImageFormSet пока что
# from .forms import TaskForm, TaskImageFormSet  # СТАРАЯ ВЕРСИЯ
try:
    from .forms import TaskForm  # НОВАЯ ВЕРСИЯ - импортируем только то что есть
except ImportError:
    TaskForm = None  # Если формы еще нет

from .models import Task, TaskImage
from curriculum.models import Topic, SubTopic

# Остальные view можно оставить как есть, но использовать стандартные Django формы
# если кастомные еще не готовы

class TaskListView(ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Task.objects.select_related('topic', 'subtopic').order_by('-created_at')
        
        # Поиск
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(text__icontains=search) |
                Q(answer__icontains=search) |
                Q(topic__name__icontains=search)
            )
        
        # Фильтр по теме
        topic_id = self.request.GET.get('topic')
        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)
        
        # Фильтр по типу
        task_type = self.request.GET.get('task_type')
        if task_type:
            queryset = queryset.filter(task_type=task_type)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['topics'] = Topic.objects.all()
        
        # Получаем типы заданий из справочников
        try:
            from references.helpers import get_task_type_choices
            context['task_types'] = get_task_type_choices()
        except ImportError:
            # Fallback если справочники не работают
            context['task_types'] = [
                ('computational', 'Расчётная задача'),
                ('qualitative', 'Качественная задача'),
                ('theoretical', 'Теоретический вопрос'),
            ]
        
        return context

class TaskDetailView(DetailView):
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'
    
    def get_queryset(self):
        return Task.objects.select_related('topic', 'subtopic').prefetch_related('images')

class TaskCreateView(CreateView):
    model = Task
    template_name = 'tasks/task_form.html'
    fields = [
        'text', 'answer', 'topic', 'subtopic',
        'task_type', 'difficulty', 'cognitive_level',
        'content_element', 'requirement_element',
        'short_solution', 'full_solution', 'hint', 'instruction',
        'estimated_time'
    ]
    
    def get_form_class(self):
        # Используем кастомную форму если есть, иначе стандартную
        if TaskForm:
            return TaskForm
        return super().get_form_class()
    
    def form_valid(self, form):
        messages.success(self.request, 'Задание успешно создано!')
        return super().form_valid(form)

class TaskUpdateView(UpdateView):
    model = Task
    template_name = 'tasks/task_form.html'
    fields = [
        'text', 'answer', 'topic', 'subtopic',
        'task_type', 'difficulty', 'cognitive_level',
        'content_element', 'requirement_element',
        'short_solution', 'full_solution', 'hint', 'instruction',
        'estimated_time'
    ]
    
    def get_form_class(self):
        if TaskForm:
            return TaskForm
        return super().get_form_class()
    
    def form_valid(self, form):
        messages.success(self.request, 'Задание успешно обновлено!')
        return super().form_valid(form)

class TaskDeleteView(DeleteView):
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    context_object_name = 'task'
    success_url = reverse_lazy('tasks:list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Задание успешно удалено!')
        return super().delete(request, *args, **kwargs)

# AJAX views для динамической загрузки
def load_subtopics(request):
    """AJAX для загрузки подтем при выборе темы"""
    topic_id = request.GET.get('topic_id')
    subtopics = SubTopic.objects.filter(topic_id=topic_id).order_by('name')
    
    data = {
        'subtopics': [
            {'id': subtopic.id, 'name': subtopic.name} 
            for subtopic in subtopics
        ]
    }
    
    return JsonResponse(data)

def load_codifier_elements(request):
    """AJAX для загрузки элементов кодификатора при выборе предмета"""
    subject = request.GET.get('subject')
    category = request.GET.get('category')  # content_elements или requirement_elements
    
    try:
        from references.helpers import get_subject_reference_choices
        choices = get_subject_reference_choices(subject, category)
        
        data = {
            'elements': [
                {'code': code, 'name': name}
                for code, name in choices
            ]
        }
    except ImportError:
        data = {'elements': []}
    
    return JsonResponse(data)
