# reports/plotly_utils.py

import json

# ─── Цветовая палитра ────────────────────────────────────────
COLORS = {
    'primary': 'rgba(13, 110, 253, 0.75)',
    'success': 'rgba(40, 167, 69, 0.75)',
    'warning': 'rgba(255, 193, 7, 0.75)',
    'danger': 'rgba(220, 53, 69, 0.75)',
    'info': 'rgba(23, 162, 184, 0.75)',
    'purple': 'rgba(111, 66, 193, 0.75)',
    'teal': 'rgba(32, 201, 151, 0.75)',
}

SCORE_COLORS = {
    2: 'rgba(220, 53, 69, 0.65)',
    3: 'rgba(255, 193, 7, 0.65)',
    4: 'rgba(40, 167, 69, 0.65)',
    5: 'rgba(13, 110, 253, 0.65)',
}

BASE_LAYOUT = {
    'paper_bgcolor': '#fff',
    'plot_bgcolor': '#f8f9fa',
    'font': {'family': 'system-ui, -apple-system, sans-serif', 'size': 12},
}

COMPACT_CONFIG = {'responsive': True, 'displayModeBar': False}


def _merge_layout(base, custom):
    """Мерджит layout с базовыми настройками"""
    result = {**BASE_LAYOUT, **custom}
    return result


# ─── Heatmap ──────────────────────────────────────────────────

def heatmap_config(students, groups, matrix, title=''):
    """Тепловая карта: X — ученики, Y — темы"""
    t_matrix = []
    t_hover = []

    for j in range(len(groups)):
        z_row = []
        hover_row = []
        for i in range(len(students)):
            val = matrix[i][j]
            if val is None:
                z_row.append(0)
                hover_row.append(
                    f'<b>{students[i]}</b><br>{groups[j]}<br>Нет данных'
                )
            else:
                z_row.append(val)
                if val >= 4.5:
                    grade_text = '⭐ Отлично'
                elif val >= 3.5:
                    grade_text = '✅ Хорошо'
                elif val >= 2.5:
                    grade_text = '⚠️ Удовл.'
                else:
                    grade_text = '❌ Неудовл.'
                hover_row.append(
                    f'<b>{students[i]}</b><br>{groups[j]}'
                    f'<br>Балл: <b>{val:.1f}</b>'
                    f'<br>{grade_text}'
                )
        t_matrix.append(z_row)
        t_hover.append(hover_row)

    return {
        'data': [{
            'type': 'heatmap',
            'z': t_matrix,
            'x': students,
            'y': groups,
            'text': t_hover,
            'hoverinfo': 'text',
            'colorscale': [
                [0, 'rgba(220, 53, 69, 0.55)'],
                [0.33, 'rgba(255, 193, 7, 0.55)'],
                [0.66, 'rgba(40, 167, 69, 0.55)'],
                [1, 'rgba(13, 110, 253, 0.55)'],
            ],
            'zmin': 2,
            'zmax': 5,
            'colorbar': {
                'title': 'Балл',
                'tickvals': [2, 3, 4, 5],
                'ticktext': ['2', '3', '4', '5'],
            },
            'xgap': 2,
            'ygap': 2,
        }],
        'layout': _merge_layout(BASE_LAYOUT, {
            'title': title,
            'xaxis': {
                'title': '', 'side': 'top',
                'tickangle': -45, 'tickfont': {'size': 11},
            },
            'yaxis': {
                'title': '', 'tickfont': {'size': 11},
                'autorange': 'reversed',
            },
            'margin': {'l': 250, 't': 140, 'r': 80, 'b': 30},
            'width': max(600, len(students) * 45 + 300),
            'height': max(400, len(groups) * 40 + 180),
        }),
        'config': {
            'responsive': True,
            'displayModeBar': True,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
            'locale': 'ru',
        },
    }


# ─── Распределение оценок ────────────────────────────────────

def score_distribution_config(scores_dict, title='Распределение оценок'):
    """Столбчатая диаграмма оценок 2-5"""
    labels = ['2', '3', '4', '5']
    values = [scores_dict.get(i, 0) for i in [2, 3, 4, 5]]
    colors = [SCORE_COLORS[i] for i in [2, 3, 4, 5]]

    return {
        'data': [{
            'type': 'bar',
            'x': labels,
            'y': values,
            'marker': {'color': colors, 'line': {'width': 1, 'color': '#fff'}},
            'text': values,
            'textposition': 'auto',
            'textfont': {'size': 14, 'color': '#333'},
        }],
        'layout': _merge_layout(BASE_LAYOUT, {
            'title': {'text': title, 'font': {'size': 14}},
            'xaxis': {'title': 'Оценка'},
            'yaxis': {'title': 'Количество', 'gridcolor': '#e9ecef'},
            'margin': {'l': 50, 't': 50, 'r': 20, 'b': 50},
            'height': 300,
            'bargap': 0.3,
        }),
        'config': COMPACT_CONFIG,
    }


# ─── Gauge (спидометр) ───────────────────────────────────────

def gauge_config(value, title='Средний балл', min_val=2, max_val=5):
    """Gauge-метр среднего балла"""
    if value <= 2.5:
        bar_color = 'rgba(220, 53, 69, 0.85)'
    elif value <= 3.5:
        bar_color = 'rgba(255, 193, 7, 0.85)'
    elif value <= 4.2:
        bar_color = 'rgba(40, 167, 69, 0.85)'
    else:
        bar_color = 'rgba(13, 110, 253, 0.85)'

    return {
        'data': [{
            'type': 'indicator',
            'mode': 'gauge+number',
            'value': round(value, 2),
            'number': {'font': {'size': 36}, 'suffix': ''},
            'gauge': {
                'axis': {
                    'range': [min_val, max_val],
                    'tickvals': [2, 3, 4, 5],
                    'ticktext': ['2', '3', '4', '5'],
                },
                'bar': {'color': bar_color, 'thickness': 0.75},
                'bgcolor': '#f0f0f0',
                'steps': [
                    {'range': [2, 3], 'color': 'rgba(220, 53, 69, 0.15)'},
                    {'range': [3, 4], 'color': 'rgba(255, 193, 7, 0.15)'},
                    {'range': [4, 4.5], 'color': 'rgba(40, 167, 69, 0.15)'},
                    {'range': [4.5, 5], 'color': 'rgba(13, 110, 253, 0.15)'},
                ],
                'threshold': {
                    'line': {'color': '#333', 'width': 3},
                    'thickness': 0.8,
                    'value': value,
                },
            },
        }],
        'layout': _merge_layout(BASE_LAYOUT, {
            'title': {'text': title, 'font': {'size': 14}},
            'margin': {'l': 30, 't': 50, 'r': 30, 'b': 10},
            'height': 250,
        }),
        'config': COMPACT_CONFIG,
    }


# ─── Donut (кольцевая) ───────────────────────────────────────

def donut_config(labels, values, title='', colors=None):
    """Кольцевая диаграмма"""
    if colors is None:
        default_colors = [
            COLORS['info'], COLORS['success'], COLORS['primary'],
            COLORS['warning'], COLORS['danger'], COLORS['purple'],
        ]
        colors = default_colors[:len(labels)]

    return {
        'data': [{
            'type': 'pie',
            'labels': labels,
            'values': values,
            'hole': 0.5,
            'marker': {
                'colors': colors,
                'line': {'color': '#fff', 'width': 2},
            },
            'textinfo': 'label+value',
            'textposition': 'outside',
            'textfont': {'size': 11},
            'hovertemplate': '<b>%{label}</b><br>%{value} (%{percent})<extra></extra>',
        }],
        'layout': _merge_layout(BASE_LAYOUT, {
            'title': {'text': title, 'font': {'size': 14}},
            'margin': {'l': 20, 't': 50, 'r': 20, 'b': 20},
            'height': 300,
            'showlegend': False,
        }),
        'config': COMPACT_CONFIG,
    }


# ─── Box-plot ─────────────────────────────────────────────────

def box_plot_config(data_series, title='Распределение по работам'):
    """Box-plot для сравнения распределений"""
    traces = []
    colors_list = [
        COLORS['primary'], COLORS['success'], COLORS['warning'],
        COLORS['danger'], COLORS['purple'], COLORS['teal'],
    ]

    for i, (name, values) in enumerate(data_series.items()):
        traces.append({
            'type': 'box',
            'y': values,
            'name': name,
            'marker': {'color': colors_list[i % len(colors_list)]},
            'boxmean': True,
        })

    return {
        'data': traces,
        'layout': _merge_layout(BASE_LAYOUT, {
            'title': {'text': title, 'font': {'size': 14}},
            'yaxis': {
                'title': 'Оценка',
                'range': [1.5, 5.5],
                'gridcolor': '#e9ecef',
                'dtick': 1,
            },
            'margin': {'l': 50, 't': 50, 'r': 20, 'b': 80},
            'height': 350,
            'showlegend': False,
        }),
        'config': COMPACT_CONFIG,
    }


# ─── Multi-bar ────────────────────────────────────────────────

def multi_bar_config(categories, series, title=''):
    """Группированная столбчатая диаграмма"""
    colors_list = list(COLORS.values())
    data = []
    for i, (name, values) in enumerate(series.items()):
        data.append({
            'type': 'bar',
            'name': name,
            'x': categories,
            'y': values,
            'marker': {'color': colors_list[i % len(colors_list)]},
        })

    return {
        'data': data,
        'layout': _merge_layout(BASE_LAYOUT, {
            'title': {'text': title, 'font': {'size': 14}},
            'barmode': 'group',
            'margin': {'l': 50, 't': 50, 'r': 20, 'b': 80},
            'height': 350,
            'legend': {'orientation': 'h', 'y': -0.2},
        }),
        'config': COMPACT_CONFIG,
    }


# ─── Line chart ───────────────────────────────────────────────

def line_chart_config(x_labels, y_values, title='', color=None):
    """Линейный график с заливкой"""
    color = color or COLORS['primary']

    return {
        'data': [{
            'type': 'scatter',
            'mode': 'lines+markers',
            'x': x_labels,
            'y': y_values,
            'line': {'color': color, 'width': 2.5, 'shape': 'spline'},
            'marker': {'size': 8, 'color': color},
            'fill': 'tozeroy',
            'fillcolor': color.replace('0.75', '0.1'),
        }],
        'layout': _merge_layout(BASE_LAYOUT, {
            'title': {'text': title, 'font': {'size': 14}},
            'margin': {'l': 50, 't': 50, 'r': 20, 'b': 50},
            'height': 300,
            'xaxis': {'gridcolor': '#e9ecef'},
            'yaxis': {'gridcolor': '#e9ecef'},
        }),
        'config': COMPACT_CONFIG,
    }


# ─── JSON serializer ─────────────────────────────────────────

def to_json(config):
    """Безопасная сериализация в JSON для шаблона"""
    return json.dumps(config, ensure_ascii=False)
