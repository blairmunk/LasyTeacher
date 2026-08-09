"""Build Django template data for heatmap reports."""

from django.urls import reverse

from reports import plotly_utils


class HeatmapPresenter:
    def heatmap_group_url_params_from_query(self, query):
        return self.heatmap_group_url_params(query.get('group'))

    def heatmap_group_url_params(self, group_id):
        return {
            'group_param': f'?group={group_id}' if group_id else '',
            'group_suffix': f'&group={group_id}' if group_id else '',
        }

    def heatmap_toggle_url(self, query, path=''):
        toggle_params = query.copy()
        if query.get('transpose') == '1':
            toggle_params.pop('transpose', None)
        else:
            toggle_params['transpose'] = '1'
        encoded_params = toggle_params.urlencode()
        if path:
            return f'{path}?{encoded_params}'
        return f'?{encoded_params}' if encoded_params else '?'

    def heatmap_topic_matrix_context(
        self,
        matrix,
        *,
        transpose=False,
        group_id='',
    ):
        columns = matrix.columns
        rows = matrix.rows
        col_averages = matrix.col_averages
        group_param = f'?group={group_id}' if group_id else ''

        if not transpose:
            return {
                'group_param': group_param,
                'grid_row_header': 'Ученик',
                'grid_rows': [
                    {
                        'label': row['student'].short_name,
                        'url': reverse(
                            'students:detail',
                            args=[row['student'].pk],
                        ),
                        'cells': row['cells'],
                        'avg': row['avg'],
                        'avg_css': row['avg_css'],
                    }
                    for row in rows
                ],
                'grid_col_headers': [
                    {
                        'label': topic.name,
                        'title': f'{topic.section} → {topic.name}',
                    }
                    for topic in columns
                ],
                'grid_col_averages': col_averages,
                'has_data': bool(rows and columns),
            }

        return {
            'group_param': group_param,
            'grid_row_header': 'Тема',
            'grid_rows': [
                {
                    'label': topic.name,
                    'url': (
                        reverse(
                            'reports:heatmap-drilldown',
                            args=[topic.pk],
                        )
                        + group_param
                    ),
                    'cells': [
                        row['cells'][column_index]
                        for row in rows
                    ],
                    'avg': col_averages[column_index]['pct'],
                    'avg_css': col_averages[column_index]['css'],
                }
                for column_index, topic in enumerate(columns)
            ],
            'grid_col_headers': [
                {
                    'label': row['student'].short_name,
                    'title': row['student'].full_name,
                }
                for row in rows
            ],
            'grid_col_averages': [
                {'pct': row['avg'], 'css': row['avg_css']}
                for row in rows
            ],
            'has_data': bool(rows and columns),
        }

    def heatmap_subtopic_matrix_context(
        self,
        matrix,
        *,
        topic_id,
        transpose=False,
        group_id='',
    ):
        columns = matrix.columns
        rows = matrix.rows
        col_averages = matrix.col_averages
        group_params = self.heatmap_group_url_params(group_id)
        group_param = group_params['group_param']
        group_suffix = group_params['group_suffix']

        if not transpose:
            grid_rows = []
            for row in rows:
                student_id = row['student'].pk
                cells = [
                    {
                        **cell,
                        'url': self._heatmap_student_cell_url(
                            topic_id=topic_id,
                            student_id=student_id,
                            subtopic_id=columns[index].pk,
                            group_suffix=group_suffix,
                            has_data=cell['pct'] is not None,
                        ),
                    }
                    for index, cell in enumerate(row['cells'])
                ]
                grid_rows.append({
                    'label': row['student'].short_name,
                    'url': (
                        reverse(
                            'reports:heatmap-student',
                            args=[topic_id, student_id],
                        )
                        + group_param
                    ),
                    'cells': cells,
                    'avg': row['avg'],
                    'avg_css': row['avg_css'],
                })
            return {
                **group_params,
                'grid_row_header': 'Ученик',
                'grid_rows': grid_rows,
                'grid_col_headers': [
                    {
                        'label': subtopic.name,
                        'title': subtopic.name,
                        'url': (
                            reverse(
                                'reports:heatmap-subtopic',
                                args=[subtopic.pk],
                            )
                            + group_param
                        ),
                    }
                    for subtopic in columns
                ],
                'grid_col_averages': col_averages,
                'has_data': bool(rows and columns),
            }

        grid_rows = []
        for column_index, subtopic in enumerate(columns):
            cells = []
            for row in rows:
                cell = row['cells'][column_index]
                cells.append({
                    **cell,
                    'url': self._heatmap_student_cell_url(
                        topic_id=topic_id,
                        student_id=row['student'].pk,
                        subtopic_id=subtopic.pk,
                        group_suffix=group_suffix,
                        has_data=cell['pct'] is not None,
                    ),
                })
            grid_rows.append({
                'label': subtopic.name,
                'url': (
                    reverse(
                        'reports:heatmap-subtopic',
                        args=[subtopic.pk],
                    )
                    + group_param
                ),
                'cells': cells,
                'avg': col_averages[column_index]['pct'],
                'avg_css': col_averages[column_index]['css'],
            })
        return {
            **group_params,
            'grid_row_header': 'Подтема',
            'grid_rows': grid_rows,
            'grid_col_headers': [
                {
                    'label': row['student'].short_name,
                    'title': row['student'].full_name,
                    'url': (
                        reverse(
                            'reports:heatmap-student',
                            args=[topic_id, row['student'].pk],
                        )
                        + group_param
                    ),
                }
                for row in rows
            ],
            'grid_col_averages': [
                {'pct': row['avg'], 'css': row['avg_css']}
                for row in rows
            ],
            'has_data': bool(rows and columns),
        }

    def heatmap_subtopic_student_rows(self, detail):
        group_id = (
            detail.selected_group.pk
            if detail.selected_group
            else ''
        )
        group_params = self.heatmap_group_url_params(group_id)
        return {
            **group_params,
            'student_rows': [
                {
                    **row,
                    'url': self._heatmap_student_cell_url(
                        topic_id=detail.topic.pk,
                        student_id=row['student'].pk,
                        subtopic_id=detail.subtopic.pk,
                        group_suffix=group_params['group_suffix'],
                        has_data=row['pct'] is not None,
                    ),
                }
                for row in detail.student_rows
            ],
        }

    def heatmap_course_timeline_json(self, timeline):
        return plotly_utils.to_json({
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
                'title': {
                    'text': 'Динамика результатов',
                    'font': {'size': 16},
                },
                'xaxis': {'title': 'Дата'},
                'yaxis': {'title': '%', 'range': [0, 105]},
                'margin': {'t': 40, 'b': 40, 'l': 50, 'r': 20},
                'height': 300,
                'shapes': [
                    {
                        'type': 'line',
                        'y0': 70,
                        'y1': 70,
                        'x0': 0,
                        'x1': 1,
                        'xref': 'paper',
                        'line': {
                            'color': '#28a745',
                            'dash': 'dash',
                            'width': 1,
                        },
                    },
                    {
                        'type': 'line',
                        'y0': 45,
                        'y1': 45,
                        'x0': 0,
                        'x1': 1,
                        'xref': 'paper',
                        'line': {
                            'color': '#dc3545',
                            'dash': 'dash',
                            'width': 1,
                        },
                    },
                ],
            },
            'config': {'displayModeBar': False, 'responsive': True},
        })

    def _heatmap_student_cell_url(
        self,
        *,
        topic_id,
        student_id,
        subtopic_id,
        group_suffix='',
        has_data=True,
    ):
        if not has_data:
            return None
        return (
            reverse(
                'reports:heatmap-student',
                args=[topic_id, student_id],
            )
            + f'?subtopic={subtopic_id}{group_suffix}'
        )
