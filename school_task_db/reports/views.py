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

def _get_nav_context(active_report='', active_course_pk=None):
    """Общий контекст для навигации по отчётам"""
    from curriculum.models import Course
    return {
        'active_report': active_report,
        'active_course_pk': active_course_pk,
        'courses': Course.objects.filter(is_active=True).order_by('grade_level', 'name'),
    }


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
        #context['courses'] = Course.objects.all()
        context['courses'] = Course.objects.filter(is_active=True).order_by('grade_level', 'name')
        context['student_groups'] = StudentGroup.objects.all()
        
        context.update(_get_nav_context('dashboard'))

        return context


class StudentPerformanceView(TemplateView):
    """Отчет по успеваемости учеников"""
    template_name = 'reports/student_performance.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        from students.models import Student, StudentGroup
        from events.models import Mark, EventParticipation

        groups = StudentGroup.objects.all().order_by('name')
        group_id = self.request.GET.get('group')

        if group_id:
            group = StudentGroup.objects.filter(pk=group_id).first()
            students = group.students.all() if group else Student.objects.all()
        else:
            group = None
            students = Student.objects.all()

        students = students.order_by('last_name', 'first_name')

        students_stats = []
        for student in students:
            participations = student.eventparticipation_set.all()
            completed = participations.filter(
                status__in=['completed', 'graded']
            )
            marks = Mark.objects.filter(participation__student=student)
            avg_score = marks.aggregate(avg=Avg('score'))['avg'] or 0

            # Средний % по task_scores
            total_pts = 0
            total_max = 0
            for mark in marks:
                if mark.task_scores:
                    for scores in mark.task_scores.values():
                        total_pts += scores.get('points', 0)
                        total_max += scores.get('max_points', 0)
            avg_pct = round(total_pts / total_max * 100) if total_max > 0 else None

            completion_rate = round(
                (completed.count() / participations.count() * 100)
                if participations.count() > 0 else 0, 1
            )

            stat = {
                'student': student,
                'total_participations': participations.count(),
                'completed_participations': completed.count(),
                'completion_rate': completion_rate,
                'total_marks': marks.count(),
                'average_score': round(avg_score, 2) if avg_score else 0,
                'average_pct': avg_pct,
                'last_activity': participations.order_by(
                    '-created_at'
                ).first(),
            }
            if participations.count() > 0:
                students_stats.append(stat)

        context['students_stats'] = students_stats
        context['groups'] = groups
        context['selected_group'] = group
        context['summary_stats'] = {
            'total_students': len(students_stats),
            'high_performers': sum(1 for s in students_stats if (s['average_pct'] or 0) >= 85),
            'need_attention': sum(1 for s in students_stats if s['average_pct'] is not None and s['average_pct'] < 45),
            'avg_completion_rate': round(
                sum(s['completion_rate'] for s in students_stats) / len(students_stats), 1
            ) if students_stats else 0,
            'avg_pct': round(
                sum(s['average_pct'] for s in students_stats if s['average_pct'] is not None) /
                max(sum(1 for s in students_stats if s['average_pct'] is not None), 1)
            ),
        }

        context.update(_get_nav_context('student-performance'))
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
            'total_marks': sum(w['total_marks'] for w in works_analysis),
            'easy_works': sum(1 for w in works_analysis if w['difficulty_assessment'] == 'Легкая'),
            'hard_works': sum(1 for w in works_analysis if w['difficulty_assessment'] in ('Сложная', 'Очень сложная')),
            'avg_score': round(
                sum(w['average_score'] for w in works_analysis) / len(works_analysis), 2
            ) if works_analysis else 0,
        }

        context.update(_get_nav_context('work-analysis'))

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

        context['all_events'] = Event.objects.select_related('work').order_by('-planned_date')
        context.update(_get_nav_context('events-status'))
        
        return context


# ============================================================
# HEATMAP
# ============================================================

from collections import defaultdict


class HeatmapView(View):
    """Тепловая карта: ученики x темы"""

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
                **_get_nav_context('heatmap'),
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
            **_get_nav_context('heatmap'),
        })

class HeatmapCourseView(View):
    """Тепловая карта по курсу: ученики × темы курса"""

    def get(self, request, course_pk):
        from curriculum.models import Course, CourseAssignment

        course = get_object_or_404(Course, pk=course_pk)
        group_id = request.GET.get('group')
        transpose = request.GET.get('transpose') == '1'

        # Группы курса
        course_groups = course.student_groups.all().order_by('name')

        if group_id:
            group = get_object_or_404(StudentGroup, pk=group_id)
            students = list(group.students.all().order_by('last_name', 'first_name'))
        elif course_groups.exists():
            students = list(
                Student.objects.filter(
                    studentgroup__in=course_groups
                ).distinct().order_by('last_name', 'first_name')
            )
            group = None
        else:
            students = list(Student.objects.all().order_by('last_name', 'first_name'))
            group = None

        if not students:
            return render(request, 'reports/heatmap_course.html', {
                'course': course,
                'groups': course_groups,
                'selected_group': group,
                'has_data': False,
                'is_transposed': transpose,
                **_get_nav_context('heatmap-course', course.pk),
            })

        # Темы курса: через CourseAssignment → Work → Variant → Task → Topic
        course_works = [ca.work for ca in CourseAssignment.objects.filter(
            course=course).select_related('work')]

        columns, rows, col_averages = _build_topic_data_for_course(
            students, course_works)
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
        toggle_url = f'{request.path}?{toggle_params.urlencode()}'

        # Plotly: динамика по работам курса
        timeline_json = _build_course_timeline(course_works, students)

        return render(request, 'reports/heatmap_course.html', {
            'course': course,
            'groups': course_groups,
            'selected_group': group,
            'group_param': group_param,
            'is_transposed': transpose,
            'toggle_url': toggle_url,
            'grid_row_header': grid_row_header,
            'grid_rows': grid_rows,
            'grid_col_headers': grid_col_headers,
            'grid_col_averages': grid_col_averages,
            'total_students': len(students),
            'total_topics': len(columns),
            'has_data': bool(rows and columns),
            'timeline_json': timeline_json,
            **_get_nav_context('heatmap-course', course.pk),
        })


class HeatmapDrilldownView(View):
    """Drill-down: ученики x подтемы одной темы"""

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
            **_get_nav_context('heatmap'),
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
            **_get_nav_context('heatmap'),
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
            **_get_nav_context('heatmap'),
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

def _build_topic_data_for_course(students, course_works):
    """Агрегация: ученики × темы, но только по работам курса"""
    from works.models import Variant

    # Задания из вариантов работ курса
    work_ids = [w.id for w in course_works]
    variant_ids = Variant.objects.filter(work_id__in=work_ids).values_list('id', flat=True)

    # Все task_ids из вариантов
    course_task_ids = set()
    for variant in Variant.objects.filter(work_id__in=work_ids).prefetch_related('tasks'):
        for task in variant.tasks.all():
            course_task_ids.add(str(task.pk))

    marks = Mark.objects.filter(
        participation__student__in=students,
        participation__event__work_id__in=work_ids,
    ).select_related('participation__student')

    all_task_ids = set()
    for mark in marks:
        if mark.task_scores:
            all_task_ids.update(mark.task_scores.keys())

    # Фильтруем только задания курса
    relevant_task_ids = all_task_ids & course_task_ids if course_task_ids else all_task_ids

    if not relevant_task_ids:
        return [], [], []

    tasks_qs = Task.objects.filter(pk__in=relevant_task_ids).select_related('topic', 'subtopic')
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


def _build_course_timeline(course_works, students):
    """Plotly JSON: средний % по работам курса во времени"""
    import json
    from events.models import Event

    work_ids = [w.id for w in course_works]
    events = Event.objects.filter(
        work_id__in=work_ids,
        status='graded',
    ).order_by('planned_date')

    dates = []
    averages = []
    labels = []

    for event in events:
        marks = Mark.objects.filter(
            participation__event=event,
            participation__student__in=students,
        )
        if not marks.exists():
            continue

        total_pts = 0
        total_max = 0
        for mark in marks:
            if not mark.task_scores:
                continue
            seen = set()
            for task_id, scores in mark.task_scores.items():
                if task_id in seen:
                    continue
                seen.add(task_id)
                total_pts += scores.get('points', 0)
                total_max += scores.get('max_points', 0)

        if total_max > 0:
            avg_pct = round(total_pts / total_max * 100)
            dates.append(event.planned_date.strftime('%Y-%m-%d'))
            averages.append(avg_pct)
            labels.append(event.name)

    chart = {
        'data': [{
            'x': dates,
            'y': averages,
            'text': labels,
            'mode': 'lines+markers',
            'type': 'scatter',
            'name': 'Средний %',
            'line': {'color': '#0d6efd', 'width': 3},
            'marker': {'size': 10},
            'hovertemplate': '%{text}<br>%{y}%<extra></extra>',
        }],
        'layout': {
            'title': {'text': 'Динамика результатов', 'font': {'size': 16}},
            'xaxis': {'title': 'Дата'},
            'yaxis': {'title': '%', 'range': [0, 105]},
            'margin': {'t': 40, 'b': 40, 'l': 50, 'r': 20},
            'height': 300,
            'shapes': [
                {'type': 'line', 'y0': 70, 'y1': 70, 'x0': 0, 'x1': 1,
                 'xref': 'paper', 'line': {'color': '#28a745', 'dash': 'dash', 'width': 1}},
                {'type': 'line', 'y0': 45, 'y1': 45, 'x0': 0, 'x1': 1,
                 'xref': 'paper', 'line': {'color': '#dc3545', 'dash': 'dash', 'width': 1}},
            ],
        },
        'config': {'displayModeBar': False, 'responsive': True},
    }

    return json.dumps(chart, ensure_ascii=False)



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

