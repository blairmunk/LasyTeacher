# reports/views.py

import json
from django.urls import reverse
from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView
from django.utils import timezone

from core_logic.use_cases.get_events_status_report import (
    EventsStatusReportRequest,
)
from core_logic.use_cases.get_heatmap_course_overview import (
    HeatmapCourseOverviewRequest,
)
from core_logic.use_cases.get_heatmap_course_topic_matrix import (
    HeatmapCourseTopicMatrixRequest,
)
from core_logic.use_cases.get_heatmap_course_timeline import (
    HeatmapCourseTimelineRequest,
)
from core_logic.use_cases.get_heatmap_drilldown_overview import (
    HeatmapDrilldownOverviewRequest,
)
from core_logic.use_cases.get_heatmap_overview import HeatmapOverviewRequest
from core_logic.use_cases.get_heatmap_student_detail import (
    HeatmapStudentDetailRequest,
)
from core_logic.use_cases.get_heatmap_subtopic_detail import (
    HeatmapSubtopicDetailRequest,
)
from core_logic.use_cases.get_heatmap_subtopic_matrix import (
    HeatmapSubtopicMatrixRequest,
)
from core_logic.use_cases.get_heatmap_topic_matrix import (
    HeatmapTopicMatrixRequest,
)
from core_logic.use_cases.get_journal import JournalRequest
from core_logic.use_cases.get_journal_select import JournalSelectRequest
from core_logic.use_cases.get_reports_dashboard import ReportsDashboardRequest
from core_logic.use_cases.get_student_performance_report import (
    StudentPerformanceReportRequest,
)
from core_logic.use_cases.get_work_analysis_report import WorkAnalysisReportRequest
from infrastructure.container import container
from . import plotly_utils


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

        matrix = container.get_heatmap_topic_matrix_use_case().execute(
            HeatmapTopicMatrixRequest(
                student_ids=[student.pk for student in students],
                section_filter=section,
            ),
        )
        columns = matrix.columns
        rows = matrix.rows
        col_averages = matrix.col_averages
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
        group_id = request.GET.get('group')
        transpose = request.GET.get('transpose') == '1'
        overview = container.get_heatmap_course_overview_use_case().execute(
            HeatmapCourseOverviewRequest(
                course_id=course_pk,
                group_id=group_id,
            ),
        )
        course = overview.course
        course_groups = overview.groups
        group = overview.selected_group
        students = overview.students
        student_ids = [student.pk for student in students]
        work_ids = [work.pk for work in overview.course_works]

        if not students:
            return render(request, 'reports/heatmap_course.html', {
                'course': course,
                'groups': course_groups,
                'selected_group': group,
                'has_data': False,
                'is_transposed': transpose,
                'active_report': overview.active_report,
                'active_course_pk': overview.active_course_pk,
                'courses': overview.courses,
            })

        matrix = container.get_heatmap_course_topic_matrix_use_case().execute(
            HeatmapCourseTopicMatrixRequest(
                student_ids=student_ids,
                work_ids=work_ids,
            ),
        )
        columns = matrix.columns
        rows = matrix.rows
        col_averages = matrix.col_averages
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

        timeline = container.get_heatmap_course_timeline_use_case().execute(
            HeatmapCourseTimelineRequest(
                student_ids=student_ids,
                work_ids=work_ids,
            ),
        )
        timeline_json = _build_course_timeline_json(timeline)

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
            'active_report': overview.active_report,
            'active_course_pk': overview.active_course_pk,
            'courses': overview.courses,
        })


class HeatmapDrilldownView(View):
    """Drill-down: ученики x подтемы одной темы"""

    def get(self, request, topic_pk):
        group_id = request.GET.get('group')
        transpose = request.GET.get('transpose') == '1'
        overview = container.get_heatmap_drilldown_overview_use_case().execute(
            HeatmapDrilldownOverviewRequest(
                topic_id=topic_pk,
                group_id=group_id,
            ),
        )

        topic = overview.topic
        groups = overview.groups
        group = overview.selected_group
        students = overview.students
        matrix = container.get_heatmap_subtopic_matrix_use_case().execute(
            HeatmapSubtopicMatrixRequest(
                student_ids=[student.pk for student in students],
                topic_id=topic_pk,
            ),
        )
        columns = matrix.columns
        rows = matrix.rows
        col_averages = matrix.col_averages
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
            'active_report': overview.active_report,
            'active_course_pk': overview.active_course_pk,
            'courses': overview.courses,
        })


class HeatmapStudentView(View):
    """Детальный вид: один ученик × подтемы одной темы"""

    def get(self, request, topic_pk, student_pk):
        subtopic_id = request.GET.get('subtopic')
        group_id = request.GET.get('group')
        group_param = f'?group={group_id}' if group_id else ''
        group_suffix = f'&group={group_id}' if group_id else ''
        detail = container.get_heatmap_student_detail_use_case().execute(
            HeatmapStudentDetailRequest(
                topic_id=topic_pk,
                student_id=student_pk,
                subtopic_id=subtopic_id,
            ),
        )

        return render(request, 'reports/heatmap_student.html', {
            'topic': detail.topic,
            'student': detail.student,
            'details': detail.details,
            'subtopic_summary': detail.subtopic_summary,
            'selected_subtopic': detail.selected_subtopic,
            'group_param': group_param,
            'group_suffix': group_suffix,
            'active_report': detail.active_report,
            'active_course_pk': detail.active_course_pk,
            'courses': detail.courses,
        })


class HeatmapSubtopicView(View):
    """Анализ подтемы: все ученики × задания одной подтемы"""

    def get(self, request, subtopic_pk):
        group_id = request.GET.get('group')
        detail = container.get_heatmap_subtopic_detail_use_case().execute(
            HeatmapSubtopicDetailRequest(
                subtopic_id=subtopic_pk,
                group_id=group_id,
            ),
        )
        group_param = (
            f'?group={detail.selected_group.pk}'
            if detail.selected_group
            else ''
        )
        group_suffix = (
            f'&group={detail.selected_group.pk}'
            if detail.selected_group
            else ''
        )
        student_rows = []
        for row in detail.student_rows:
            url = None
            if row['pct'] is not None:
                url = (
                    reverse(
                        'reports:heatmap-student',
                        args=[detail.topic.pk, row['student'].pk],
                    )
                    + f'?subtopic={detail.subtopic.pk}{group_suffix}'
                )
            student_rows.append({**row, 'url': url})

        return render(request, 'reports/heatmap_subtopic.html', {
            'subtopic': detail.subtopic,
            'topic': detail.topic,
            'groups': detail.groups,
            'selected_group': detail.selected_group,
            'group_param': group_param,
            'student_rows': student_rows,
            'task_rows': detail.task_rows,
            'overall_pct': detail.overall_pct,
            'overall_css': detail.overall_css,
            'total_students': detail.total_students,
            'students_with_data': detail.students_with_data,
            'active_report': detail.active_report,
            'active_course_pk': detail.active_course_pk,
            'courses': detail.courses,
        })


# ============================================================
# Общие функции
# ============================================================

def _build_course_timeline_json(timeline):
    """Plotly JSON for course result timeline."""
    chart = {
        'data': [{
            'x': timeline.dates,
            'y': timeline.averages,
            'text': timeline.labels,
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
        year = getattr(self.request, 'current_year', None)
        journal = container.get_journal_select_use_case().execute(
            JournalSelectRequest(year=year),
        )
        context.update({
            'journal_links': journal.journal_links,
            'courses': journal.courses,
            'groups': journal.groups,
            'active_report': journal.active_report,
            'active_course_pk': journal.active_course_pk,
        })
        return context


class JournalView(TemplateView):
    """Классный журнал — ученики × события"""
    template_name = 'reports/journal.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        show_debts_only = self.request.GET.get('debts') == '1'
        journal = container.get_journal_use_case().execute(
            JournalRequest(
                course_id=kwargs['course_pk'],
                group_id=kwargs['group_pk'],
                year=getattr(self.request, 'current_year', None),
                show_debts_only=show_debts_only,
            ),
        )

        context.update({
            'course': journal.course,
            'group': journal.group,
            'events': journal.events,
            'event_stats': journal.event_stats,
            'rows': journal.rows,
            'all_rows_count': journal.all_rows_count,
            'show_debts_only': journal.show_debts_only,
            'total_debts': journal.total_debts,
            'students_with_debts': journal.students_with_debts,
            'active_report': journal.active_report,
            'active_course_pk': journal.active_course_pk,
            'courses': journal.courses,
        })
        return context

# ============================================================
# ТЕХНИЧЕСКИЕ ОТЧЁТЫ (здоровье базы заданий)
# ============================================================

class TaskDBHealthView(TemplateView):
    """Здоровье базы заданий"""
    template_name = 'reports/db_health.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        health = container.get_task_db_health_use_case().execute()

        context.update({
            'stats': health.stats,
            'orphan_variants': health.orphan_variants,
            'empty_groups': health.empty_groups,
            'coverage_issues': health.coverage_issues,
            'difficulty_dist': health.difficulty_dist,
            'ungrouped_tasks': health.ungrouped_tasks,
            'fragile_groups': health.fragile_groups,
            'works_no_variants': health.works_no_variants,
            'works_no_spec': health.works_no_spec,
            'type_dist': health.type_dist,
            'most_used_tasks': health.most_used_tasks,
            'group_sizes': health.group_sizes,
            'unverified_tasks': health.unverified_tasks,
            'no_source_tasks': health.no_source_tasks,
            'no_grade_tasks': health.no_grade_tasks,
            'health': health.health,
            'active_report': health.active_report,
            'active_course_pk': health.active_course_pk,
            'courses': health.courses,
        })
        return context
