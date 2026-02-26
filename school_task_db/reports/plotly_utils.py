# reports/plotly_utils.py

import json


def heatmap_config(students, groups, matrix, title=''):
    """
    Генерирует конфиг Plotly heatmap.
    Оси: X — ученики, Y — темы (группы аналогов)
    """
    
    # Транспонируем матрицу: было [студент][группа], станет [группа][студент]
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
            'x': students,       # ← ученики по горизонтали
            'y': groups,          # ← темы по вертикали
            'text': t_hover,
            'hoverinfo': 'text',
            'colorscale': [
                [0, 'rgba(220, 53, 69, 0.55)'],     # 2 — красный
                [0.33, 'rgba(255, 193, 7, 0.55)'],   # 3 — жёлтый
                [0.66, 'rgba(40, 167, 69, 0.55)'],   # 4 — зелёный
                [1, 'rgba(13, 110, 253, 0.55)'],     # 5 — синий
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
        'layout': {
            'title': title,
            'xaxis': {
                'title': '',
                'side': 'top',
                'tickangle': -45,
                'tickfont': {'size': 11},
            },
            'yaxis': {
                'title': '',
                'tickfont': {'size': 11},
                'autorange': 'reversed',
            },
            'margin': {'l': 250, 't': 140, 'r': 80, 'b': 30},
            'width': max(600, len(students) * 45 + 300),
            'height': max(400, len(groups) * 40 + 180),
            'paper_bgcolor': '#fff',
            'plot_bgcolor': '#f8f9fa',
        },
        'config': {
            'responsive': True,
            'displayModeBar': True,
            'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
            'toImageButtonOptions': {
                'format': 'png',
                'filename': 'heatmap',
                'width': max(600, len(students) * 45 + 300),
                'height': max(400, len(groups) * 40 + 180),
                'scale': 2,
            },
            'locale': 'ru',
        },
    }


def bar_chart_config(labels, values, title='', color='#0d6efd', horizontal=False):
    """Столбчатая диаграмма"""
    orientation = 'h' if horizontal else 'v'
    data = {
        'type': 'bar',
        'orientation': orientation,
        'marker': {'color': color, 'opacity': 0.75},
    }
    if horizontal:
        data['x'] = values
        data['y'] = labels
    else:
        data['x'] = labels
        data['y'] = values
    
    return {
        'data': [data],
        'layout': {
            'title': title,
            'margin': {'l': 60, 't': 50, 'r': 20, 'b': 40},
            'height': 300,
            'paper_bgcolor': '#fff',
            'plot_bgcolor': '#f8f9fa',
        },
        'config': {'responsive': True, 'displayModeBar': False},
    }


def score_distribution_config(scores_dict, title='Распределение оценок'):
    """Столбчатая диаграмма распределения оценок"""
    labels = ['2', '3', '4', '5']
    values = [scores_dict.get(i, 0) for i in [2, 3, 4, 5]]
    colors = [
        'rgba(220, 53, 69, 0.65)',
        'rgba(255, 193, 7, 0.65)',
        'rgba(40, 167, 69, 0.65)',
        'rgba(13, 110, 253, 0.65)',
    ]
    
    return {
        'data': [{
            'type': 'bar',
            'x': labels,
            'y': values,
            'marker': {'color': colors},
            'text': values,
            'textposition': 'auto',
        }],
        'layout': {
            'title': title,
            'xaxis': {'title': 'Оценка'},
            'yaxis': {'title': 'Количество'},
            'margin': {'l': 50, 't': 50, 'r': 20, 'b': 50},
            'height': 300,
            'paper_bgcolor': '#fff',
            'plot_bgcolor': '#f8f9fa',
        },
        'config': {'responsive': True, 'displayModeBar': False},
    }


def multi_bar_config(categories, series, title=''):
    """Группированная столбчатая диаграмма"""
    colors = [
        'rgba(13, 110, 253, 0.65)',
        'rgba(40, 167, 69, 0.65)',
        'rgba(255, 193, 7, 0.65)',
        'rgba(220, 53, 69, 0.65)',
        'rgba(111, 66, 193, 0.65)',
        'rgba(32, 201, 151, 0.65)',
    ]
    data = []
    for i, (name, values) in enumerate(series.items()):
        data.append({
            'type': 'bar',
            'name': name,
            'x': categories,
            'y': values,
            'marker': {'color': colors[i % len(colors)]},
        })
    
    return {
        'data': data,
        'layout': {
            'title': title,
            'barmode': 'group',
            'margin': {'l': 50, 't': 50, 'r': 20, 'b': 80},
            'height': 350,
            'legend': {'orientation': 'h', 'y': -0.2},
            'paper_bgcolor': '#fff',
            'plot_bgcolor': '#f8f9fa',
        },
        'config': {'responsive': True, 'displayModeBar': False},
    }


def line_chart_config(x_labels, y_values, title='', color='rgba(13, 110, 253, 0.75)'):
    """Линейный график"""
    return {
        'data': [{
            'type': 'scatter',
            'mode': 'lines+markers',
            'x': x_labels,
            'y': y_values,
            'line': {'color': color, 'width': 2},
            'marker': {'size': 8},
            'fill': 'tozeroy',
            'fillcolor': 'rgba(13, 110, 253, 0.1)',
        }],
        'layout': {
            'title': title,
            'margin': {'l': 50, 't': 50, 'r': 20, 'b': 50},
            'height': 300,
            'paper_bgcolor': '#fff',
            'plot_bgcolor': '#f8f9fa',
        },
        'config': {'responsive': True, 'displayModeBar': False},
    }


def to_json(config):
    """Безопасная сериализация в JSON для шаблона"""
    return json.dumps(config, ensure_ascii=False)
