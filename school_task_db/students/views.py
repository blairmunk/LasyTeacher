from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Avg, Count, F, Q
from django.views import View
from django.shortcuts import get_object_or_404
from django.utils import timezone as tz
from django.db.models import Count


from tasks.models import Task
from works.models import Work, Variant, VariantTask
from task_groups.models import AnalogGroup, TaskGroup

from .models import Student, StudentGroup, StudentTaskLog
from .forms import StudentForm, StudentGroupForm
from events.models import Event, EventParticipation



class StudentListView(ListView):
    model = Student
    template_name = 'students/list.html'
    context_object_name = 'students'
    paginate_by = 50


class StudentDetailView(DetailView):
    model = Student
    template_name = 'students/detail.html'
    context_object_name = 'student'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.object

        from infrastructure.container import container
        from reports import plotly_utils
        profile = container.get_student_profile_use_case().execute(str(student.pk))

        context['student_groups'] = profile.student_groups
        context['participations_data'] = profile.participations_data
        context['stats'] = profile.stats
        context['group_scores'] = profile.group_scores
        context['task_log_stats'] = profile.task_log_stats
        context['heatmap_groups'] = profile.heatmap_groups
        context['heatmap_topics'] = profile.heatmap_topics
        context['heatmap_difficulty'] = profile.heatmap_difficulty
        context['recent_task_log'] = profile.recent_task_log

        if profile.group_scores:
            # Для Plotly мини-heatmap
            group_names = [g['name'] for g in profile.group_scores]

            heatmap_chart = plotly_utils.heatmap_config(
                students=[student.get_short_name()],
                groups=group_names,
                matrix=[[g['avg'] for g in profile.group_scores]],
                title='Успеваемость по темам',
            )
            # Уменьшаем высоту для мини-версии
            heatmap_chart['layout']['height'] = 150
            heatmap_chart['layout']['margin'] = {
                'l': 250, 't': 50, 'r': 80, 'b': 30
            }
            context['mini_heatmap_json'] = plotly_utils.to_json(heatmap_chart)

        # --- График динамики ---
        if profile.scores_timeline:
            scores_timeline = list(reversed(profile.scores_timeline))
            dates = [s.date for s in scores_timeline]
            scores_vals = [s.score for s in scores_timeline]
            hover_texts = [
                f"{s.work}<br>Оценка: <b>{s.score}</b>"
                for s in scores_timeline
            ]

            dynamics_chart = {
                'data': [{
                    'type': 'scatter',
                    'mode': 'lines+markers',
                    'x': dates,
                    'y': scores_vals,
                    'text': hover_texts,
                    'hoverinfo': 'text',
                    'line': {'color': 'rgba(13, 110, 253, 0.75)', 'width': 2},
                    'marker': {
                        'size': 10,
                        'color': [
                            'rgba(220,53,69,0.7)' if s <= 2
                            else 'rgba(255,193,7,0.7)' if s <= 3
                            else 'rgba(40,167,69,0.7)' if s <= 4
                            else 'rgba(13,110,253,0.7)'
                            for s in scores_vals
                        ],
                    },
                    'fill': 'tozeroy',
                    'fillcolor': 'rgba(13, 110, 253, 0.05)',
                }],
                'layout': {
                    'title': 'Динамика оценок',
                    'yaxis': {
                        'range': [1.5, 5.5],
                        'tickvals': [2, 3, 4, 5],
                        'gridcolor': 'rgba(0,0,0,0.1)',
                    },
                    'xaxis': {'tickangle': -45},
                    'margin': {'l': 40, 't': 40, 'r': 20, 'b': 80},
                    'height': 280,
                    'paper_bgcolor': '#fff',
                    'plot_bgcolor': '#f8f9fa',
                    'shapes': [{
                        'type': 'line',
                        'x0': dates[0], 'x1': dates[-1],
                        'y0': profile.stats['avg_score'],
                        'y1': profile.stats['avg_score'],
                        'line': {
                            'color': 'rgba(255,0,0,0.3)',
                            'width': 1, 'dash': 'dash'
                        },
                    }] if len(dates) > 1 else [],
                },
                'config': {'responsive': True, 'displayModeBar': False},
            }
            context['dynamics_chart_json'] = plotly_utils.to_json(dynamics_chart)

        # --- Распределение оценок ---
        if profile.stats['graded_works'] > 0:
            context['score_chart_json'] = plotly_utils.to_json(
                plotly_utils.score_distribution_config(
                    profile.stats['score_counts'],
                    title='Распределение оценок',
                )
            )

        return context


class StudentCreateView(CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/form.html'
    success_url = reverse_lazy('students:list')

    def form_valid(self, form):
        messages.success(self.request, 'Ученик успешно добавлен!')
        return super().form_valid(form)


class StudentUpdateView(UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/form.html'
    success_url = reverse_lazy('students:list')

    def form_valid(self, form):
        messages.success(self.request, 'Данные ученика обновлены!')
        return super().form_valid(form)


class StudentGroupListView(ListView):
    model = StudentGroup
    template_name = 'students/group_list.html'
    context_object_name = 'student_groups'


class StudentGroupDetailView(DetailView):
    model = StudentGroup
    template_name = 'students/group_detail.html'
    context_object_name = 'studentgroup'


class StudentGroupCreateView(CreateView):
    model = StudentGroup
    form_class = StudentGroupForm
    template_name = 'students/group_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Класс успешно создан!')
        return super().form_valid(form)


class StudentGroupUpdateView(UpdateView):
    model = StudentGroup
    form_class = StudentGroupForm
    template_name = 'students/group_form.html'

    def form_valid(self, form):
        messages.success(self.request, 'Класс успешно обновлен!')
        return super().form_valid(form)

class RemedialWorkView(DetailView):
    """Работа над ошибками: анализ + генерация варианта"""
    model = Student
    template_name = 'students/remedial.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        student = self.object

        task_logs = StudentTaskLog.objects.filter(student=student)
        if not task_logs.exists():
            context['no_data'] = True
            return context

        # 1. Группы с ошибками: avg < 70%
        weak_groups = task_logs.exclude(
            analog_group__isnull=True
        ).values(
            'analog_group', 'analog_group__name'
        ).annotate(
            total=Count('id'),
            correct=Count('id', filter=Q(is_correct=True)),
            wrong=Count('id', filter=Q(is_correct=False)),
            avg_pct=Avg('percentage'),
        ).filter(avg_pct__lt=70).order_by('avg_pct')

        # 2. Все задания, которые ученик уже выполнял
        done_task_ids = set(
            task_logs.values_list('task_id', flat=True)
        )

        # 3. Для каждой слабой группы — доступные невыполненные задания
        remedial_groups = []
        total_available = 0

        for wg in weak_groups:
            group_id = wg['analog_group']
            group = AnalogGroup.objects.get(pk=group_id)

            # Задания из группы, которые ученик ещё не делал
            group_task_ids = set(
                TaskGroup.objects.filter(group=group).values_list('task_id', flat=True)
            )
            available_ids = group_task_ids - done_task_ids
            available_tasks = Task.objects.filter(id__in=available_ids)

            remedial_groups.append({
                'group': group,
                'avg_pct': round(wg['avg_pct'] or 0, 1),
                'total_done': wg['total'],
                'correct': wg['correct'],
                'wrong': wg['wrong'],
                'available_count': len(available_ids),
                'available_tasks': available_tasks[:5],  # Превью
                'group_total': len(group_task_ids),
            })
            total_available += len(available_ids)

        # 4. Слабые темы (без группы)
        weak_topics = task_logs.exclude(
            topic__isnull=True
        ).values(
            'topic', 'topic__name'
        ).annotate(
            total=Count('id'),
            correct=Count('id', filter=Q(is_correct=True)),
            avg_pct=Avg('percentage'),
        ).filter(avg_pct__lt=70).order_by('avg_pct')[:10]

        context['remedial_groups'] = remedial_groups
        context['weak_topics'] = weak_topics
        context['total_available'] = total_available
        context['done_count'] = len(done_task_ids)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        student = self.object

        # Параметры
        max_tasks = int(request.POST.get('max_tasks', 10))
        selected_groups = request.POST.getlist('groups')

        task_logs = StudentTaskLog.objects.filter(student=student)
        done_task_ids = set(task_logs.values_list('task_id', flat=True))

        # Собираем задания
        tasks_to_add = []

        if selected_groups:
            group_ids = selected_groups
        else:
            # Все слабые группы
            group_ids = task_logs.exclude(
                analog_group__isnull=True
            ).values('analog_group').annotate(
                avg_pct=Avg('percentage')
            ).filter(avg_pct__lt=70).values_list('analog_group', flat=True)

        for group_id in group_ids:
            if len(tasks_to_add) >= max_tasks:
                break

            group_task_ids = set(
                TaskGroup.objects.filter(group_id=group_id).values_list('task_id', flat=True)
            )
            available_ids = list(group_task_ids - done_task_ids)

            if available_ids:
                import random
                random.shuffle(available_ids)
                # Берём 1-2 задания из каждой группы
                take = min(2, max_tasks - len(tasks_to_add), len(available_ids))
                tasks_to_add.extend(available_ids[:take])

        if not tasks_to_add:
            messages.warning(request, 'Нет доступных заданий для работы над ошибками.')
            return redirect('students:detail', pk=student.pk)

        # Собираем задания как список объектов
        tasks_list = list(Task.objects.filter(id__in=tasks_to_add))
        if not tasks_list:
            messages.warning(request, 'Нет доступных заданий для работы над ошибками.')
            return redirect('students:detail', pk=student.pk)

        # Суммарный балл = сумма сложностей
        total_score = sum(t.difficulty or 1 for t in tasks_list)

        variant = Variant.objects.create(
            work=None,
            number=1,
            work_name_snapshot=f'Работа над ошибками — {student.get_short_name()}',
            max_score_snapshot=total_score,
            variant_type='remedial',
            assigned_student=student,
        )

        for i, task in enumerate(tasks_list, 1):
            VariantTask.objects.create(
                variant=variant,
                task=task,
                order=i,
                weight=float(task.difficulty or 1),
                max_points=task.difficulty or 1,
            )

        messages.success(
            request,
            f'Создан вариант «Работа над ошибками» для {student.get_short_name()}: '
            f'{len(tasks_list)} заданий, макс. балл: {total_score}'
        )
        return redirect('works:variant-detail', pk=variant.pk)

class RemedialWizardView(View):
    """Wizard: работа над ошибками для класса"""

    def get(self, request):
        """Step 1: выбор класса и параметров"""
        groups = StudentGroup.objects.select_related('academic_year').order_by('name')

        # Лимиты
        LIMIT_CHOICES = [
            ('tasks', 'По количеству заданий'),
            ('weight', 'По суммарному весу (≈ сложность)'),
            ('time', 'По времени выполнения (мин)'),
        ]

        context = {
            'groups': groups,
            'limit_choices': LIMIT_CHOICES,
        }
        return render(request, 'students/remedial_wizard_step1.html', context)

    def post(self, request):
        step = request.POST.get('step', '2')

        if step == '2':
            return self._step2_preview(request)
        elif step == '3':
            return self._step3_create(request)

        return redirect('students:remedial-wizard')

    def _step2_preview(self, request):
        """Step 2: анализ и превью с дифференциацией по уровню"""
        group_id = request.POST.get('group_id')
        threshold = int(request.POST.get('threshold', 70))
        limit_type = request.POST.get('limit_type', 'tasks')
        limit_value = int(request.POST.get('limit_value', 10))
        work_name = request.POST.get('work_name', 'Работа над ошибками')

        group = get_object_or_404(StudentGroup, pk=group_id)
        students = group.get_active_students()

        preview = []
        for student in students:
            task_logs = StudentTaskLog.objects.filter(student=student)
            if not task_logs.exists():
                preview.append({
                    'student': student,
                    'student_level': 'unknown',
                    'student_level_label': '—',
                    'overall_avg': 0,
                    'weak_groups': 0,
                    'tasks_count': 0,
                    'total_weight': 0,
                    'est_time': 0,
                    'available': False,
                    'reason': 'Нет данных',
                })
                continue

            done_task_ids = set(task_logs.values_list('task_id', flat=True))

            # Общий средний % ученика
            overall_avg = task_logs.aggregate(avg=Avg('percentage'))['avg'] or 0

            # Определяем уровень
            if overall_avg < 50:
                student_level = 'weak'
            elif overall_avg < 80:
                student_level = 'medium'
            else:
                student_level = 'strong'

            # Слабые группы (ниже порога)
            weak_group_ids = list(
                task_logs.exclude(analog_group__isnull=True)
                .values('analog_group')
                .annotate(avg_pct=Avg('percentage'))
                .filter(avg_pct__lt=threshold)
                .values_list('analog_group', flat=True)
            )

            # Все группы ученика
            all_group_ids = list(
                task_logs.exclude(analog_group__isnull=True)
                .values_list('analog_group', flat=True)
                .distinct()
            )

            # === ДИФФЕРЕНЦИРОВАННЫЙ ПОДБОР ===
            candidate_tasks = []

            if student_level == 'weak':
                # Слабый: из слабых групп задания ≤ номинальной сложности (закрепление)
                for gid in weak_group_ids:
                    try:
                        group_obj = AnalogGroup.objects.get(pk=gid)
                        group_diff = group_obj.effective_difficulty
                    except AnalogGroup.DoesNotExist:
                        group_diff = 3

                    group_task_ids = set(
                        TaskGroup.objects.filter(group_id=gid)
                        .values_list('task_id', flat=True)
                    )
                    available_ids = group_task_ids - done_task_ids
                    if available_ids:
                        tasks_qs = Task.objects.filter(
                            id__in=available_ids,
                            difficulty__lte=group_diff
                        ).values('id', 'difficulty', 'estimated_time')
                        for t in tasks_qs:
                            candidate_tasks.append({
                                'id': t['id'],
                                'difficulty': t['difficulty'] or 1,
                                'estimated_time': t['estimated_time'] or 0,
                                'group_id': gid,
                            })

            elif student_level == 'medium':
                # Средний: из слабых групп задания ≈ номинальной сложности
                for gid in weak_group_ids:
                    try:
                        group_obj = AnalogGroup.objects.get(pk=gid)
                        group_diff = group_obj.effective_difficulty
                    except AnalogGroup.DoesNotExist:
                        group_diff = 3

                    group_task_ids = set(
                        TaskGroup.objects.filter(group_id=gid)
                        .values_list('task_id', flat=True)
                    )
                    available_ids = group_task_ids - done_task_ids
                    if available_ids:
                        # Точная сложность
                        tasks_qs = Task.objects.filter(
                            id__in=available_ids,
                            difficulty=group_diff
                        ).values('id', 'difficulty', 'estimated_time')
                        found = list(tasks_qs)

                        # Fallback: ±1
                        if not found:
                            tasks_qs = Task.objects.filter(
                                id__in=available_ids,
                                difficulty__gte=max(1, group_diff - 1),
                                difficulty__lte=group_diff + 1,
                            ).values('id', 'difficulty', 'estimated_time')
                            found = list(tasks_qs)

                        for t in found:
                            candidate_tasks.append({
                                'id': t['id'],
                                'difficulty': t['difficulty'] or 1,
                                'estimated_time': t['estimated_time'] or 0,
                                'group_id': gid,
                            })

            else:
                # Сильный: из ВСЕХ групп задания ВЫШЕ номинальной сложности
                for gid in all_group_ids:
                    try:
                        group_obj = AnalogGroup.objects.get(pk=gid)
                        group_diff = group_obj.effective_difficulty
                    except AnalogGroup.DoesNotExist:
                        group_diff = 3

                    group_task_ids = set(
                        TaskGroup.objects.filter(group_id=gid)
                        .values_list('task_id', flat=True)
                    )
                    available_ids = group_task_ids - done_task_ids
                    if available_ids:
                        tasks_qs = Task.objects.filter(
                            id__in=available_ids,
                            difficulty__gt=group_diff
                        ).values('id', 'difficulty', 'estimated_time')
                        for t in tasks_qs:
                            candidate_tasks.append({
                                'id': t['id'],
                                'difficulty': t['difficulty'] or 1,
                                'estimated_time': t['estimated_time'] or 0,
                                'group_id': gid,
                            })

                # Fallback: сложность ≥ 4 из любых групп
                if not candidate_tasks:
                    all_group_task_ids = set(
                        TaskGroup.objects.filter(group_id__in=all_group_ids)
                        .values_list('task_id', flat=True)
                    )
                    tasks_qs = Task.objects.filter(
                        id__in=all_group_task_ids - done_task_ids,
                        difficulty__gte=4
                    ).values('id', 'difficulty', 'estimated_time')
                    for t in tasks_qs:
                        candidate_tasks.append({
                            'id': t['id'],
                            'difficulty': t['difficulty'] or 1,
                            'estimated_time': t['estimated_time'] or 0,
                            'group_id': None,
                        })

            # === ОТБОР ПО ЛИМИТУ ===
            import random
            random.shuffle(candidate_tasks)
            selected = []
            running_total = 0

            for ct in candidate_tasks:
                if limit_type == 'tasks' and len(selected) >= limit_value:
                    break
                elif limit_type == 'weight' and running_total >= limit_value:
                    break
                elif limit_type == 'time' and running_total >= limit_value:
                    break

                selected.append(ct)
                if limit_type == 'tasks':
                    running_total = len(selected)
                elif limit_type == 'weight':
                    running_total += ct['difficulty']
                elif limit_type == 'time':
                    running_total += ct['estimated_time'] or ct['difficulty'] * 3

            total_weight = sum(t['difficulty'] for t in selected)
            est_time = sum((t['estimated_time'] or t['difficulty'] * 3) for t in selected)

            level_labels = {
                'weak': 'Слабый',
                'medium': 'Средний',
                'strong': 'Сильный',
            }

            preview.append({
                'student': student,
                'student_level': student_level,
                'student_level_label': level_labels[student_level],
                'overall_avg': round(overall_avg, 1),
                'weak_groups': len(weak_group_ids),
                'tasks_count': len(selected),
                'total_weight': total_weight,
                'est_time': est_time,
                'available': len(selected) > 0,
                'reason': '' if selected else 'Нет слабых групп или все задания решены',
                'task_ids': [t['id'] for t in selected],
            })

        context = {
            'group': group,
            'preview': preview,
            'threshold': threshold,
            'limit_type': limit_type,
            'limit_value': limit_value,
            'work_name': work_name,
            'students_with_tasks': sum(1 for p in preview if p['available']),
            'total_tasks': sum(p['tasks_count'] for p in preview),
        }
        return render(request, 'students/remedial_wizard_step2.html', context)

    def _step3_create(self, request):
        """Step 3: создание Work + Variants + Event"""
        from events.models import Event, EventParticipation

        group_id = request.POST.get('group_id')
        work_name = request.POST.get('work_name', 'Работа над ошибками')
        create_event = request.POST.get('create_event') == '1'
        event_date = request.POST.get('event_date', '')

        group = get_object_or_404(StudentGroup, pk=group_id)
        selected_students = request.POST.getlist('selected_students')

        if not selected_students:
            messages.warning(request, 'Не выбрано ни одного ученика.')
            return redirect('students:remedial-wizard')

        # Собираем task_ids для каждого ученика
        student_tasks = {}
        for student_id in selected_students:
            task_ids_str = request.POST.get(f'task_ids_{student_id}', '')
            if task_ids_str:
                student_tasks[student_id] = task_ids_str.split(',')

        if not student_tasks:
            messages.warning(request, 'Нет заданий для выбранных учеников.')
            return redirect('students:remedial-wizard')

        # Создаём Work
        max_weight = max(
            sum(
                (Task.objects.get(pk=tid).difficulty or 1) for tid in tids
            ) for tids in student_tasks.values()
        ) if student_tasks else 0

        work = Work.objects.create(
            name=work_name,
            work_type='remedial',
            max_score=max_weight,
            variant_counter=len(student_tasks),
        )

        # Создаём Event (если нужно)
        event = None
        if create_event:
            import datetime
            from django.utils import timezone as tz

            if event_date:
                try:
                    date_obj = datetime.datetime.strptime(event_date, '%Y-%m-%d').date()
                except ValueError:
                    date_obj = tz.now().date()
            else:
                date_obj = tz.now().date()

            event = Event.objects.create(
                name=work_name,
                work=work,
                planned_date=tz.make_aware(
                    datetime.datetime.combine(date_obj, datetime.time(9, 0))
                ),
                status='planned',
                description=f'Работа над ошибками для {group.name}',
            )


        # Создаём варианты
        variants_created = 0
        for i, (student_id, task_ids) in enumerate(student_tasks.items(), 1):
            student = Student.objects.get(pk=student_id)
            tasks_list = list(Task.objects.filter(id__in=task_ids))
            total_score = sum(t.difficulty or 1 for t in tasks_list)

            variant = Variant.objects.create(
                work=work,
                number=i,
                work_name_snapshot=work_name,
                max_score_snapshot=total_score,
                variant_type='remedial',
                assigned_student=student,
            )

            for j, task in enumerate(tasks_list, 1):
                VariantTask.objects.create(
                    variant=variant,
                    task=task,
                    order=j,
                    weight=float(task.difficulty or 1),
                    max_points=task.difficulty or 1,
                )

            # EventParticipation
            if event:
                EventParticipation.objects.create(
                    event=event,
                    student=student,
                    variant=variant,
                    status='assigned',
                )

            variants_created += 1

        msg = f'Создана работа «{work_name}» с {variants_created} вариантами.'
        if event:
            msg += f' Событие на {event_date} создано.'
        messages.success(request, msg)

        if event:
            return redirect('events:detail', pk=event.pk)
        return redirect('works:detail', pk=work.pk)

class RemedialFromEventView(View):
    """Работа над ошибками для конкретного события/работы"""

    def get(self, request, event_pk):
        """Показываем анализ: кто плохо написал"""
        from django.http import Http404
        from infrastructure.container import container

        result = container.get_remedial_event_preview_use_case().execute(
            str(event_pk)
        )
        if not result.success:
            raise Http404(result.message)

        return render(request, 'students/remedial_from_event.html', {
            'event': result.event,
            'work': result.work,
            'analysis': result.analysis,
            'weak_students': result.weak_students,
        })

    def post(self, request, event_pk):
        """Создаём работу над ошибками из результатов события"""
        from core_logic.use_cases.create_remedial_from_event import (
            RemedialFromEventRequest,
        )
        from infrastructure.container import container

        result = container.create_remedial_from_event_use_case().execute(
            RemedialFromEventRequest(
                event_id=str(event_pk),
                selected_student_ids=request.POST.getlist('selected_students'),
                work_name=request.POST.get('work_name', ''),
                create_event=request.POST.get('create_event') == '1',
                event_date=request.POST.get('event_date', ''),
            )
        )

        if not result.success:
            messages.warning(request, result.message)
            return redirect('students:remedial-from-event', event_pk=event_pk)

        messages.success(request, result.message)
        if result.event_id:
            return redirect('events:detail', pk=result.event_id)
        return redirect('works:detail', pk=result.work_id)

class RemedialSolutionsView(View):
    """Страница решений: показывает оригинальные задания КР + их решения"""

    def get(self, request, variant_pk):
        from infrastructure.container import container
        from works.models import Variant

        variant = get_object_or_404(Variant, pk=variant_pk)

        if not variant.source_work:
            messages.error(request, 'У этого варианта нет исходной работы.')
            if variant.work:
                return redirect('works:detail', pk=variant.work.pk)
            return redirect('works:variant-detail', pk=variant.pk)

        student = variant.assigned_student
        if not student:
            messages.error(
                request,
                'Для разбора ошибок нужно знать ученика, которому назначен вариант.',
            )
            return redirect('works:variant-detail', pk=variant.pk)

        sheet_data = container.get_remedial_sheet_data_use_case().execute(
            str(variant.pk),
        )

        context = {
            'variant': sheet_data.variant,
            'student': sheet_data.student,
            'source_work': sheet_data.source_work,
            'original_tasks': sheet_data.original_tasks,
            'new_tasks': sheet_data.new_tasks,
            'mark': sheet_data.mark,
        }
        return render(request, 'students/remedial_solutions.html', context)
