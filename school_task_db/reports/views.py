# reports/views.py

import json
from django.urls import reverse
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from django.db.models import Count, Avg, Q
from datetime import datetime, timedelta

from . import plotly_utils

from students.models import Student, StudentGroup
from tasks.models import Task
from events.models import Mark, EventParticipation
from curriculum.models import Topic, SubTopic


class ReportsDashboardView(TemplateView):
    template_name = 'reports/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_date = datetime.now()
        
        from students.models import Student, StudentGroup
        from events.models import Event, EventParticipation, Mark
        from works.models import Work
        from curriculum.models import Course
        
        # Основная статистика
        context.update({
            'total_students': Student.objects.count(),
            'total_events': Event.objects.count(),
            'total_works': Work.objects.count(),
            'total_courses': Course.objects.count(),
        })
        
        # Статистика по отметкам
        marks = Mark.objects.all()
        context.update({
            'total_marks': marks.count(),
            'average_score': marks.aggregate(
                avg_score=Avg('score')
            )['avg_score'] or 0,
            'marks_last_month': marks.filter(
                checked_at__gte=current_date - timedelta(days=30)
            ).count(),
        })
        
        # Распределение оценок — Plotly
        score_counts = {}
        for item in marks.exclude(score__isnull=True).values('score').annotate(
            count=Count('score')
        ):
            score_counts[item['score']] = item['count']
        
        context['score_distribution'] = list(
            marks.exclude(score__isnull=True).values('score').annotate(
                count=Count('score')
            ).order_by('score')
        )
        context['score_chart_json'] = plotly_utils.to_json(
            plotly_utils.score_distribution_config(score_counts)
        )
        
        # Статистика по событиям
        context.update({
            'events_planned': Event.objects.filter(status='planned').count(),
            'events_completed': Event.objects.filter(status='completed').count(),
            'events_graded': Event.objects.filter(status='graded').count(),
        })
        
        # Активность по месяцам — Plotly
        monthly_labels = []
        monthly_values = []
        for i in range(6):
            month_start = current_date.replace(day=1) - timedelta(days=30 * i)
            month_end = month_start + timedelta(days=31)
            count = EventParticipation.objects.filter(
                event__planned_date__range=[month_start, month_end],
                status__in=['completed', 'graded']
            ).count()
            monthly_labels.append(month_start.strftime('%b %Y'))
            monthly_values.append(count)
        
        monthly_labels.reverse()
        monthly_values.reverse()
        context['activity_chart_json'] = plotly_utils.to_json(
            plotly_utils.line_chart_config(
                monthly_labels, monthly_values,
                title='Активность по месяцам'
            )
        )
        
        # Статистика по классам — Plotly
        class_stats = []
        class_names = []
        class_avg_scores = []
        class_completion = []
        
        for student_group in StudentGroup.objects.all():
            students_ids = list(
                student_group.students.values_list('id', flat=True)
            )
            participations = EventParticipation.objects.filter(
                student__id__in=students_ids
            )
            completed = participations.filter(
                status__in=['completed', 'graded']
            )
            class_marks = Mark.objects.filter(
                participation__student__id__in=students_ids,
                score__isnull=False
            )
            avg_score = class_marks.aggregate(avg=Avg('score'))['avg'] or 0
            completion_rate = round(
                (completed.count() / participations.count() * 100)
                if participations.count() > 0 else 0, 1
            )
            
            # Ссылки на heatmap — только для привязанных курсов
            heatmap_links = []
            linked_courses = student_group.courses.all()
            for c in linked_courses:
                heatmap_links.append({
                    'course_id': str(c.pk),
                    'course_name': c.name,
                    'group_id': str(student_group.pk),
                    'group_name': student_group.name,
                })
            
            stat = {
                'name': student_group.name,
                'students_count': student_group.students.count(),
                'total_participations': participations.count(),
                'completed_participations': completed.count(),
                'average_score': round(avg_score, 2) if avg_score else 0,
                'completion_rate': completion_rate,
                'id': str(student_group.id),
                'heatmap_links': heatmap_links,
            }
            class_stats.append(stat)
            class_names.append(student_group.name)
            class_avg_scores.append(round(avg_score, 2))
            class_completion.append(completion_rate)
        
        context['class_stats'] = class_stats

        context['class_chart_json'] = plotly_utils.to_json(
            plotly_utils.multi_bar_config(
                class_names,
                {
                    'Средний балл': class_avg_scores,
                    '% выполнения (÷25)': [
                        round(c / 25, 2) for c in class_completion
                    ],
                },
                title='Сравнение классов'
            )
        )
        
        # Топ учеников
        top_students = Student.objects.annotate(
            completed_works=Count(
                'eventparticipation',
                filter=Q(
                    eventparticipation__status__in=['completed', 'graded']
                )
            )
        ).order_by('-completed_works')[:10]
        context['top_students'] = top_students
        
        # Последние события
        recent_events = Event.objects.select_related(
            'work', 'course'
        ).order_by('-planned_date')[:10]
        context['recent_events'] = recent_events
        
        # События требующие внимания
        events_need_attention = Event.objects.filter(
            Q(status='reviewing') |
            Q(status='completed',
              planned_date__lt=current_date - timedelta(days=7))
        ).select_related('work')[:5]
        context['events_need_attention'] = events_need_attention
        
        # Типы работ
        work_type_stats = Work.objects.values('work_type').annotate(
            count=Count('id'), avg_duration=Avg('duration')
        ).order_by('-count')
        context['work_type_stats'] = list(work_type_stats)
        
        # Доступные курсы и классы для heatmap
        context['courses'] = Course.objects.all()
        context['student_groups'] = StudentGroup.objects.all()
        
        return context


class HeatmapLegacyView(TemplateView):
    """Тепловая карта успеваемости (старая версия, на основе Course)"""
    template_name = 'reports/heatmap.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from students.models import StudentGroup
        from curriculum.models import Course
        
        # Параметры из GET
        course_id = self.request.GET.get('course', '')
        group_id = self.request.GET.get('group', '')
        
        # Все курсы — всегда показываем
        all_courses = Course.objects.all()
        context['courses'] = all_courses
        context['selected_course'] = course_id
        context['selected_group'] = group_id
        
        # Группы: если курс выбран — только привязанные, иначе все
        selected_course_obj = None
        if course_id:
            try:
                selected_course_obj = Course.objects.get(pk=course_id)
                linked_groups = selected_course_obj.student_groups.all()
                if linked_groups.exists():
                    context['student_groups'] = linked_groups
                else:
                    context['student_groups'] = StudentGroup.objects.all()
            except (Course.DoesNotExist, ValueError):
                context['student_groups'] = StudentGroup.objects.all()
        else:
            context['student_groups'] = StudentGroup.objects.all()
        
        # Если оба параметра выбраны — строим карту
        if course_id and group_id:
            try:
                course = selected_course_obj or Course.objects.get(pk=course_id)
                group = StudentGroup.objects.get(pk=group_id)
                context['course'] = course
                context['group'] = group
                
                heatmap_data = self._build_heatmap(course, group)
                context['heatmap_data'] = heatmap_data
                
                if heatmap_data['students'] and heatmap_data['groups']:
                    chart = plotly_utils.heatmap_config(
                        students=heatmap_data['students'],
                        groups=heatmap_data['groups'],
                        matrix=heatmap_data['matrix'],
                        title=f'Успеваемость: {group.name} — {course.name}',
                    )
                    context['heatmap_json'] = plotly_utils.to_json(chart)
                    context['stats'] = self._calc_stats(heatmap_data)
                else:
                    context['error'] = 'Нет данных для построения карты'
                
            except (Course.DoesNotExist, StudentGroup.DoesNotExist, ValueError) as e:
                context['error'] = f'Курс или класс не найден: {e}'
        
        return context
    
    def _build_heatmap(self, course, group):
        """Построение матрицы оценок: студенты × группы аналогов"""
        from events.models import Event, Mark
        from works.models import WorkAnalogGroup
        from curriculum.models import CourseAssignment
        
        # Ученики класса
        students = list(
            group.students.all().order_by('last_name', 'first_name')
        )
        
        # Работы курса
        course_work_ids = list(
            CourseAssignment.objects.filter(
                course=course
            ).values_list('work_id', flat=True)
        )
        
        # Группы аналогов из работ курса
        work_ag_links = WorkAnalogGroup.objects.filter(
            work_id__in=course_work_ids
        ).select_related('analog_group').order_by('analog_group__name')
        
        ag_dict = {}
        ag_to_works = {}
        for wag in work_ag_links:
            ag = wag.analog_group
            if ag.id not in ag_dict:
                ag_dict[ag.id] = ag
                ag_to_works[ag.id] = set()
            ag_to_works[ag.id].add(wag.work_id)
        
        analog_groups = list(ag_dict.values())
        
        # События курса
        events = Event.objects.filter(
            work_id__in=course_work_ids,
            course=course,
        )
        
        # Все оценки
        student_ids = [s.id for s in students]
        marks = Mark.objects.filter(
            participation__event__in=events,
            participation__student_id__in=student_ids,
            score__isnull=False,
        ).select_related('participation', 'participation__event')
        
        sw_scores = {}
        for mark in marks:
            key = (
                mark.participation.student_id,
                mark.participation.event.work_id
            )
            if key not in sw_scores:
                sw_scores[key] = []
            sw_scores[key].append(mark.score)
        
        # Матрица
        matrix = []
        for student in students:
            row = []
            for ag in analog_groups:
                work_ids = ag_to_works.get(ag.id, set())
                scores = []
                for work_id in work_ids:
                    key = (student.id, work_id)
                    if key in sw_scores:
                        scores.extend(sw_scores[key])
                
                if scores:
                    row.append(round(sum(scores) / len(scores), 2))
                else:
                    row.append(None)
            matrix.append(row)
        
        short_names = [
            f'{s.last_name} {s.first_name[0]}.' for s in students
        ]
        group_names = [ag.name for ag in analog_groups]
        
        return {
            'students': short_names,
            'student_objects': students,
            'groups': group_names,
            'group_objects': analog_groups,
            'matrix': matrix,
        }
    
    def _calc_stats(self, heatmap_data):
        """Статистика по тепловой карте"""
        matrix = heatmap_data['matrix']
        students = heatmap_data['students']
        groups = heatmap_data['groups']
        
        student_avgs = []
        for i, row in enumerate(matrix):
            vals = [v for v in row if v is not None]
            avg = sum(vals) / len(vals) if vals else None
            student_avgs.append({
                'name': students[i],
                'avg': round(avg, 2) if avg else None,
                'count': len(vals),
            })
        
        group_avgs = []
        for j, gname in enumerate(groups):
            vals = [
                matrix[i][j] for i in range(len(students))
                if matrix[i][j] is not None
            ]
            avg = sum(vals) / len(vals) if vals else None
            group_avgs.append({
                'name': gname,
                'avg': round(avg, 2) if avg else None,
                'count': len(vals),
            })
        
        problem_zones = []
        excellent_zones = []
        for i, row in enumerate(matrix):
            for j, val in enumerate(row):
                if val is not None and val < 3:
                    problem_zones.append({
                        'student': students[i],
                        'group': groups[j],
                        'score': val,
                    })
                if val is not None and val >= 4.5:
                    excellent_zones.append({
                        'student': students[i],
                        'group': groups[j],
                        'score': val,
                    })
        
        student_avgs.sort(key=lambda x: x['avg'] or 0, reverse=True)
        group_avgs.sort(key=lambda x: x['avg'] or 0)
        
        all_vals = [v for row in matrix for v in row if v is not None]
        overall_avg = round(
            sum(all_vals) / len(all_vals), 2
        ) if all_vals else 0
        
        return {
            'student_avgs': student_avgs,
            'group_avgs': group_avgs,
            'problem_zones': problem_zones[:10],
            'excellent_zones': excellent_zones[:10],
            'overall_avg': overall_avg,
            'total_cells': len(students) * len(groups),
            'filled_cells': len(all_vals),
            'empty_cells': len(students) * len(groups) - len(all_vals),
        }

class StudentPerformanceView(TemplateView):
    """Отчет по успеваемости учеников"""
    template_name = 'reports/student_performance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from students.models import Student
        from events.models import Mark, EventParticipation
        
        students_stats = []
        high_performers_count = 0
        students_with_scores = 0
        students_with_activity = 0
        total_completion_rate = 0
        total_average_score = 0
        
        for student in Student.objects.all():
            participations = student.eventparticipation_set.all()
            completed = participations.filter(
                status__in=['completed', 'graded']
            )
            student_marks = Mark.objects.filter(
                participation__student=student, score__isnull=False
            )
            avg_score = student_marks.aggregate(
                avg=Avg('score')
            )['avg'] or 0
            completion_rate = round(
                (completed.count() / participations.count() * 100)
                if participations.count() > 0 else 0, 1
            )
            
            students_stats.append({
                'student': student,
                'total_participations': participations.count(),
                'completed_participations': completed.count(),
                'total_marks': student_marks.count(),
                'average_score': round(avg_score, 2) if avg_score else 0,
                'completion_rate': completion_rate,
                'last_activity': participations.order_by(
                    '-created_at'
                ).first()
            })
            
            if participations.count() > 0:
                total_completion_rate += completion_rate
                students_with_activity += 1
            if avg_score > 0:
                total_average_score += avg_score
                students_with_scores += 1
                if avg_score >= 4.5:
                    high_performers_count += 1
        
        students_stats.sort(
            key=lambda x: x['average_score'], reverse=True
        )
        
        context['students_stats'] = students_stats
        context['summary_stats'] = {
            'total_students': len(students_stats),
            'high_performers': high_performers_count,
            'avg_completion_rate': round(
                total_completion_rate / students_with_activity, 1
            ) if students_with_activity > 0 else 0,
            'avg_score': round(
                total_average_score / students_with_scores, 1
            ) if students_with_scores > 0 else 0,
        }
        
        return context


class WorkAnalysisView(TemplateView):
    """Анализ работ и их результатов"""
    template_name = 'reports/work_analysis.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from works.models import Work
        from events.models import Event, Mark
        
        works_analysis = []
        easy_works_count = 0
        hard_works_count = 0
        total_marks_all = 0
        
        for work in Work.objects.all():
            work_events = Event.objects.filter(work=work)
            work_marks = Mark.objects.filter(
                participation__event__work=work, score__isnull=False
            )
            avg_score = work_marks.aggregate(
                avg=Avg('score')
            )['avg'] or 0
            avg_percentage = work_marks.aggregate(
                avg=Avg('points')
            )['avg'] or 0
            score_dist = work_marks.values('score').annotate(
                count=Count('score')
            ).order_by('score')
            difficulty = self.assess_difficulty(avg_score, avg_percentage)
            
            works_analysis.append({
                'work': work,
                'events_count': work_events.count(),
                'total_marks': work_marks.count(),
                'average_score': round(avg_score, 2) if avg_score else 0,
                'average_percentage': round(
                    avg_percentage, 1
                ) if avg_percentage else 0,
                'score_distribution': list(score_dist),
                'difficulty_assessment': difficulty,
            })
            
            if difficulty == "Лёгкая":
                easy_works_count += 1
            elif difficulty in ["Сложная", "Очень сложная"]:
                hard_works_count += 1
            total_marks_all += work_marks.count()
        
        works_analysis.sort(key=lambda x: x['average_score'])
        
        context['works_analysis'] = works_analysis
        context['summary_stats'] = {
            'total_works': len(works_analysis),
            'easy_works': easy_works_count,
            'hard_works': hard_works_count,
            'total_marks': total_marks_all,
        }
        return context
    
    def assess_difficulty(self, avg_score, avg_percentage):
        if avg_score >= 4.5:
            return "Лёгкая"
        elif avg_score >= 3.5:
            return "Средняя"
        elif avg_score >= 2.5:
            return "Сложная"
        else:
            return "Очень сложная"


class EventsStatusView(TemplateView):
    """Отчет по статусам событий"""
    template_name = 'reports/events_status.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from events.models import Event, EventParticipation
        
        events_by_status = Event.objects.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        context['events_by_status'] = list(events_by_status)
        
        current_date = datetime.now()
        
        context.update({
            'overdue_events': Event.objects.filter(
                status='planned',
                planned_date__lt=current_date - timedelta(days=1)
            ).select_related('work'),
            'long_reviewing': Event.objects.filter(
                status='reviewing',
                actual_end__lt=current_date - timedelta(days=7)
            ).select_related('work'),
            'completed_unchecked': Event.objects.filter(
                status='completed',
                actual_end__lt=current_date - timedelta(days=3)
            ).select_related('work'),
        })
        
        participation_stats = EventParticipation.objects.values(
            'status'
        ).annotate(count=Count('id')).order_by('status')
        context['participation_stats'] = list(participation_stats)
        
        return context


# ============================================================
# HEATMAP
# ============================================================

from collections import defaultdict


class HeatmapView(View):
    """Тепловая карта: ученики × темы"""

    def get(self, request):
        group_id = request.GET.get('group')
        section = request.GET.get('section', '')
        transpose = request.GET.get('transpose') == '1'

        groups = StudentGroup.objects.all().order_by('name')

        if group_id:
            group = get_object_or_404(StudentGroup, pk=group_id)
            students = list(group.students.all().order_by('last_name', 'first_name'))
        else:
            group = None
            students = list(Student.objects.all().order_by('last_name', 'first_name'))

        sections = list(
            Topic.objects.filter(subject='Физика')
            .values_list('section', flat=True)
            .distinct().order_by('section')
        )

        if not students:
            return render(request, 'reports/heatmap.html', {
                'groups': groups, 'selected_group': group,
                'sections': sections, 'selected_section': section,
                'has_data': False, 'is_transposed': transpose,
            })

        columns, rows, col_averages = _build_topic_data(students, section)
        group_param = f'?group={group.pk}' if group else ''

        if not transpose:
            grid_row_header = 'Ученик'
            grid_rows = [{
                'label': row['student'].get_short_name(),
                'url': reverse('students:detail', args=[row['student'].pk]),
                'cells': row['cells'],
                'avg': row['avg'],
                'avg_css': row['avg_css'],
            } for row in rows]
            grid_col_headers = [{
                'label': t.name,
                'title': f'{t.section} → {t.name}',
            } for t in columns]
            grid_col_averages = col_averages
        else:
            grid_row_header = 'Тема'
            grid_rows = []
            for i, topic in enumerate(columns):
                cells = [rows[j]['cells'][i] for j in range(len(rows))]
                url = reverse('reports:heatmap-drilldown', args=[topic.pk]) + group_param
                grid_rows.append({
                    'label': topic.name,
                    'url': url,
                    'cells': cells,
                    'avg': col_averages[i]['pct'],
                    'avg_css': col_averages[i]['css'],
                })
            grid_col_headers = [{
                'label': row['student'].get_short_name(),
                'title': row['student'].get_full_name(),
            } for row in rows]
            grid_col_averages = [{'pct': row['avg'], 'css': row['avg_css']} for row in rows]

        toggle_params = request.GET.copy()
        if transpose:
            toggle_params.pop('transpose', None)
        else:
            toggle_params['transpose'] = '1'
        toggle_url = f'?{toggle_params.urlencode()}' if toggle_params else '?'

        return render(request, 'reports/heatmap.html', {
            'groups': groups,
            'selected_group': group,
            'sections': sections,
            'selected_section': section,
            'is_transposed': transpose,
            'toggle_url': toggle_url,
            'grid_row_header': grid_row_header,
            'grid_rows': grid_rows,
            'grid_col_headers': grid_col_headers,
            'grid_col_averages': grid_col_averages,
            'total_students': len(students),
            'total_topics': len(columns),
            'has_data': bool(rows and columns),
        })


class HeatmapDrilldownView(View):
    """Drill-down: ученики × подтемы одной темы"""

    def get(self, request, topic_pk):
        topic = get_object_or_404(Topic, pk=topic_pk)
        group_id = request.GET.get('group')
        transpose = request.GET.get('transpose') == '1'

        groups = StudentGroup.objects.all().order_by('name')

        if group_id:
            group = get_object_or_404(StudentGroup, pk=group_id)
            students = list(group.students.all().order_by('last_name', 'first_name'))
        else:
            group = None
            students = list(Student.objects.all().order_by('last_name', 'first_name'))

        columns, rows, col_averages = _build_subtopic_data(students, topic)
        group_param = f'?group={group.pk}' if group else ''
        group_suffix = f'&group={group.pk}' if group else ''

        if not transpose:
            grid_row_header = 'Ученик'
            grid_rows = []
            for row in rows:
                cells_with_urls = []
                for i, cell in enumerate(row['cells']):
                    url = None
                    if cell['pct'] is not None:
                        url = (reverse('reports:heatmap-student',
                                       args=[topic.pk, row['student'].pk])
                               + f'?subtopic={columns[i].pk}{group_suffix}')
                    cells_with_urls.append({**cell, 'url': url})

                student_url = (reverse('reports:heatmap-student',
                                       args=[topic.pk, row['student'].pk])
                               + group_param)
                grid_rows.append({
                    'label': row['student'].get_short_name(),
                    'url': student_url,
                    'cells': cells_with_urls,
                    'avg': row['avg'],
                    'avg_css': row['avg_css'],
                })

            grid_col_headers = [{
                'label': sub.name,
                'title': sub.name,
                'url': reverse('reports:heatmap-subtopic', args=[sub.pk]) + group_param,
            } for sub in columns]
            grid_col_averages = col_averages
        else:
            grid_row_header = 'Подтема'
            grid_rows = []
            for i, sub in enumerate(columns):
                cells_with_urls = []
                for j in range(len(rows)):
                    cell = rows[j]['cells'][i]
                    url = None
                    if cell['pct'] is not None:
                        url = (reverse('reports:heatmap-student',
                                       args=[topic.pk, rows[j]['student'].pk])
                               + f'?subtopic={sub.pk}{group_suffix}')
                    cells_with_urls.append({**cell, 'url': url})

                grid_rows.append({
                    'label': sub.name,
                    'url': reverse('reports:heatmap-subtopic', args=[sub.pk]) + group_param,
                    'cells': cells_with_urls,
                    'avg': col_averages[i]['pct'],
                    'avg_css': col_averages[i]['css'],
                })

            grid_col_headers = [{
                'label': row['student'].get_short_name(),
                'title': row['student'].get_full_name(),
                'url': (reverse('reports:heatmap-student',
                                args=[topic.pk, row['student'].pk]) + group_param),
            } for row in rows]
            grid_col_averages = [{'pct': row['avg'], 'css': row['avg_css']} for row in rows]

        toggle_params = request.GET.copy()
        if transpose:
            toggle_params.pop('transpose', None)
        else:
            toggle_params['transpose'] = '1'
        toggle_url = f'{request.path}?{toggle_params.urlencode()}'

        return render(request, 'reports/heatmap_drilldown.html', {
            'topic': topic,
            'groups': groups,
            'selected_group': group,
            'group_param': group_param,
            'is_transposed': transpose,
            'toggle_url': toggle_url,
            'grid_row_header': grid_row_header,
            'grid_rows': grid_rows,
            'grid_col_headers': grid_col_headers,
            'grid_col_averages': grid_col_averages,
            'has_data': bool(rows and columns),
        })


class HeatmapStudentView(View):
    """Детальный вид: один ученик × подтемы одной темы"""

    def get(self, request, topic_pk, student_pk):
        topic = get_object_or_404(Topic, pk=topic_pk)
        student = get_object_or_404(Student, pk=student_pk)
        subtopic_id = request.GET.get('subtopic')
        group_id = request.GET.get('group')
        group_param = f'?group={group_id}' if group_id else ''

        selected_subtopic = None
        if subtopic_id:
            selected_subtopic = SubTopic.objects.filter(pk=subtopic_id).first()

        marks = Mark.objects.filter(
            participation__student=student,
        ).select_related(
            'participation__event',
            'participation__variant',
        )

        all_task_ids = set()
        for mark in marks:
            if mark.task_scores:
                all_task_ids.update(mark.task_scores.keys())

        tasks_qs = Task.objects.filter(
            pk__in=all_task_ids,
            topic=topic,
        ).select_related('subtopic')
        task_map = {str(t.pk): t for t in tasks_qs}

        # Детализация: per-mark дедупликация
        details = []
        for mark in marks:
            if not mark.task_scores:
                continue
            event = mark.participation.event
            seen = set()
            for task_id, scores in mark.task_scores.items():
                if task_id in seen:
                    continue
                seen.add(task_id)

                task = task_map.get(task_id)
                if not task:
                    continue
                # Фильтр по подтеме
                if selected_subtopic and task.subtopic_id != selected_subtopic.id:
                    continue

                pts = scores.get('points', 0)
                mx = scores.get('max_points', 0)
                pct = round(pts / mx * 100) if mx > 0 else 0
                details.append({
                    'event': event,
                    'task': task,
                    'subtopic': task.subtopic,
                    'points': pts,
                    'max_points': mx,
                    'pct': pct,
                    'css': _color_class(pct),
                })

        details.sort(key=lambda d: (
            d['subtopic'].name if d['subtopic'] else '',
            d['event'].planned_date,
        ))

        # Агрегация по подтемам (всегда все — для карточек)
        all_details = []
        for mark in marks:
            if not mark.task_scores:
                continue
            seen = set()
            for task_id, scores in mark.task_scores.items():
                if task_id in seen:
                    continue
                seen.add(task_id)
                task = task_map.get(task_id)
                if not task:
                    continue
                all_details.append({
                    'subtopic': task.subtopic,
                    'points': scores.get('points', 0),
                    'max_points': scores.get('max_points', 0),
                })

        sub_agg = defaultdict(lambda: {'points': 0, 'max_points': 0})
        for d in all_details:
            if d['subtopic']:
                sub_agg[d['subtopic'].id]['points'] += d['points']
                sub_agg[d['subtopic'].id]['max_points'] += d['max_points']

        subtopic_summary = []
        for sub in SubTopic.objects.filter(topic=topic).order_by('order'):
            data = sub_agg.get(sub.id)
            is_selected = selected_subtopic and sub.id == selected_subtopic.id
            if data and data['max_points'] > 0:
                pct = round(data['points'] / data['max_points'] * 100)
                subtopic_summary.append({
                    'subtopic': sub,
                    'points': data['points'],
                    'max_points': data['max_points'],
                    'pct': pct,
                    'css': _color_class(pct),
                    'is_selected': is_selected,
                })
            else:
                subtopic_summary.append({
                    'subtopic': sub,
                    'pct': None,
                    'css': 'no-data',
                    'is_selected': is_selected,
                })

        group_suffix = f'&group={group_id}' if group_id else ''

        return render(request, 'reports/heatmap_student.html', {
            'topic': topic,
            'student': student,
            'details': details,
            'subtopic_summary': subtopic_summary,
            'selected_subtopic': selected_subtopic,
            'group_param': group_param,
            'group_suffix': group_suffix,
        })


class HeatmapSubtopicView(View):
    """Анализ подтемы: все ученики × задания одной подтемы"""

    def get(self, request, subtopic_pk):
        subtopic = get_object_or_404(SubTopic, pk=subtopic_pk)
        topic = subtopic.topic
        group_id = request.GET.get('group')

        groups = StudentGroup.objects.all().order_by('name')

        if group_id:
            group = get_object_or_404(StudentGroup, pk=group_id)
            students = list(group.students.all().order_by('last_name', 'first_name'))
        else:
            group = None
            students = list(Student.objects.all().order_by('last_name', 'first_name'))

        group_param = f'?group={group.pk}' if group else ''

        marks = Mark.objects.filter(
            participation__student__in=students,
        ).select_related('participation__student', 'participation__event')

        all_task_ids = set()
        for mark in marks:
            if mark.task_scores:
                all_task_ids.update(mark.task_scores.keys())

        tasks_qs = Task.objects.filter(
            pk__in=all_task_ids,
            subtopic=subtopic,
        )
        task_map = {str(t.pk): t for t in tasks_qs}

        # Агрегация по ученикам
        student_agg = defaultdict(lambda: {'points': 0, 'max_points': 0, 'events': set()})
        task_agg = defaultdict(lambda: {'points': 0, 'max_points': 0, 'count': 0})

        for mark in marks:
            if not mark.task_scores:
                continue
            student_id = mark.participation.student_id
            event_name = mark.participation.event.name
            seen = set()
            for task_id, scores in mark.task_scores.items():
                if task_id in seen:
                    continue
                seen.add(task_id)

                task = task_map.get(task_id)
                if not task:
                    continue

                pts = scores.get('points', 0)
                mx = scores.get('max_points', 0)

                student_agg[student_id]['points'] += pts
                student_agg[student_id]['max_points'] += mx
                student_agg[student_id]['events'].add(event_name)

                task_agg[task.id]['points'] += pts
                task_agg[task.id]['max_points'] += mx
                task_agg[task.id]['count'] += 1

        # Строки учеников
        student_rows = []
        for student in students:
            data = student_agg.get(student.id)
            if data and data['max_points'] > 0:
                pct = round(data['points'] / data['max_points'] * 100)
                student_rows.append({
                    'student': student,
                    'points': data['points'],
                    'max_points': data['max_points'],
                    'pct': pct,
                    'css': _color_class(pct),
                    'events': sorted(data['events']),
                    'url': (reverse('reports:heatmap-student',
                                    args=[topic.pk, student.pk])
                            + f'?subtopic={subtopic.pk}'
                            + (f'&group={group.pk}' if group else '')),
                })
            else:
                student_rows.append({
                    'student': student,
                    'pct': None,
                    'css': 'no-data',
                    'events': [],
                    'url': None,
                })

        # Анализ заданий
        task_rows = []
        for task in tasks_qs.order_by('difficulty', 'text'):
            data = task_agg.get(task.id)
            if data and data['max_points'] > 0:
                avg_pct = round(data['points'] / data['max_points'] * 100)
                task_rows.append({
                    'task': task,
                    'avg_pct': avg_pct,
                    'css': _color_class(avg_pct),
                    'students_count': data['count'],
                    'total_points': data['points'],
                    'total_max': data['max_points'],
                })

        # Общая статистика
        total_pts = sum(d['points'] for d in student_agg.values())
        total_max = sum(d['max_points'] for d in student_agg.values())
        overall_pct = round(total_pts / total_max * 100) if total_max > 0 else None
        students_with_data = sum(1 for r in student_rows if r['pct'] is not None)

        return render(request, 'reports/heatmap_subtopic.html', {
            'subtopic': subtopic,
            'topic': topic,
            'groups': groups,
            'selected_group': group,
            'group_param': group_param,
            'student_rows': student_rows,
            'task_rows': task_rows,
            'overall_pct': overall_pct,
            'overall_css': _color_class(overall_pct) if overall_pct else 'no-data',
            'total_students': len(students),
            'students_with_data': students_with_data,
        })


# ============================================================
# Общие функции
# ============================================================

def _build_topic_data(students, section_filter=''):
    """Агрегация: ученики × темы"""
    marks = Mark.objects.filter(
        participation__student__in=students,
    ).select_related('participation__student')

    all_task_ids = set()
    for mark in marks:
        if mark.task_scores:
            all_task_ids.update(mark.task_scores.keys())

    if not all_task_ids:
        return [], [], []

    tasks_qs = Task.objects.filter(pk__in=all_task_ids).select_related('topic', 'subtopic')
    task_map = {str(t.pk): t for t in tasks_qs}

    agg = defaultdict(lambda: {'points': 0, 'max_points': 0})

    for mark in marks:
        student_id = mark.participation.student_id
        if not mark.task_scores:
            continue
        seen = set()
        for task_id, scores in mark.task_scores.items():
            if task_id in seen:
                continue
            seen.add(task_id)

            task = task_map.get(task_id)
            if not task or not task.topic:
                continue
            if section_filter and task.topic.section != section_filter:
                continue

            key = (student_id, task.topic_id)
            agg[key]['points'] += scores.get('points', 0)
            agg[key]['max_points'] += scores.get('max_points', 0)

    topic_ids = set(tid for (_, tid) in agg.keys())
    columns = list(
        Topic.objects.filter(pk__in=topic_ids).order_by('section', 'order', 'name')
    )

    rows = []
    for student in students:
        cells = []
        total_pts = 0
        total_max = 0
        for topic in columns:
            data = agg.get((student.id, topic.id))
            if data and data['max_points'] > 0:
                pct = round(data['points'] / data['max_points'] * 100)
                total_pts += data['points']
                total_max += data['max_points']
                cells.append({
                    'pct': pct, 'points': data['points'],
                    'max_points': data['max_points'],
                    'css': _color_class(pct), 'topic': topic,
                })
            else:
                cells.append({'pct': None, 'css': 'no-data', 'topic': topic})

        avg = round(total_pts / total_max * 100) if total_max > 0 else None
        rows.append({
            'student': student, 'cells': cells,
            'avg': avg,
            'avg_css': _color_class(avg) if avg is not None else 'no-data',
        })

    col_averages = []
    for topic in columns:
        pts = sum(agg.get((s.id, topic.id), {}).get('points', 0) for s in students)
        mx = sum(agg.get((s.id, topic.id), {}).get('max_points', 0) for s in students)
        avg = round(pts / mx * 100) if mx > 0 else None
        col_averages.append({
            'pct': avg, 'css': _color_class(avg) if avg is not None else 'no-data',
        })

    return columns, rows, col_averages


def _build_subtopic_data(students, topic):
    """Агрегация: ученики × подтемы одной темы"""
    marks = Mark.objects.filter(
        participation__student__in=students,
    ).select_related('participation__student')

    all_task_ids = set()
    for mark in marks:
        if mark.task_scores:
            all_task_ids.update(mark.task_scores.keys())

    if not all_task_ids:
        return [], [], []

    tasks_qs = Task.objects.filter(
        pk__in=all_task_ids, topic=topic,
    ).select_related('subtopic')
    task_map = {str(t.pk): t for t in tasks_qs}

    agg = defaultdict(lambda: {'points': 0, 'max_points': 0})

    for mark in marks:
        student_id = mark.participation.student_id
        if not mark.task_scores:
            continue
        seen = set()
        for task_id, scores in mark.task_scores.items():
            if task_id in seen:
                continue
            seen.add(task_id)

            task = task_map.get(task_id)
            if not task:
                continue

            col_key = task.subtopic_id if task.subtopic_id else f'topic_{task.topic_id}'
            key = (student_id, col_key)
            agg[key]['points'] += scores.get('points', 0)
            agg[key]['max_points'] += scores.get('max_points', 0)

    subtopic_ids = set()
    for (_, col_key) in agg.keys():
        if not str(col_key).startswith('topic_'):
            subtopic_ids.add(col_key)

    columns = list(SubTopic.objects.filter(pk__in=subtopic_ids).order_by('order', 'name'))

    rows = []
    for student in students:
        cells = []
        total_pts = 0
        total_max = 0
        for sub in columns:
            data = agg.get((student.id, sub.id))
            if data and data['max_points'] > 0:
                pct = round(data['points'] / data['max_points'] * 100)
                total_pts += data['points']
                total_max += data['max_points']
                cells.append({
                    'pct': pct, 'points': data['points'],
                    'max_points': data['max_points'],
                    'css': _color_class(pct), 'subtopic': sub,
                })
            else:
                cells.append({'pct': None, 'css': 'no-data', 'subtopic': sub})

        avg = round(total_pts / total_max * 100) if total_max > 0 else None
        rows.append({
            'student': student, 'cells': cells,
            'avg': avg,
            'avg_css': _color_class(avg) if avg is not None else 'no-data',
        })

    col_averages = []
    for sub in columns:
        pts = sum(agg.get((s.id, sub.id), {}).get('points', 0) for s in students)
        mx = sum(agg.get((s.id, sub.id), {}).get('max_points', 0) for s in students)
        avg = round(pts / mx * 100) if mx > 0 else None
        col_averages.append({
            'pct': avg, 'css': _color_class(avg) if avg is not None else 'no-data',
        })

    return columns, rows, col_averages


def _color_class(pct):
    if pct is None:
        return 'no-data'
    if pct >= 95:
        return 'perfect'
    if pct >= 85:
        return 'excellent'
    if pct >= 70:
        return 'good'
    if pct >= 60:
        return 'moderate'
    if pct >= 45:
        return 'warning'
    return 'danger'

