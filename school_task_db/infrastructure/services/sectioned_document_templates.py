"""Template maps for built-in sectioned document renderers."""

from core_logic.value_objects.document_recipes import (
    ANSWER_KEY_SECTION,
    ANSWERS_SECTION,
    FULL_SOLUTIONS_SECTION,
    HEADER_SECTION,
    LEGACY_TASK_VARIANTS_SECTION,
    ORIGINAL_MISTAKES_SECTION,
    SHORT_SOLUTIONS_SECTION,
    TASK_LIST_SECTION,
    TRAINING_TASKS_SECTION,
)


WORK_HTML_SECTION_TEMPLATES = {
    HEADER_SECTION: 'documents/html/sections/header.html',
    TASK_LIST_SECTION: 'documents/html/sections/task_list.html',
    LEGACY_TASK_VARIANTS_SECTION: 'documents/html/sections/task_list.html',
    ANSWER_KEY_SECTION: 'documents/html/sections/answers.html',
    ANSWERS_SECTION: 'documents/html/sections/answers.html',
    SHORT_SOLUTIONS_SECTION: 'documents/html/sections/short_solutions.html',
    FULL_SOLUTIONS_SECTION: 'documents/html/sections/full_solutions.html',
}
WORK_HTML_WRAPPER_TEMPLATE = 'documents/html/base/document.html'

WORK_LATEX_SECTION_TEMPLATES = {
    HEADER_SECTION: 'documents/latex/sections/header.tex',
    TASK_LIST_SECTION: 'documents/latex/sections/task_list.tex',
    LEGACY_TASK_VARIANTS_SECTION: 'documents/latex/sections/task_list.tex',
    ANSWER_KEY_SECTION: 'documents/latex/sections/answers.tex',
    ANSWERS_SECTION: 'documents/latex/sections/answers.tex',
    SHORT_SOLUTIONS_SECTION: 'documents/latex/sections/short_solutions.tex',
    FULL_SOLUTIONS_SECTION: 'documents/latex/sections/full_solutions.tex',
}
WORK_LATEX_WRAPPER_TEMPLATE = 'documents/latex/base/document.tex'

REMEDIAL_HTML_SECTION_TEMPLATES = {
    HEADER_SECTION: 'documents/html/sections/remedial_header.html',
    ORIGINAL_MISTAKES_SECTION: (
        'documents/html/sections/remedial_original_mistakes.html'
    ),
    TRAINING_TASKS_SECTION: (
        'documents/html/sections/remedial_training_tasks.html'
    ),
    ANSWERS_SECTION: 'documents/html/sections/remedial_answers.html',
    SHORT_SOLUTIONS_SECTION: (
        'documents/html/sections/remedial_short_solutions.html'
    ),
    FULL_SOLUTIONS_SECTION: (
        'documents/html/sections/remedial_full_solutions.html'
    ),
}
REMEDIAL_HTML_WRAPPER_TEMPLATE = 'documents/html/base/document.html'

REMEDIAL_LATEX_SECTION_TEMPLATES = {
    HEADER_SECTION: 'documents/latex/sections/remedial_header.tex',
    ORIGINAL_MISTAKES_SECTION: (
        'documents/latex/sections/remedial_original_mistakes.tex'
    ),
    TRAINING_TASKS_SECTION: (
        'documents/latex/sections/remedial_training_tasks.tex'
    ),
    ANSWERS_SECTION: 'documents/latex/sections/remedial_answers.tex',
    SHORT_SOLUTIONS_SECTION: (
        'documents/latex/sections/remedial_short_solutions.tex'
    ),
    FULL_SOLUTIONS_SECTION: (
        'documents/latex/sections/remedial_full_solutions.tex'
    ),
}
REMEDIAL_LATEX_WRAPPER_TEMPLATE = 'documents/latex/base/document.tex'
