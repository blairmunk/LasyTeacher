from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from .forms import TaskForm
from .models import Task, TaskImage
from .utils import math_status_cache  # НОВЫЙ ИМПОРТ
from curriculum.models import Topic, SubTopic
from latex_generator.utils.formula_utils import formula_processor

class TaskListView(ListView):
    model = Task
    template_name = 'tasks/list.html'
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
        
        # ОПТИМИЗИРОВАНО: Фильтрация с использованием кэша
        math_filter = self.request.GET.get('math_filter')
        
        if math_filter == 'with_math':
            # Получаем ID заданий с формулами из кэша
            task_ids_with_math = math_status_cache.get_tasks_with_math_ids()
            queryset = queryset.filter(id__in=task_ids_with_math)
        
        elif math_filter == 'with_errors':
            # Получаем ID заданий с ошибками из кэша
            task_ids_with_errors = math_status_cache.get_tasks_with_errors_ids()
            queryset = queryset.filter(id__in=task_ids_with_errors)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['topics'] = Topic.objects.all()
        
        # Получаем типы заданий из справочников
        try:
            from references.helpers import get_task_type_choices
            context['task_types'] = get_task_type_choices()
        except ImportError:
            context['task_types'] = [
                ('computational', 'Расчётная задача'),
                ('qualitative', 'Качественная задача'),
                ('theoretical', 'Теоретический вопрос'),
            ]
        
        # Информация о текущем фильтре
        context['current_filter'] = self.request.GET.get('math_filter', 'all')
        context['search_query'] = self.request.GET.get('search', '')
        
        # НОВОЕ: Добавляем статистику кэша для администраторов
        if self.request.user.is_staff:
            context['cache_stats'] = math_status_cache.get_cache_stats()
        
        return context

# Остальные классы остаются без изменений
class TaskDetailView(DetailView):
    model = Task
    template_name = 'tasks/detail.html'
    context_object_name = 'task'
    
    def get_queryset(self):
        return Task.objects.select_related('topic', 'subtopic').prefetch_related('images')

class TaskCreateView(CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Задание успешно создано!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Ошибка при создании задания. Проверьте введённые данные.')
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)

class TaskUpdateView(UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Задание успешно обновлено!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Ошибка при обновлении задания. Проверьте введённые данные.')
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)

class TaskDeleteView(DeleteView):
    model = Task
    template_name = 'tasks/confirm_delete.html'
    context_object_name = 'task'
    success_url = reverse_lazy('tasks:list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Задание успешно удалено!')
        return super().delete(request, *args, **kwargs)

def load_subtopics(request):
    """AJAX для загрузки подтем при выборе темы"""
    topic_id = request.GET.get('topic_id')
    
    if not topic_id:
        return JsonResponse({'subtopics': []})
    
    try:
        topic = Topic.objects.get(pk=topic_id)
        subtopics = topic.subtopics.all().order_by('order', 'name')
        
        data = {
            'subtopics': [
                {'id': subtopic.id, 'name': subtopic.name} 
                for subtopic in subtopics
            ]
        }
    except Topic.DoesNotExist:
        data = {'subtopics': []}
    
    return JsonResponse(data)

def load_codifier_elements(request):
    """AJAX для загрузки элементов кодификатора при выборе предмета"""
    subject = request.GET.get('subject')
    category = request.GET.get('category')
    
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

# НОВЫЕ VIEW для управления кэшем
def refresh_math_cache(request):
    """Принудительное обновление кэша формул (только для администраторов)"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)
    
    try:
        stats = math_status_cache.refresh_cache()
        return JsonResponse({
            'success': True,
            'message': 'Кэш успешно обновлен',
            'stats': {
                'with_math': len(stats['with_math']),
                'with_errors': len(stats['with_errors']),
                'with_warnings': len(stats['with_warnings']),
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
