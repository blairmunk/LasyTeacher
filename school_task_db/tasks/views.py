from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from .forms import TaskForm, TaskImageFormSet
from .models import Task, TaskImage
from .utils import math_status_cache
from curriculum.models import Topic, SubTopic
from document_generator.utils.formula_utils import formula_processor

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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # ИСПРАВЛЕНО: Для создания используем пустой formset
        if self.request.POST:
            context['image_formset'] = TaskImageFormSet(
                self.request.POST, 
                self.request.FILES,
                prefix='images'
            )
        else:
            context['image_formset'] = TaskImageFormSet(
                prefix='images'
            )
        
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        image_formset = context['image_formset']
        
        if image_formset.is_valid():
            # Сначала сохраняем задание
            self.object = form.save()
            
            # Затем сохраняем изображения с привязкой к заданию
            image_formset.instance = self.object  # ВАЖНО: устанавливаем instance
            image_formset.save()
            
            # Подсчитываем созданные изображения
            created_images = len([img for img in image_formset.forms if img.instance.pk and not img.cleaned_data.get('DELETE', False)])
            
            messages.success(self.request, f'Задание успешно создано!')
            if created_images > 0:
                messages.info(self.request, f'Добавлено изображений: {created_images}')
            
            return redirect(self.object.get_absolute_url())
        else:
            messages.error(self.request, 'Ошибка при создании задания. Проверьте данные изображений.')
            return self.form_invalid(form)

class TaskUpdateView(UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # ИСПРАВЛЕНО: Для обновления используем instance
        if self.request.POST:
            context['image_formset'] = TaskImageFormSet(
                self.request.POST, 
                self.request.FILES,
                instance=self.object,  # ✅ Теперь это работает!
                prefix='images'
            )
        else:
            context['image_formset'] = TaskImageFormSet(
                instance=self.object,  # ✅ Теперь это работает!
                prefix='images'
            )
        
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        image_formset = context['image_formset']
        
        if image_formset.is_valid():
            # Сначала сохраняем задание
            self.object = form.save()
            
            # Сохраняем formset (instance уже установлен в get_context_data)
            saved_images = image_formset.save()
            
            # Статистика изменений
            created_images = len([img for img in saved_images if img.pk and not hasattr(img, '_created')])
            deleted_count = len(image_formset.deleted_objects)
            
            messages.success(self.request, 'Задание успешно обновлено!')
            
            if created_images > 0:
                messages.info(self.request, f'Добавлено изображений: {created_images}')
            if deleted_count > 0:
                messages.info(self.request, f'Удалено изображений: {deleted_count}')
            
            return redirect(self.object.get_absolute_url())
        else:
            messages.error(self.request, 'Ошибка при обновлении задания. Проверьте данные изображений.')
            
            # Отладочная информация в development режиме
            if settings.DEBUG:
                for i, form in enumerate(image_formset.forms):
                    if form.errors:
                        for field, errors in form.errors.items():
                            messages.error(self.request, f'Изображение {i+1}, поле {field}: {", ".join(errors)}')
                
                if image_formset.non_form_errors():
                    for error in image_formset.non_form_errors():
                        messages.error(self.request, f'Formset ошибка: {error}')
            
            return self.form_invalid(form)

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
