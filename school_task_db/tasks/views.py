from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Q, Count, Exists, OuterRef
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_POST

from .forms import TaskForm, TaskImageFormSet
from .models import Task, TaskImage
from .utils import math_status_cache
from curriculum.models import Topic, SubTopic
from task_groups.models import AnalogGroup, TaskGroup
from document_generator.utils.formula_utils import formula_processor


class TaskListView(ListView):
    model = Task
    template_name = 'tasks/list.html'
    context_object_name = 'tasks'
    paginate_by = 20

    def get_queryset(self):
        queryset = Task.objects.select_related('topic', 'subtopic').order_by('-created_at')

        # Аннотируем: есть ли у задания группа
        queryset = queryset.annotate(
            group_count=Count('taskgroup'),
            has_group=Exists(
                TaskGroup.objects.filter(task=OuterRef('pk'))
            ),
        )

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

        # Фильтр по подтеме
        subtopic_id = self.request.GET.get('subtopic')
        if subtopic_id:
            queryset = queryset.filter(subtopic_id=subtopic_id)

        # Фильтр по типу
        task_type = self.request.GET.get('task_type')
        if task_type:
            queryset = queryset.filter(task_type=task_type)

        # Фильтр по сложности
        difficulty = self.request.GET.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=int(difficulty))

        # Фильтр по принадлежности к группе
        group_filter = self.request.GET.get('group_filter')
        if group_filter == 'no_group':
            queryset = queryset.filter(has_group=False)
        elif group_filter == 'has_group':
            queryset = queryset.filter(has_group=True)

        # Фильтр по конкретной группе аналогов
        analog_group_id = self.request.GET.get('analog_group')
        if analog_group_id:
            queryset = queryset.filter(taskgroup__group_id=analog_group_id)

        # Фильтр по формулам
        math_filter = self.request.GET.get('math_filter')
        if math_filter == 'with_math':
            task_ids_with_math = math_status_cache.get_tasks_with_math_ids()
            queryset = queryset.filter(id__in=task_ids_with_math)
        elif math_filter == 'with_errors':
            task_ids_with_errors = math_status_cache.get_tasks_with_errors_ids()
            queryset = queryset.filter(id__in=task_ids_with_errors)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['topics'] = Topic.objects.all().order_by('section', 'name')
        context['analog_groups'] = AnalogGroup.objects.all().order_by('name')


        # Подтемы для выбранной темы
        topic_id = self.request.GET.get('topic')
        if topic_id:
            context['subtopics'] = SubTopic.objects.filter(
                topic_id=topic_id
            ).order_by('order', 'name')
        else:
            context['subtopics'] = SubTopic.objects.none()

        # Типы заданий
        try:
            from references.helpers import get_task_type_choices
            context['task_types'] = get_task_type_choices()
        except ImportError:
            context['task_types'] = [
                ('computational', 'Расчётная задача'),
                ('qualitative', 'Качественная задача'),
                ('theoretical', 'Теоретический вопрос'),
                ('test', 'Тест'),
            ]

        context['difficulties'] = [
            (1, 'Базовый'),
            (2, 'Повышенный'),
            (3, 'Высокий'),
        ]

        # Текущие фильтры
        context['current_filter'] = self.request.GET.get('math_filter', 'all')
        context['search_query'] = self.request.GET.get('search', '')
        context['current_topic'] = self.request.GET.get('topic', '')
        context['current_subtopic'] = self.request.GET.get('subtopic', '')
        context['current_task_type'] = self.request.GET.get('task_type', '')
        context['current_difficulty'] = self.request.GET.get('difficulty', '')
        context['current_group_filter'] = self.request.GET.get('group_filter', '')
        context['current_analog_group'] = self.request.GET.get('analog_group', '')

        # Статистика
        context['total_tasks'] = Task.objects.count()
        context['ungrouped_count'] = Task.objects.filter(
            ~Exists(TaskGroup.objects.filter(task=OuterRef('pk')))
        ).count()

        if self.request.user.is_staff:
            context['cache_stats'] = math_status_cache.get_cache_stats()

        return context


class TaskDetailView(DetailView):
    model = Task
    template_name = 'tasks/detail.html'
    context_object_name = 'task'

    def get_queryset(self):
        return Task.objects.select_related('topic', 'subtopic').prefetch_related('images')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Группы, в которых состоит задание
        context['task_groups'] = TaskGroup.objects.filter(
            task=self.object
        ).select_related('group')
        return context


class TaskCreateView(CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['image_formset'] = TaskImageFormSet(
                self.request.POST,
                self.request.FILES,
                prefix='images'
            )
        else:
            context['image_formset'] = TaskImageFormSet(prefix='images')
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        image_formset = context['image_formset']

        if image_formset.is_valid():
            self.object = form.save()
            image_formset.instance = self.object
            image_formset.save()

            created_images = len([
                img for img in image_formset.forms
                if img.instance.pk and not img.cleaned_data.get('DELETE', False)
            ])

            messages.success(self.request, 'Задание успешно создано!')
            if created_images > 0:
                messages.info(self.request, f'Добавлено изображений: {created_images}')

            return redirect(self.object.get_absolute_url())
        else:
            messages.error(self.request, 'Ошибка при создании задания.')
            return self.form_invalid(form)


class TaskUpdateView(UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['image_formset'] = TaskImageFormSet(
                self.request.POST,
                self.request.FILES,
                instance=self.object,
                prefix='images'
            )
        else:
            context['image_formset'] = TaskImageFormSet(
                instance=self.object,
                prefix='images'
            )
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        image_formset = context['image_formset']

        if image_formset.is_valid():
            self.object = form.save()
            saved_images = image_formset.save()

            created_images = len([img for img in saved_images if img.pk])
            deleted_count = len(image_formset.deleted_objects)

            messages.success(self.request, 'Задание успешно обновлено!')
            if created_images > 0:
                messages.info(self.request, f'Добавлено изображений: {created_images}')
            if deleted_count > 0:
                messages.info(self.request, f'Удалено изображений: {deleted_count}')

            return redirect(self.object.get_absolute_url())
        else:
            messages.error(self.request, 'Ошибка при обновлении задания.')
            return self.form_invalid(form)


class TaskDeleteView(DeleteView):
    model = Task
    template_name = 'tasks/confirm_delete.html'
    context_object_name = 'task'
    success_url = reverse_lazy('tasks:list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Задание успешно удалено!')
        return super().delete(request, *args, **kwargs)


# === AJAX endpoints ===

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
                {'id': str(s.id), 'name': s.name} for s in subtopics
            ]
        }
    except Topic.DoesNotExist:
        data = {'subtopics': []}

    return JsonResponse(data)


def load_codifier_elements(request):
    """AJAX для загрузки элементов кодификатора"""
    subject = request.GET.get('subject')
    category = request.GET.get('category')

    try:
        from references.helpers import get_subject_reference_choices
        choices = get_subject_reference_choices(subject, category)
        data = {
            'elements': [
                {'code': code, 'name': name} for code, name in choices
            ]
        }
    except ImportError:
        data = {'elements': []}

    return JsonResponse(data)


# === Bulk actions ===

@require_POST
def bulk_create_group(request):
    """Создать новую группу аналогов из выбранных заданий"""
    import json
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Невалидный JSON'}, status=400)

    task_ids = body.get('task_ids', [])
    group_name = body.get('group_name', '').strip()

    if not task_ids:
        return JsonResponse({'error': 'Не выбрано ни одного задания'}, status=400)
    if not group_name:
        return JsonResponse({'error': 'Название группы не указано'}, status=400)

    # Проверяем уникальность имени
    if AnalogGroup.objects.filter(name=group_name).exists():
        return JsonResponse({'error': 'Группа с таким названием уже существует'}, status=400)

    tasks = Task.objects.filter(pk__in=task_ids)
    if not tasks.exists():
        return JsonResponse({'error': 'Задания не найдены'}, status=400)

    group = AnalogGroup.objects.create(
        name=group_name,
        description='Создана из выбранных заданий',
    )

    created = 0
    for task in tasks:
        _, was_created = TaskGroup.objects.get_or_create(task=task, group=group)
        if was_created:
            created += 1

    return JsonResponse({
        'success': True,
        'group_id': str(group.pk),
        'group_name': group.name,
        'added': created,
        'message': f'Создана группа «{group.name}» с {created} заданиями',
    })


@require_POST
def bulk_add_to_group(request):
    """Добавить выбранные задания в существующую группу"""
    import json
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Невалидный JSON'}, status=400)

    task_ids = body.get('task_ids', [])
    group_id = body.get('group_id')

    if not task_ids:
        return JsonResponse({'error': 'Не выбрано ни одного задания'}, status=400)
    if not group_id:
        return JsonResponse({'error': 'Группа не указана'}, status=400)

    group = AnalogGroup.objects.filter(pk=group_id).first()
    if not group:
        return JsonResponse({'error': 'Группа не найдена'}, status=400)

    tasks = Task.objects.filter(pk__in=task_ids)
    added = 0
    skipped = 0
    for task in tasks:
        _, was_created = TaskGroup.objects.get_or_create(task=task, group=group)
        if was_created:
            added += 1
        else:
            skipped += 1

    return JsonResponse({
        'success': True,
        'added': added,
        'skipped': skipped,
        'message': f'Добавлено {added} заданий в «{group.name}»'
                   + (f' (пропущено {skipped} — уже в группе)' if skipped else ''),
    })


@require_POST
def bulk_remove_from_groups(request):
    """Удалить выбранные задания из всех групп"""
    import json
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Невалидный JSON'}, status=400)

    task_ids = body.get('task_ids', [])
    if not task_ids:
        return JsonResponse({'error': 'Не выбрано ни одного задания'}, status=400)

    deleted, _ = TaskGroup.objects.filter(task_id__in=task_ids).delete()

    return JsonResponse({
        'success': True,
        'removed': deleted,
        'message': f'Удалено {deleted} связей с группами',
    })

@require_POST
def bulk_create_work(request):
    """Создать работу с вариантом из выбранных заданий"""
    import json
    from works.models import Work, Variant, VariantTask

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Невалидный JSON'}, status=400)

    task_ids = body.get('task_ids', [])
    work_name = body.get('work_name', '').strip()
    work_type = body.get('work_type', 'test')

    if not task_ids:
        return JsonResponse({'error': 'Не выбрано ни одного задания'}, status=400)
    if not work_name:
        return JsonResponse({'error': 'Название работы не указано'}, status=400)

    tasks = Task.objects.filter(pk__in=task_ids)
    if not tasks.exists():
        return JsonResponse({'error': 'Задания не найдены'}, status=400)

    # Сохраняем порядок как в task_ids
    task_map = {str(t.pk): t for t in tasks}
    ordered_tasks = [task_map[tid] for tid in task_ids if tid in task_map]

    # Создаём работу
    work = Work.objects.create(
        name=work_name,
        work_type=work_type,
    )

    # Создаём вариант
    variant = Variant.objects.create(
        work=work,
        number=1,
    )
    work.variant_counter = 1
    work.save(update_fields=['variant_counter'])

    # Добавляем задания в порядке выбора
    for order, task in enumerate(ordered_tasks, 1):
        VariantTask.objects.create(
            variant=variant,
            task=task,
            order=order,
        )

    return JsonResponse({
        'success': True,
        'work_id': str(work.pk),
        'variant_id': str(variant.pk),
        'tasks_count': len(ordered_tasks),
        'redirect_url': f'/works/{work.pk}/',
        'message': f'Создана работа «{work_name}» с {len(ordered_tasks)} заданиями',
    })


def refresh_math_cache(request):
    """Принудительное обновление кэша формул"""
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
