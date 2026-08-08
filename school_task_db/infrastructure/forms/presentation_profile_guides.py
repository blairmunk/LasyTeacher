"""User-facing style hooks for rendered document types."""

from core_logic.value_objects.document_recipes import (
    EVENT_PERFORMANCE_REPORT_DOCUMENT_TYPE,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    STUDENT_DIGEST_DOCUMENT_TYPE,
    WORK_DOCUMENT_TYPE,
)


COMMON_HTML_HOOKS = (
    ('body', 'Шрифт, цвет и базовые интервалы всего документа.'),
    ('.document-section', 'Внешние интервалы любой секции.'),
)

WORK_HTML_HOOKS = COMMON_HTML_HOOKS + (
    ('.document-header', 'Заголовок варианта.'),
    ('.document-header-meta', 'Время и максимальный балл.'),
    ('.document-student-fields', 'Строки фамилии, имени и даты.'),
    ('.document-task-variants', 'Секция с содержанием вариантов.'),
    ('.document-variant', 'Один вариант внутри документа.'),
    ('.document-theory-block', 'Блок теории.'),
    ('.task-item', 'Одно задание.'),
    ('.task-heading', 'Строка номера задания и количества баллов.'),
    ('.task-blank-cells', 'Клетки после конкретного задания.'),
)

REMEDIAL_HTML_HOOKS = COMMON_HTML_HOOKS + (
    ('.remedial-header', 'Персональный заголовок листа РнО.'),
    ('.remedial-original-mistakes', 'Ошибки исходной работы.'),
    ('.remedial-training-tasks', 'Тренировочные задания.'),
    ('.remedial-task', 'Одно исходное задание.'),
    ('.task-blank-cells', 'Клетки после тренировочного задания.'),
    ('.remedial-answers', 'Краткие ответы.'),
)

REPORT_COMMON_HTML_HOOKS = COMMON_HTML_HOOKS + (
    ('.report-header', 'Шапка печатного отчёта.'),
    ('.report-kicker', 'Надпись над главным заголовком.'),
    ('.report-section-title', 'Заголовки разделов.'),
    ('.report-metrics', 'Сетка ключевых показателей.'),
    ('.report-metric', 'Один показатель в сводке.'),
)

EVENT_REPORT_HTML_HOOKS = REPORT_COMMON_HTML_HOOKS + (
    (
        '.document-section-event_report_specification',
        'Краткая спецификация работы.',
    ),
    (
        '.document-section-event_report_summary',
        'Общие результаты.',
    ),
    (
        '.document-section-event_report_task_analysis',
        'Анализ выполнения заданий.',
    ),
    (
        '.document-section-event_report_conclusions',
        'Выводы и дальнейшая работа.',
    ),
    (
        '.document-section-event_report_teacher_notes',
        'Необязательное приложение с комментариями проверки.',
    ),
)

STUDENT_DIGEST_HTML_HOOKS = REPORT_COMMON_HTML_HOOKS + (
    ('.digest-header', 'Персональная шапка ученика.'),
    ('.digest-header-row', 'Строка имени и периода.'),
    ('.digest-grade', 'Оценка в таблице.'),
    ('.digest-note', 'Акцентный блок рекомендаций.'),
    ('.digest-teacher-comment', 'Необязательный комментарий учителя.'),
    ('.document-section-student_digest_summary', 'Сводка за период.'),
    ('.document-section-student_digest_retakes', 'Работы к пересдаче.'),
    ('.document-section-student_digest_details', 'Таблица оценок.'),
    ('.document-section-student_digest_focus', 'Рекомендации.'),
    (
        '.document-section-student_digest_teacher_comments',
        'Общие комментарии учителя к работам.',
    ),
)

WORK_LATEX_HOOKS = (
    ('schoolheader', 'Заголовок варианта.'),
    ('schooltasklist', 'Список заданий.'),
    ('schooltheory', 'Блок теории.'),
    ('schoolanswers', 'Блок ответов.'),
    ('schoolblankcells', 'Поле в клетку.'),
    ('schoolscoretable', 'Таблица баллов.'),
    ('schoolvariantheading', 'Команда заголовка варианта.'),
    ('schooltaskheading', 'Команда заголовка задания и количества баллов.'),
    ('schoolsectionheading', 'Команда заголовка секции.'),
    ('schoolsubheading', 'Команда подзаголовка внутри секции.'),
)

REMEDIAL_LATEX_HOOKS = (
    ('schoolheader', 'Персональный заголовок листа РнО.'),
    ('schooloriginalmistakes', 'Ошибки исходной работы.'),
    ('schooltrainingtasks', 'Тренировочные задания.'),
    ('schoolanswers', 'Блок ответов.'),
    ('schoolblankcells', 'Поле в клетку.'),
    ('schooltaskheading', 'Команда заголовка задания.'),
    ('schoolsectionheading', 'Команда заголовка секции.'),
    ('schoolsubheading', 'Команда подзаголовка внутри секции.'),
)


def get_presentation_profile_guides(document_types):
    """Build JSON-safe guides from actual HTML and LaTeX template hooks."""
    return {
        item.document_type: {
            'supports_latex': 'latex' in item.renderer_types,
            'html_hooks': _hook_context(_html_hooks(item.document_type)),
            'latex_hooks': _hook_context(_latex_hooks(item.document_type)),
            'css_example': _css_example(item.document_type),
            'latex_example': _latex_example(item.document_type),
            'presets': _presentation_presets(item.document_type),
        }
        for item in document_types
    }


def _html_hooks(document_type):
    return {
        WORK_DOCUMENT_TYPE: WORK_HTML_HOOKS,
        REMEDIAL_SHEET_DOCUMENT_TYPE: REMEDIAL_HTML_HOOKS,
        EVENT_PERFORMANCE_REPORT_DOCUMENT_TYPE: EVENT_REPORT_HTML_HOOKS,
        STUDENT_DIGEST_DOCUMENT_TYPE: STUDENT_DIGEST_HTML_HOOKS,
    }.get(document_type, COMMON_HTML_HOOKS)


def _latex_hooks(document_type):
    return {
        WORK_DOCUMENT_TYPE: WORK_LATEX_HOOKS,
        REMEDIAL_SHEET_DOCUMENT_TYPE: REMEDIAL_LATEX_HOOKS,
    }.get(document_type, ())


def _hook_context(hooks):
    return [
        {'selector': selector, 'description': description}
        for selector, description in hooks
    ]


def _css_example(document_type):
    if document_type == EVENT_PERFORMANCE_REPORT_DOCUMENT_TYPE:
        return (
            'body { font-family: Arial, sans-serif; font-size: 10.5pt; }\n\n'
            '.report-section-title { border-bottom-color: #1f4b6e; }\n\n'
            '.document-section-event_report_specification table {\n'
            '    font-size: 9.5pt;\n'
            '}\n\n'
            '.report-metric { border-left-color: #1f4b6e; }'
        )
    if document_type == STUDENT_DIGEST_DOCUMENT_TYPE:
        return (
            'body { font-family: Arial, sans-serif; font-size: 10.5pt; }\n\n'
            '.digest-header-row { border-bottom-color: #1f4b6e; }\n\n'
            '.digest-grade { color: #1f4b6e; }\n\n'
            '.digest-note { border-left-color: #b54708; }'
        )
    if document_type == REMEDIAL_SHEET_DOCUMENT_TYPE:
        return (
            'body { font-family: Georgia, serif; font-size: 14px; }\n\n'
            '.remedial-original-mistakes { margin-bottom: 1.5rem; }\n\n'
            '.remedial-training-task { break-inside: avoid; }'
        )
    return (
        'body { font-family: Georgia, serif; font-size: 14px; }\n\n'
        '.document-section { margin-bottom: 1.5rem; }\n\n'
        '.document-theory-block {\n'
        '    border-left: 3px solid #555;\n'
        '    padding-left: 1rem;\n'
        '}'
    )


def _latex_example(document_type):
    if document_type == REMEDIAL_SHEET_DOCUMENT_TYPE:
        return (
            '\\usepackage{xcolor}\n\n'
            '\\renewenvironment{schooloriginalmistakes}\n'
            '  {\\begin{quote}\\small}\n'
            '  {\\end{quote}}'
        )
    if document_type == WORK_DOCUMENT_TYPE:
        return (
            '\\usepackage{xcolor}\n\n'
            '\\renewenvironment{schooltheory}\n'
            '  {\\begin{quote}\\small\\color{gray}}\n'
            '  {\\end{quote}}'
        )
    return ''


def _presentation_presets(document_type):
    if document_type != WORK_DOCUMENT_TYPE:
        return []
    return [
        {
            'preset_id': 'compact_worksheet',
            'title': 'Компактный рабочий лист',
            'description': (
                'Две колонки на широкой странице, одна колонка на A5. '
                'Порядок и состав блоков не меняются.'
            ),
            'custom_css': _compact_worksheet_css(),
            'custom_latex_preamble': _compact_worksheet_latex(),
        },
    ]


def _compact_worksheet_css():
    return (
        '.document-variant .task-list {\n'
        '    columns: 2 72mm;\n'
        '    column-gap: 8mm;\n'
        '    column-rule: 1px solid var(--document-line);\n'
        '}\n\n'
        '.document-theory-block,\n'
        '.document-text-block,\n'
        '.task-item,\n'
        '.task-blank-cells {\n'
        '    break-inside: avoid;\n'
        '}\n\n'
        '.task-item {\n'
        '    break-after: avoid;\n'
        '}'
    )


def _compact_worksheet_latex():
    return (
        '\\usepackage{multicol}\n'
        '\\setlength{\\columnsep}{7mm}\n'
        '\\setlength{\\columnseprule}{0.2pt}\n'
        '\\newif\\ifschoolwidepage\n'
        '\\ifdim\\paperwidth>170mm\n'
        '  \\schoolwidepagetrue\n'
        '\\else\n'
        '  \\schoolwidepagefalse\n'
        '\\fi\n'
        '\\renewenvironment{schooltasklist}\n'
        '  {\\ifschoolwidepage\\begin{multicols}{2}\\raggedcolumns\\fi}\n'
        '  {\\ifschoolwidepage\\end{multicols}\\fi}'
    )
