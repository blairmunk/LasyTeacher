"""Генератор LaTeX для рабочего листа 'Работа над ошибками'"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from document_generator.utils.formula_utils import formula_processor
from latex_generator.utils.latex_specific import latex_formula_processor
from latex_generator.utils.latex_image_utils import prepare_images_for_latex, render_task_with_images
from latex_generator.utils.compilation import latex_compiler, LaTeXCompilationError
from .base import BaseLatexGenerator
from .work_generator import get_latex_geometry

logger = logging.getLogger(__name__)


class RemedialSheetLatexGenerator(BaseLatexGenerator):
    """Генератор рабочего листа «Работа над ошибками»

    Структура документа:
    1. Заголовок: ФИО, оценка, исходная КР
    2. Секция «Разбор ошибок»: оригинальные задания с решениями + баллы
    3. Секция «Тренировка»: новые задания из тех же групп
    """

    def get_template_name(self) -> str:
        return 'latex/remedial/sheet.tex'

    def get_output_filename(self, work) -> str:
        variant = getattr(self, '_variant', None)
        if variant and variant.assigned_student:
            name = variant.assigned_student.get_short_name()
            return f"remedial_{name}.tex"
        return f"remedial_{work.name}.tex"

    def prepare_context(self, work) -> Dict[str, Any]:
        """Подготавливает контекст для remedial sheet."""
        from works.models import Variant, VariantTask
        from events.models import EventParticipation, Mark
        from task_groups.models import TaskGroup

        variant = getattr(self, '_variant', None)
        content_config = getattr(self, '_content_config', {})
        page_format = content_config.get('page_format', 'A4').upper()

        if not variant:
            raise ValueError("Не указан вариант (_variant)")

        student = variant.assigned_student
        source_work = variant.source_work

        document_errors = []
        document_warnings = []

        # ═══ Секция 1: Оригинальные задания с решениями ═══
        original_tasks = []
        mark = None
        task_scores = {}

        if source_work and student:
            # Находим оригинальное участие
            original_ep = EventParticipation.objects.filter(
                event__work=source_work,
                student=student,
            ).select_related('variant').first()

            if original_ep:
                mark_obj = Mark.objects.filter(participation=original_ep).first()
                if mark_obj:
                    mark = mark_obj
                    task_scores = mark_obj.task_scores or {}

                if original_ep.variant:
                    orig_vts = VariantTask.objects.filter(
                        variant=original_ep.variant
                    ).select_related('task', 'task__topic').order_by('order')

                    for vt in orig_vts:
                        task = vt.task
                        tid = str(task.pk)
                        score_data = task_scores.get(tid, {})

                        pts = score_data.get('points', None)
                        max_pts = score_data.get('max_points', None)

                        # Определяем статус
                        if isinstance(pts, (int, float)) and isinstance(max_pts, (int, float)) and max_pts > 0:
                            pct = pts / max_pts * 100
                            if pct >= 70:
                                status = 'ok'
                            elif pct > 0:
                                status = 'partial'
                            else:
                                status = 'fail'
                        else:
                            pct = 0
                            status = 'unknown'

                        # Группа аналогов
                        tg = TaskGroup.objects.filter(task=task).first()
                        group_name = tg.group.name if tg else ''

                        # Обрабатываем текст задания
                        text_result = self._safe_process(task.text, f'orig task {task.id}')
                        answer_result = self._safe_process(task.answer or '', f'orig answer {task.id}')
                        short_sol_result = self._safe_process(task.short_solution or '', f'orig short_sol {task.id}')
                        full_sol_result = self._safe_process(task.full_solution or '', f'orig full_sol {task.id}')

                        document_errors.extend(text_result['errors'])
                        document_errors.extend(answer_result['errors'])
                        document_warnings.extend(text_result['warnings'])

                        # Изображения
                        try:
                            task_images = prepare_images_for_latex(task, self.output_dir)
                        except Exception:
                            task_images = []

                        if task_images:
                            try:
                                latex_content = render_task_with_images(
                                    {'text': text_result['content']}, task_images
                                )
                            except Exception:
                                latex_content = text_result['content']
                        else:
                            latex_content = text_result['content']

                        original_tasks.append({
                            'number': vt.order,
                            'text': text_result['content'],
                            'latex_content': latex_content,
                            'answer': answer_result['content'],
                            'short_solution': short_sol_result['content'],
                            'full_solution': full_sol_result['content'],
                            'points': pts,
                            'max_points': max_pts,
                            'pct': round(pct, 1),
                            'status': status,
                            'group_name': group_name,
                            'has_images': len(task_images) > 0,
                        })

        # ═══ Секция 2: Новые задания (тренировка) ═══
        new_tasks = []
        new_vts = VariantTask.objects.filter(
            variant=variant
        ).select_related('task', 'task__topic').order_by('order')

        for vt in new_vts:
            task = vt.task
            text_result = self._safe_process(task.text, f'new task {task.id}')
            answer_result = self._safe_process(task.answer or '', f'new answer {task.id}')

            document_errors.extend(text_result['errors'])
            document_warnings.extend(text_result['warnings'])

            try:
                task_images = prepare_images_for_latex(task, self.output_dir)
            except Exception:
                task_images = []

            if task_images:
                try:
                    latex_content = render_task_with_images(
                        {'text': text_result['content']}, task_images
                    )
                except Exception:
                    latex_content = text_result['content']
            else:
                latex_content = text_result['content']

            new_tasks.append({
                'number': vt.order,
                'text': text_result['content'],
                'latex_content': latex_content,
                'answer': answer_result['content'],
                'weight': float(vt.weight) if vt.weight else 1,
                'max_points': float(vt.max_points) if vt.max_points else 1,
                'has_images': len(task_images) > 0,
            })

        # Заголовок
        work_name_result = self._safe_process(work.name, 'work_name')
        source_name_result = self._safe_process(
            source_work.name if source_work else '', 'source_work_name'
        )

        student_name = ''
        if student:
            student_name = student.get_full_name()

        return {
            'work': work,
            'work_name': work_name_result['content'],
            'source_work_name': source_name_result['content'],
            'student_name': student_name,
            'mark_score': mark.score if mark else None,
            'mark_points': mark.points if mark else None,
            'mark_max_points': mark.max_points if mark else None,
            'variant': variant,

            # Секции
            'original_tasks': original_tasks,
            'new_tasks': new_tasks,

            # Мета
            'page_format': page_format,
            'page_geometry': get_latex_geometry(page_format),
            'has_formula_errors': len(document_errors) > 0,
            'has_formula_warnings': len(document_warnings) > 0,
            'formula_errors': document_errors,
            'formula_warnings': document_warnings,

            # Флаги контента
            'show_solutions': content_config.get('include_short_solutions', True),
            'show_full_solutions': content_config.get('include_full_solutions', False),
            'show_answers_for_new': content_config.get('include_answers', False),
        }

    def _safe_process(self, text, label=''):
        """Обработка формул с fallback."""
        if not text:
            return {'content': '', 'errors': [], 'warnings': []}
        try:
            return latex_formula_processor.render_for_latex_safe(text)
        except Exception as e:
            logger.error(f'Ошибка обработки {label}: {e}')
            return {'content': text, 'errors': [f'{label}: {e}'], 'warnings': []}

    def generate_for_variant(self, variant, output_format='pdf',
                              content_config=None):
        """Точка входа: генерация для конкретного варианта.
        
        Вся логика render + compile в базовом классе.
        """
        self._variant = variant
        self._content_config = content_config or {
            'include_short_solutions': True,
            'include_full_solutions': False,
            'include_answers': False,
        }

        work = variant.work
        # Базовый generate(): prepare_context → render_to_string → .tex → compile_latex_to_pdf
        return super().generate(work, output_format)
