"""Infrastructure helpers for Django student forms."""

from core_logic.entities.student import SaveStudentGroupParams, SaveStudentParams
from reports import plotly_utils


class StudentFormAdapter:
    def student_params_from_form(self, form, student_id=''):
        return SaveStudentParams(
            student_id=student_id,
            first_name=form.cleaned_data['first_name'],
            last_name=form.cleaned_data['last_name'],
            middle_name=form.cleaned_data.get('middle_name', ''),
            email=form.cleaned_data.get('email', ''),
        )

    def student_form_initial(self, student):
        return {
            'first_name': student.first_name,
            'last_name': student.last_name,
            'middle_name': student.middle_name,
            'email': student.email,
        }

    def student_group_params_from_form(self, form, group_id=''):
        return SaveStudentGroupParams(
            group_id=group_id,
            name=form.cleaned_data['name'],
            student_ids=[
                str(student.pk)
                for student in form.cleaned_data.get('students', [])
            ],
        )

    def student_group_form_initial(self, group):
        return {
            'name': group.name,
            'students': [student.pk for student in group.students],
        }

    def student_detail_context(self, student, profile):
        context = {
            'student': student,
            'object': student,
            'student_groups': profile.student_groups,
            'participations_data': profile.participations_data,
            'stats': profile.stats,
            'group_scores': profile.group_scores,
            'task_log_stats': profile.task_log_stats,
            'heatmap_groups': profile.heatmap_groups,
            'heatmap_topics': profile.heatmap_topics,
            'heatmap_difficulty': profile.heatmap_difficulty,
            'recent_task_log': profile.recent_task_log,
        }
        context.update(self.student_profile_chart_context(student, profile))
        return context

    def student_remedial_context(self, student, remedial_data):
        context = {
            'student': student,
            'object': student,
        }
        if remedial_data.no_data:
            context['no_data'] = True
            return context

        context.update({
            'remedial_groups': remedial_data.remedial_groups,
            'weak_topics': remedial_data.weak_topics,
            'total_available': remedial_data.total_available,
            'done_count': remedial_data.done_count,
        })
        return context

    def remedial_wizard_start_context(self, start_data):
        return {
            'groups': start_data.groups,
            'limit_choices': start_data.limit_choices,
        }

    def remedial_wizard_preview_context(self, preview_data):
        return {
            'group': preview_data.group,
            'preview': preview_data.preview,
            'threshold': preview_data.threshold,
            'limit_type': preview_data.limit_type,
            'limit_value': preview_data.limit_value,
            'work_name': preview_data.work_name,
            'students_with_tasks': preview_data.students_with_tasks,
            'total_tasks': preview_data.total_tasks,
        }

    def remedial_event_preview_context(self, result):
        return {
            'event': result.event,
            'work': result.work,
            'analysis': result.analysis,
            'weak_students': result.weak_students,
        }

    def remedial_solutions_context(self, sheet_data):
        return {
            'variant': sheet_data.variant,
            'student': sheet_data.student,
            'source_work': sheet_data.source_work,
            'original_tasks': sheet_data.original_tasks,
            'new_tasks': sheet_data.new_tasks,
            'mark': sheet_data.mark,
        }

    def student_profile_chart_context(self, student, profile):
        context = {}
        if profile.group_scores:
            context['mini_heatmap_json'] = self._mini_heatmap_json(
                student,
                profile,
            )
        if profile.scores_timeline:
            context['dynamics_chart_json'] = self._dynamics_chart_json(profile)
        if profile.stats.get('graded_works', 0) > 0:
            context['score_chart_json'] = plotly_utils.to_json(
                plotly_utils.score_distribution_config(
                    profile.stats.get('score_counts', {}),
                    title='Распределение оценок',
                )
            )
        return context

    def _mini_heatmap_json(self, student, profile):
        group_names = [group['name'] for group in profile.group_scores]
        heatmap_chart = plotly_utils.heatmap_config(
            students=[student.short_name],
            groups=group_names,
            matrix=[[group['avg'] for group in profile.group_scores]],
            title='Успеваемость по темам',
        )
        heatmap_chart['layout']['height'] = 150
        heatmap_chart['layout']['margin'] = {
            'l': 250,
            't': 50,
            'r': 80,
            'b': 30,
        }
        return plotly_utils.to_json(heatmap_chart)

    def _dynamics_chart_json(self, profile):
        scores_timeline = list(reversed(profile.scores_timeline))
        dates = [point.date for point in scores_timeline]
        scores_vals = [point.score for point in scores_timeline]
        hover_texts = [
            f"{point.work}<br>Оценка: <b>{point.score}</b>"
            for point in scores_timeline
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
                        self._score_color(score)
                        for score in scores_vals
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
                'shapes': self._average_score_shapes(
                    dates,
                    profile.stats.get('avg_score', 0),
                ),
            },
            'config': {'responsive': True, 'displayModeBar': False},
        }
        return plotly_utils.to_json(dynamics_chart)

    def _average_score_shapes(self, dates, avg_score):
        if len(dates) <= 1:
            return []
        return [{
            'type': 'line',
            'x0': dates[0],
            'x1': dates[-1],
            'y0': avg_score,
            'y1': avg_score,
            'line': {
                'color': 'rgba(255,0,0,0.3)',
                'width': 1,
                'dash': 'dash',
            },
        }]

    def _score_color(self, score):
        if score <= 2:
            return 'rgba(220,53,69,0.7)'
        if score <= 3:
            return 'rgba(255,193,7,0.7)'
        if score <= 4:
            return 'rgba(40,167,69,0.7)'
        return 'rgba(13,110,253,0.7)'
