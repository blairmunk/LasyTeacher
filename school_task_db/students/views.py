from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Avg, Count, F, Q

from .models import Student, StudentGroup
from .forms import StudentForm, StudentGroupForm


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

        from events.models import EventParticipation, Mark
        from works.models import WorkAnalogGroup
        from reports import plotly_utils

        # Класс ученика
        groups = StudentGroup.objects.filter(students=student)
        context['student_groups'] = groups

        # Все участия с оценками
        participations = EventParticipation.objects.filter(
            student=student
        ).select_related(
            'event', 'event__work', 'event__course', 'variant'
        ).order_by('-event__planned_date')

        # Собираем данные по каждому участию
        participations_data = []
        scores_timeline = []  # для графика динамики
        total_marks = 0
        total_score_sum = 0
        absent_count = 0
        score_counts = {2: 0, 3: 0, 4: 0, 5: 0}

        for p in participations:
            mark = Mark.objects.filter(participation=p).first()
            is_absent = p.status == 'absent'

            if is_absent:
                absent_count += 1

            score = None
            if mark and mark.score:
                score = mark.score
                total_marks += 1
                total_score_sum += score
                if score in score_counts:
                    score_counts[score] += 1

                if p.event.planned_date:
                    scores_timeline.append({
                        'date': p.event.planned_date.strftime('%d.%m.%Y'),
                        'score': score,
                        'work': p.event.work.name if p.event.work else p.event.name,
                    })

            participations_data.append({
                'participation': p,
                'event': p.event,
                'work': p.event.work,
                'mark': mark,
                'score': score,
                'is_absent': is_absent,
                'variant_number': p.variant.number if p.variant else None,
            })

        context['participations_data'] = participations_data

        # Общая статистика
        avg_score = round(total_score_sum / total_marks, 2) if total_marks > 0 else 0
        total_participations = len(participations_data)
        attendance_rate = round(
            (total_participations - absent_count) / total_participations * 100, 1
        ) if total_participations > 0 else 100

        context['stats'] = {
            'total_works': total_participations,
            'graded_works': total_marks,
            'absent_count': absent_count,
            'avg_score': avg_score,
            'attendance_rate': attendance_rate,
            'score_counts': score_counts,
        }

        # --- Мини-heatmap: группы аналогов ---
        group_scores = self._build_group_scores(student)
        context['group_scores'] = group_scores

        if group_scores:
            # Для Plotly мини-heatmap
            group_names = [g['name'] for g in group_scores]
            group_avgs = [g['avg'] for g in group_scores]

            heatmap_chart = plotly_utils.heatmap_config(
                students=[student.get_short_name()],
                groups=group_names,
                matrix=[[g['avg'] for g in group_scores]],
                title='Успеваемость по темам',
            )
            # Уменьшаем высоту для мини-версии
            heatmap_chart['layout']['height'] = 150
            heatmap_chart['layout']['margin'] = {
                'l': 250, 't': 50, 'r': 80, 'b': 30
            }
            context['mini_heatmap_json'] = plotly_utils.to_json(heatmap_chart)

        # --- График динамики ---
        if scores_timeline:
            scores_timeline.reverse()
            dates = [s['date'] for s in scores_timeline]
            scores_vals = [s['score'] for s in scores_timeline]
            hover_texts = [
                f"{s['work']}<br>Оценка: <b>{s['score']}</b>"
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
                        'y0': avg_score, 'y1': avg_score,
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
        if total_marks > 0:
            context['score_chart_json'] = plotly_utils.to_json(
                plotly_utils.score_distribution_config(
                    score_counts, title='Распределение оценок'
                )
            )

        # === StudentTaskLog: детализация по заданиям ===
        from .models import StudentTaskLog

        task_logs = StudentTaskLog.objects.filter(student=student)
        log_count = task_logs.count()

        if log_count > 0:
            log_agg = task_logs.aggregate(
                avg_pct=Avg('percentage'),
                correct=Count('id', filter=Q(is_correct=True)),
                wrong=Count('id', filter=Q(is_correct=False)),
            )
            context['task_log_stats'] = {
                'total': log_count,
                'correct': log_agg['correct'],
                'wrong': log_agg['wrong'],
                'avg_pct': round(log_agg['avg_pct'] or 0, 1),
            }

            def _build_cells(qs):
                cells = []
                for row in qs:
                    pct = row['avg_pct'] or 0
                    if pct == 0:
                        level = 0
                    elif pct < 30:
                        level = 1
                    elif pct < 55:
                        level = 2
                    elif pct < 80:
                        level = 3
                    else:
                        level = 4
                    cells.append({
                        'name': row['name'],
                        'total': row['total'],
                        'correct': row['correct'],
                        'avg_pct': round(pct, 1),
                        'level': level,
                    })
                return cells

            # По группам аналогов
            group_qs = task_logs.exclude(
                analog_group__isnull=True
            ).values(
                name=F('analog_group__name')
            ).annotate(
                total=Count('id'),
                correct=Count('id', filter=Q(is_correct=True)),
                avg_pct=Avg('percentage'),
            ).order_by('-avg_pct')
            context['heatmap_groups'] = _build_cells(group_qs)

            # По темам
            topic_qs = task_logs.exclude(
                topic__isnull=True
            ).values(
                name=F('topic__name')
            ).annotate(
                total=Count('id'),
                correct=Count('id', filter=Q(is_correct=True)),
                avg_pct=Avg('percentage'),
            ).order_by('-avg_pct')
            context['heatmap_topics'] = _build_cells(topic_qs)

            # По сложности
            diff_qs = task_logs.exclude(
                difficulty__isnull=True
            ).values(
                'difficulty'
            ).annotate(
                total=Count('id'),
                correct=Count('id', filter=Q(is_correct=True)),
                avg_pct=Avg('percentage'),
            ).order_by('difficulty')
            diff_cells = []
            for row in diff_qs:
                pct = row['avg_pct'] or 0
                level = 0 if pct == 0 else 1 if pct < 30 else 2 if pct < 55 else 3 if pct < 80 else 4
                diff_cells.append({
                    'name': f"Сложность {row['difficulty']}",
                    'total': row['total'],
                    'correct': row['correct'],
                    'avg_pct': round(pct, 1),
                    'level': level,
                })
            context['heatmap_difficulty'] = diff_cells

            # История заданий (последние 50)
            context['recent_task_log'] = task_logs.select_related(
                'task', 'event', 'topic', 'analog_group'
            ).order_by('-completed_at')[:50]

        return context

    def _build_group_scores(self, student):
        """Средний балл по группам аналогов"""
        from events.models import EventParticipation, Mark
        from works.models import WorkAnalogGroup

        marks = Mark.objects.filter(
            participation__student=student,
            score__isnull=False,
        ).select_related('participation__event')

        # work_id → [scores]
        work_scores = {}
        for mark in marks:
            work_id = mark.participation.event.work_id
            if work_id:
                if work_id not in work_scores:
                    work_scores[work_id] = []
                work_scores[work_id].append(mark.score)

        # Группы аналогов → средний балл
        ag_scores = {}
        for wag in WorkAnalogGroup.objects.filter(
            work_id__in=work_scores.keys()
        ).select_related('analog_group'):
            ag = wag.analog_group
            if ag.id not in ag_scores:
                ag_scores[ag.id] = {
                    'name': ag.name,
                    'scores': [],
                }
            ag_scores[ag.id]['scores'].extend(work_scores[wag.work_id])

        result = []
        for ag_id, data in ag_scores.items():
            scores = data['scores']
            avg = round(sum(scores) / len(scores), 2) if scores else None
            result.append({
                'name': data['name'],
                'avg': avg,
                'count': len(scores),
                'min': min(scores) if scores else None,
                'max': max(scores) if scores else None,
            })

        result.sort(key=lambda x: x['avg'] or 0)
        return result


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
