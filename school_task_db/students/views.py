from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import Http404
from django.views import View

from infrastructure.container import container
from .models import Student, StudentGroup
from .forms import StudentForm, StudentGroupForm


class StudentListView(ListView):
    model = Student
    template_name = 'students/list.html'
    context_object_name = 'students'
    paginate_by = 50

    def get_queryset(self):
        return container.get_student_list_use_case().execute().students


class StudentDetailView(TemplateView):
    template_name = 'students/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        detail = container.get_student_detail_use_case().execute(
            str(self.kwargs['pk']),
        )
        student = detail.student
        if student is None:
            raise Http404('Ученик не найден')

        from reports import plotly_utils
        profile = container.get_student_profile_use_case().execute(str(student.pk))

        context['student'] = student
        context['object'] = student
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

    def get_queryset(self):
        return container.get_student_group_list_use_case().execute().student_groups


class StudentGroupDetailView(TemplateView):
    template_name = 'students/group_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        detail = container.get_student_group_detail_use_case().execute(
            str(self.kwargs['pk']),
        )
        if detail.student_group is None:
            raise Http404('Класс не найден')
        context['studentgroup'] = detail.student_group
        context['object'] = detail.student_group
        return context


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
        from infrastructure.container import container

        remedial_data = container.get_student_remedial_work_use_case().execute(
            str(student.pk),
        )
        if remedial_data.no_data:
            context['no_data'] = True
            return context

        context['remedial_groups'] = remedial_data.remedial_groups
        context['weak_topics'] = remedial_data.weak_topics
        context['total_available'] = remedial_data.total_available
        context['done_count'] = remedial_data.done_count
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        student = self.object
        from core_logic.use_cases.create_student_remedial_variant import (
            CreateStudentRemedialVariantRequest,
        )
        from infrastructure.container import container

        max_tasks = int(request.POST.get('max_tasks', 10))
        selected_groups = request.POST.getlist('groups')

        result = container.create_student_remedial_variant_use_case().execute(
            CreateStudentRemedialVariantRequest(
                student_id=str(student.pk),
                max_tasks=max_tasks,
                selected_group_ids=selected_groups,
            )
        )

        if not result.success:
            messages.warning(request, result.message)
            return redirect('students:detail', pk=student.pk)

        messages.success(request, result.message)
        return redirect('works:variant-detail', pk=result.variant_id)

class RemedialWizardView(View):
    """Wizard: работа над ошибками для класса"""

    def get(self, request):
        """Step 1: выбор класса и параметров"""
        from infrastructure.container import container

        start_data = container.get_remedial_wizard_start_use_case().execute()

        context = {
            'groups': start_data.groups,
            'limit_choices': start_data.limit_choices,
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
        from core_logic.use_cases.get_remedial_wizard_preview import (
            RemedialWizardPreviewRequest,
        )
        from infrastructure.container import container

        group_id = request.POST.get('group_id')
        threshold = int(request.POST.get('threshold', 70))
        limit_type = request.POST.get('limit_type', 'tasks')
        limit_value = int(request.POST.get('limit_value', 10))
        work_name = request.POST.get('work_name', 'Работа над ошибками')

        preview_data = container.get_remedial_wizard_preview_use_case().execute(
            RemedialWizardPreviewRequest(
                group_id=group_id,
                threshold=threshold,
                limit_type=limit_type,
                limit_value=limit_value,
                work_name=work_name,
            )
        )
        if preview_data.status == 'not_found':
            raise Http404("Класс не найден")

        context = {
            'group': preview_data.group,
            'preview': preview_data.preview,
            'threshold': preview_data.threshold,
            'limit_type': preview_data.limit_type,
            'limit_value': preview_data.limit_value,
            'work_name': preview_data.work_name,
            'students_with_tasks': preview_data.students_with_tasks,
            'total_tasks': preview_data.total_tasks,
        }
        return render(request, 'students/remedial_wizard_step2.html', context)

    def _step3_create(self, request):
        """Step 3: создание Work + Variants + Event"""
        from core_logic.use_cases.create_remedial_wizard_work import (
            CreateRemedialWizardWorkRequest,
        )
        from infrastructure.container import container

        group_id = request.POST.get('group_id')
        work_name = request.POST.get('work_name', 'Работа над ошибками')
        create_event = request.POST.get('create_event') == '1'
        event_date = request.POST.get('event_date', '')

        selected_students = request.POST.getlist('selected_students')
        student_tasks = {}
        for student_id in selected_students:
            task_ids_str = request.POST.get(f'task_ids_{student_id}', '')
            if task_ids_str:
                student_tasks[student_id] = task_ids_str.split(',')

        result = container.create_remedial_wizard_work_use_case().execute(
            CreateRemedialWizardWorkRequest(
                group_id=group_id,
                selected_student_ids=selected_students,
                student_task_ids=student_tasks,
                work_name=work_name,
                create_event=create_event,
                event_date=event_date,
            )
        )

        if not result.success:
            if result.status == 'group_not_found':
                raise Http404("Класс не найден")
            messages.warning(request, result.message)
            return redirect('students:remedial-wizard')

        messages.success(request, result.message)
        if result.event_id:
            return redirect('events:detail', pk=result.event_id)
        return redirect('works:detail', pk=result.work_id)

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

        sheet_data = container.get_remedial_sheet_data_use_case().execute(
            str(variant_pk),
        )
        if sheet_data.status == 'not_found':
            raise Http404(sheet_data.message)
        if sheet_data.status == 'missing_source':
            messages.error(request, sheet_data.message)
            if sheet_data.redirect_work_id:
                return redirect('works:detail', pk=sheet_data.redirect_work_id)
            return redirect('works:variant-detail', pk=variant_pk)
        if sheet_data.status == 'missing_student':
            messages.error(request, sheet_data.message)
            return redirect('works:variant-detail', pk=variant_pk)

        context = {
            'variant': sheet_data.variant,
            'student': sheet_data.student,
            'source_work': sheet_data.source_work,
            'original_tasks': sheet_data.original_tasks,
            'new_tasks': sheet_data.new_tasks,
            'mark': sheet_data.mark,
        }
        return render(request, 'students/remedial_solutions.html', context)
