# reports/views.py

import json
from django.urls import reverse
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from django.db.models import Count, Avg, Q
from django.utils import timezone

from core_logic.use_cases.get_events_status_report import (
    EventsStatusReportRequest,
)
from core_logic.use_cases.get_heatmap_overview import HeatmapOverviewRequest
from core_logic.use_cases.get_reports_dashboard import ReportsDashboardRequest
from core_logic.use_cases.get_student_performance_report import (
    StudentPerformanceReportRequest,
)
from core_logic.use_cases.get_work_analysis_report import WorkAnalysisReportRequest
from infrastructure.container import container
from . import plotly_utils

from students.models import Student, StudentGroup
from tasks.models import Task
from events.models import Mark, EventParticipation
from curriculum.models import Topic, SubTopic

def _get_nav_context(active_report='', active_course_pk=None, year=None):
    """Общий контекст для навигации по отчётам"""
    from curriculum.models import Course
    qs = Course.objects.filter(is_active=True)
    if year:
        qs = qs.filter(year=year)
    return {
        'active_report': active_report,
        'active_course_pk': active_course_pk,
        'courses': qs.order_by('grade_level', 'name'),
    }


def _year_qs(request):
    """Возвращает dict с отфильтрованными по году querysets"""
    from students.models import Student, StudentGroup
    from events.models import Event, EventParticipation, Mark
    from works.models import Work
    from curriculum.models import Course

    year = getattr(request, 'current_year', None)

    if year:
        groups = StudentGroup.objects.filter(academic_year=year)
        date_range = (year.start_date, year.end_date)
        events = Event.objects.filter(planned_date__range=date_range)
        students = Student.objects.filter(studentgroup__academic_year=year).distinct()
        courses = Course.objects.filter(year=year, is_active=True)
        marks = Mark.objects.filter(
            participation__event__planned_date__range=date_range
        )
        participations = EventParticipation.objects.filter(
            event__planned_date__range=date_range
        )
    else:
        groups = StudentGroup.objects.all()
        events = Event.objects.all()
        students = Student.objects.all()
        courses = Course.objects.filter(is_active=True)
        marks = Mark.objects.all()
        participations = EventParticipation.objects.all()

    return {
        'year': year,
        'groups': groups,
        'events': events,
        'students': students,
        'courses': courses,
        'marks': marks,
        'participations': participations,
    }


class ReportsDashboardView(TemplateView):
    template_name = 'reports/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = container.get_reports_dashboard_use_case().execute(
            ReportsDashboardRequest(
                year=getattr(self.request, 'current_year', None),
                current_date=timezone.now(),
            ),
        )

        context.update({
            'total_students': report.total_students,
            'total_events': report.total_events,
            'total_works': report.total_works,
            'total_courses': report.total_courses,
            'total_marks': report.total_marks,
            'average_score': report.average_score,
            'marks_last_month': report.marks_last_month,
            'events_planned': report.events_planned,
            'events_completed': report.events_completed,
            'events_graded': report.events_graded,
            'class_stats': report.class_stats,
            'recent_events': report.recent_events,
            'courses': report.courses,
            'active_report': report.active_report,
            'active_course_pk': report.active_course_pk,
        })

        context['score_chart_json'] = plotly_utils.to_json(
            plotly_utils.score_distribution_config(report.score_counts)
        )
        context['activity_chart_json'] = plotly_utils.to_json(
            plotly_utils.line_chart_config(
                report.monthly_labels,
                report.monthly_values,
                title='Активность по месяцам'
            )
        )
        context['class_chart_json'] = plotly_utils.to_json(
            plotly_utils.multi_bar_config(
                report.class_names,
                {
                    'Средний балл': report.class_avg_scores,
                    '% выполнения (÷25)': [
                        round(c / 25, 2) for c in report.class_completion
                    ],
                },
                title='Сравнение классов'
            )
        )

        context['gauge_json'] = plotly_utils.to_json(
            plotly_utils.gauge_config(
                report.average_score or 0,
                title='Средний балл',
            )
        )

        status_labels = []
        status_values = []
        status_colors = []
        status_map = {
            'planned': ('Запланировано', 'rgba(23, 162, 184, 0.75)'),
            'in_progress': ('Выполняется', 'rgba(111, 66, 193, 0.75)'),
            'completed': ('Завершено', 'rgba(40, 167, 69, 0.75)'),
            'reviewing': ('На проверке', 'rgba(255, 193, 7, 0.75)'),
            'graded': ('Проверено', 'rgba(13, 110, 253, 0.75)'),
            'closed': ('Закрыто', 'rgba(108, 117, 125, 0.75)'),
        }
        for status_code, (label, color) in status_map.items():
            count = report.event_status_counts.get(status_code, 0)
            if count > 0:
                status_labels.append(label)
                status_values.append(count)
                status_colors.append(color)

        context['donut_json'] = plotly_utils.to_json(
            plotly_utils.donut_config(
                status_labels, status_values,
                title='Статусы событий',
                colors=status_colors
            )
        )

        context['box_plot_json'] = plotly_utils.to_json(
            plotly_utils.box_plot_config(
                report.box_data,
                title='Распределение по работам',
            )
        )

        return context


class StudentPerformanceView(TemplateView):
    """Отчет по успеваемости учеников"""
    template_name = 'reports/student_performance.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = container.get_student_performance_report_use_case().execute(
            StudentPerformanceReportRequest(
                year=getattr(self.request, 'current_year', None),
                group_id=self.request.GET.get('group'),
            ),
        )

        context.update({
            'students_stats': report.students_stats,
            'groups': report.groups,
            'selected_group': report.selected_group,
            'summary_stats': report.summary_stats,
            'active_report': report.active_report,
            'active_course_pk': report.active_course_pk,
            'courses': report.courses,
        })
        return context


class WorkAnalysisView(TemplateView):
    """Анализ работ и их результатов"""
    template_name = 'reports/work_analysis.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = container.get_work_analysis_report_use_case().execute(
            WorkAnalysisReportRequest(
                year=getattr(self.request, 'current_year', None),
            ),
        )

        context.update({
            'works_analysis': report.works_analysis,
            'summary_stats': report.summary_stats,
            'active_report': report.active_report,
            'active_course_pk': report.active_course_pk,
            'courses': report.courses,
        })
        return context


class EventsStatusView(TemplateView):
    """Отчет по статусам событий"""
    template_name = 'reports/events_status.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = container.get_events_status_report_use_case().execute(
            EventsStatusReportRequest(
                year=getattr(self.request, 'current_year', None),
                current_date=timezone.now(),
            ),
        )

        context.update({
            'events_by_status': report.events_by_status,
            'overdue_events': report.overdue_events,
            'long_reviewing': report.long_reviewing,
            'completed_unchecked': report.completed_unchecked,
            'participation_stats': report.participation_stats,
            'all_events': report.all_events,
            'active_report': report.active_report,
            'active_course_pk': report.active_course_pk,
            'courses': report.courses,
        })

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
        overview = container.get_heatmap_overview_use_case().execute(
            HeatmapOverviewRequest(group_id=group_id),
        )

        groups = overview.groups
        group = overview.selected_group
        students = overview.students

        if not students:
            return render(request, 'reports/heatmap.html', {
                'groups': groups, 'selected_group': group,
                'sections': overview.sections, 'selected_section': section,
                'has_data': False, 'is_transposed': transpose,
                'active_report': overview.active_report,
                'active_course_pk': overview.active_course_pk,
                'courses': overview.courses,
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
            'sections': overview.sections,
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
            'active_report': overview.active_report,
            'active_course_pk': overview.active_course_pk,
            'courses': overview.courses,
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

class JournalSelectView(TemplateView):
    """Выбор курса и класса для журнала"""
    template_name = 'reports/journal_select.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from curriculum.models import Course
        from students.models import StudentGroup
        from events.models import Event

        year = getattr(self.request, 'current_year', None)
        qs = _year_qs(self.request)

        courses = qs['courses'].order_by('grade_level', 'name')
        groups = qs['groups'].order_by('name')

        # Собираем пары курс-класс, у которых есть события
        journal_links = []
        for course in courses:
            for group in course.student_groups.all():
                if group in groups:
                    event_count = Event.objects.filter(
                        course=course,
                        eventparticipation__student__in=group.students.all()
                    ).distinct().count()
                    journal_links.append({
                        'course': course,
                        'group': group,
                        'event_count': event_count,
                    })

        context['journal_links'] = journal_links
        context['courses'] = courses
        context['groups'] = groups
        context.update(_get_nav_context('journal', year=year))
        return context


class JournalView(TemplateView):
    """Классный журнал — ученики × события"""
    template_name = 'reports/journal.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        from curriculum.models import Course
        from students.models import StudentGroup
        from events.models import Event, EventParticipation, Mark

        course = get_object_or_404(Course, pk=kwargs['course_pk'])
        group = get_object_or_404(StudentGroup, pk=kwargs['group_pk'])

        students = group.students.all().order_by('last_name', 'first_name')
        student_ids = list(students.values_list('id', flat=True))

        # События этого курса, где есть ученики из класса
        events = Event.objects.filter(
            course=course,
            eventparticipation__student__in=student_ids
        ).distinct().select_related('work').order_by('planned_date')

        # Все участия и оценки — два запроса вместо N×M
        participations = EventParticipation.objects.filter(
            event__in=events,
            student__in=student_ids
        ).select_related('student', 'event', 'variant')

        marks = Mark.objects.filter(
            participation__in=participations
        ).select_related('participation')

        # Lookup: (student_id, event_id) → participation
        part_lookup = {}
        for p in participations:
            part_lookup[(p.student_id, p.event_id)] = p

        # Lookup: participation_id → mark
        mark_lookup = {}
        for m in marks:
            mark_lookup[m.participation_id] = m

        # Строим строки журнала
        rows = []
        for student in students:
            cells = []
            total_score = 0
            score_count = 0
            debts = 0

            for event in events:
                participation = part_lookup.get((student.id, event.id))
                mark = mark_lookup.get(participation.id) if participation else None

                cell = {
                    'event': event,
                    'participation': participation,
                    'mark': mark,
                    'score': None,
                    'status': 'missing',
                    'css_class': '',
                    'display': '',
                    'variant': participation.variant if participation else None,
                }

                if participation:
                    if participation.status == 'absent':
                        cell['status'] = 'absent'
                        cell['display'] = 'Н'
                        cell['css_class'] = 'journal-absent'
                        debts += 1
                    elif mark and mark.score is not None:
                        cell['status'] = 'graded'
                        cell['score'] = mark.score
                        cell['display'] = str(mark.score)
                        total_score += mark.score
                        score_count += 1
                        if mark.score >= 5:
                            cell['css_class'] = 'journal-5'
                        elif mark.score == 4:
                            cell['css_class'] = 'journal-4'
                        elif mark.score == 3:
                            cell['css_class'] = 'journal-3'
                        else:
                            cell['css_class'] = 'journal-2'
                    elif participation.status in ('assigned', 'started'):
                        cell['status'] = 'in_progress'
                        cell['display'] = '…'
                        cell['css_class'] = 'journal-progress'
                    elif participation.status == 'completed':
                        cell['status'] = 'completed'
                        cell['display'] = '✓'
                        cell['css_class'] = 'journal-completed'
                    else:
                        cell['status'] = 'assigned'
                        cell['display'] = '–'
                else:
                    # Нет участия — долг
                    cell['status'] = 'missing'
                    cell['display'] = ''
                    cell['css_class'] = 'journal-missing'
                    debts += 1

                cells.append(cell)

            avg_score = round(total_score / score_count, 1) if score_count > 0 else None

            rows.append({
                'student': student,
                'cells': cells,
                'avg_score': avg_score,
                'score_count': score_count,
                'debts': debts,
            })

        # Фильтр «только долги»
        show_debts_only = self.request.GET.get('debts') == '1'
        all_rows = rows
        if show_debts_only:
            rows = [r for r in rows if r['debts'] > 0]

        # Итоговая статистика по столбцам (событиям)
        event_stats = []
        for event in events:
            graded = 0
            absent = 0
            missing = 0
            total = 0
            for row in all_rows:
                for cell in row['cells']:
                    if cell['event'].id == event.id:
                        total += 1
                        if cell['status'] == 'graded':
                            graded += 1
                        elif cell['status'] == 'absent':
                            absent += 1
                        elif cell['status'] == 'missing':
                            missing += 1
            event_stats.append({
                'event': event,
                'graded': graded,
                'absent': absent,
                'missing': missing,
                'total': total,
            })

        context.update({
            'course': course,
            'group': group,
            'events': events,
            'event_stats': event_stats,
            'rows': rows,
            'all_rows_count': len(all_rows),
            'show_debts_only': show_debts_only,
            'total_debts': sum(r['debts'] for r in all_rows),
            'students_with_debts': sum(1 for r in all_rows if r['debts'] > 0),
        })

        year = getattr(self.request, 'current_year', None)
        context.update(_get_nav_context('journal', year=year))
        return context

# ============================================================
# ТЕХНИЧЕСКИЕ ОТЧЁТЫ (здоровье базы заданий)
# ============================================================

class TaskDBHealthView(TemplateView):
    """Здоровье базы заданий"""
    template_name = 'reports/db_health.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        from works.models import Work, Variant, VariantTask, WorkAnalogGroup
        from task_groups.models import AnalogGroup, TaskGroup

        # === Общая статистика ===
        total_tasks = Task.objects.count()
        total_groups_qs = AnalogGroup.objects.annotate(
            task_count=Count('taskgroup')
        )
        total_works = Work.objects.count()
        total_variants = Variant.objects.count()

        context['stats'] = {
            'total_tasks': total_tasks,
            'total_groups': total_groups_qs.count(),
            'total_works': total_works,
            'total_variants': total_variants,
        }

        # === Варианты-сироты ===
        orphan_variants = Variant.objects.filter(work__isnull=True)
        context['orphan_variants'] = {
            'count': orphan_variants.count(),
            'items': orphan_variants.order_by('-created_at')[:10],
        }

        # === Пустые группы ===
        empty_groups = total_groups_qs.filter(task_count=0)
        context['empty_groups'] = {
            'count': empty_groups.count(),
            'items': empty_groups.order_by('name')[:20],
        }

        # === Группы с недостаточным покрытием ===
        coverage_issues = []
        for wag in WorkAnalogGroup.objects.select_related(
            'work', 'analog_group'
        ).annotate(
            available=Count('analog_group__taskgroup')
        ):
            if wag.available < wag.count:
                coverage_issues.append({
                    'work': wag.work,
                    'group': wag.analog_group,
                    'needed': wag.count,
                    'available': wag.available,
                    'deficit': wag.count - wag.available,
                })
        context['coverage_issues'] = {
            'count': len(coverage_issues),
            'items': coverage_issues[:20],
        }

        # === Распределение сложности ===
        difficulty_dist = []
        for item in Task.objects.values('difficulty').annotate(
            count=Count('id')
        ).order_by('difficulty'):
            d = item['difficulty'] or 0
            cnt = item['count']
            pct = round(cnt / total_tasks * 100, 1) if total_tasks else 0
            difficulty_dist.append({
                'difficulty': d,
                'count': cnt,
                'pct': pct,
            })
        context['difficulty_dist'] = difficulty_dist

        # === Задания без группы ===
        tasks_in_groups = set(
            TaskGroup.objects.values_list('task_id', flat=True)
        )
        ungrouped_count = Task.objects.exclude(id__in=tasks_in_groups).count()
        context['ungrouped_tasks'] = {
            'count': ungrouped_count,
            'pct': round(ungrouped_count / total_tasks * 100, 1) if total_tasks else 0,
        }

        # === Хрупкие группы (1 задание) ===
        fragile_groups = total_groups_qs.filter(task_count=1)
        context['fragile_groups'] = {
            'count': fragile_groups.count(),
            'items': fragile_groups.order_by('name')[:20],
        }

        # === Работы без вариантов ===
        works_no_variants = Work.objects.annotate(
            variant_count=Count('variant')
        ).filter(variant_count=0)
        context['works_no_variants'] = {
            'count': works_no_variants.count(),
            'items': works_no_variants[:10],
        }

        # === Работы без спецификации ===
        works_no_spec = Work.objects.annotate(
            spec_count=Count('workanaloggroup')
        ).filter(spec_count=0)
        context['works_no_spec'] = {
            'count': works_no_spec.count(),
            'items': works_no_spec[:10],
        }

        # === Распределение по типу задания ===
        type_dist = list(
            Task.objects.values('task_type').annotate(
                count=Count('id')
            ).order_by('-count')
        )
        # Подставляем human-readable названия
        type_labels = dict(Task.TASK_TYPE_CHOICES) if hasattr(Task, 'TASK_TYPE_CHOICES') else {}
        for item in type_dist:
            item['pct'] = round(item['count'] / total_tasks * 100, 1) if total_tasks else 0
            item['label'] = type_labels.get(item['task_type'], item['task_type'] or '—')
        context['type_dist'] = type_dist

        # === Самые «популярные» задания (в наибольшем кол-ве вариантов) ===
        most_used = Task.objects.annotate(
            variant_count=Count('varianttask')
        ).filter(variant_count__gt=0).order_by('-variant_count')[:10]
        context['most_used_tasks'] = most_used

        # === Распределение размера групп ===
        group_sizes = list(
            total_groups_qs.values('task_count').annotate(
                group_count=Count('id')
            ).order_by('task_count')
        )
        context['group_sizes'] = group_sizes
        # === Непроверенные задания ===
        unverified_count = Task.objects.filter(is_verified=False).count()
        context['unverified_tasks'] = {
            'count': unverified_count,
            'pct': round(unverified_count / total_tasks * 100, 1) if total_tasks else 0,
        }

        # === Задания без источника ===
        no_source_count = Task.objects.filter(source__isnull=True).count()
        context['no_source_tasks'] = {
            'count': no_source_count,
            'pct': round(no_source_count / total_tasks * 100, 1) if total_tasks else 0,
        }

        # === Задания без класса ===
        no_grade_count = Task.objects.filter(grade__isnull=True).count()
        context['no_grade_tasks'] = {
            'count': no_grade_count,
            'pct': round(no_grade_count / total_tasks * 100, 1) if total_tasks else 0,
        }

        # === Общий «индекс здоровья» ===
        issues = (
            context['orphan_variants']['count']
            + context['empty_groups']['count']
            + context['coverage_issues']['count']
            + context['ungrouped_tasks']['count']
            + context['fragile_groups']['count']
            + context['works_no_variants']['count']
            + context['works_no_spec']['count']
        )
        if issues == 0:
            health = {'label': 'Отлично', 'color': 'success', 'icon': 'check-circle'}
        elif issues <= 5:
            health = {'label': 'Хорошо', 'color': 'info', 'icon': 'info-circle'}
        elif issues <= 15:
            health = {'label': 'Есть замечания', 'color': 'warning', 'icon': 'exclamation-triangle'}
        else:
            health = {'label': 'Требует внимания', 'color': 'danger', 'icon': 'exclamation-circle'}
        health['issues'] = issues
        
        # Склонение
        if 11 <= issues % 100 <= 19:
            health['issues_text'] = f'{issues} замечаний'
        elif issues % 10 == 1:
            health['issues_text'] = f'{issues} замечание'
        elif 2 <= issues % 10 <= 4:
            health['issues_text'] = f'{issues} замечания'
        else:
            health['issues_text'] = f'{issues} замечаний'
        
        context['health'] = health


        context.update(_get_nav_context('db-health'))
        return context
