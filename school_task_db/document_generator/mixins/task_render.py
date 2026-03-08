"""
Общий миксин для подготовки контекста заданий.
Используется в LaTeX и HTML генераторах — устраняет дублирование.
"""
import logging

logger = logging.getLogger(__name__)


class TaskRenderMixin:
    """Миксин для обработки заданий: формулы, решения, изображения, ошибки."""

    def prepare_task_context(self, task, order, content_config, formula_processor,
                             process_func_name='render_for_latex_safe'):
        """
        Обрабатывает одно задание и возвращает dict с контекстом.

        Args:
            task: Task model instance
            order: порядковый номер задания
            content_config: dict с флагами (include_answers, include_short_solutions, ...)
            formula_processor: объект процессора формул
            process_func_name: имя метода процессора ('render_for_latex_safe' или 'render_for_html_safe')

        Returns:
            dict с полями: number, text, answer, short_solution, full_solution,
                          hint, instruction, images, errors, warnings, ...
        """
        process = getattr(formula_processor, process_func_name)

        include_answers = content_config.get('include_answers', False)
        include_short = content_config.get('include_short_solutions', False)
        include_full = content_config.get('include_full_solutions', False)
        include_hints = content_config.get('include_hints', False)
        include_instructions = content_config.get('include_instructions', False)

        errors = []
        warnings = []

        # --- Текст задания ---
        text_result = self._safe_process(process, task.text, f'text задания {task.id}')
        errors.extend(text_result['errors'])
        warnings.extend(text_result['warnings'])

        # --- Ответ ---
        answer_content = ''
        if include_answers and task.answer:
            answer_result = self._safe_process(process, task.answer, f'answer задания {task.id}')
            answer_content = answer_result['content']
            errors.extend(answer_result['errors'])
            warnings.extend(answer_result['warnings'])

        # --- Краткое решение ---
        short_solution = ''
        if include_short and task.short_solution:
            result = self._safe_process(process, task.short_solution,
                                        f'short_solution задания {task.id}')
            short_solution = result['content']
            errors.extend(result['errors'])
            warnings.extend(result['warnings'])

        # --- Полное решение ---
        full_solution = ''
        if include_full and task.full_solution:
            result = self._safe_process(process, task.full_solution,
                                        f'full_solution задания {task.id}')
            full_solution = result['content']
            errors.extend(result['errors'])
            warnings.extend(result['warnings'])

        # --- Подсказка ---
        hint = ''
        if include_hints and task.hint:
            result = self._safe_process(process, task.hint,
                                        f'hint задания {task.id}')
            hint = result['content']
            errors.extend(result['errors'])
            warnings.extend(result['warnings'])

        # --- Инструкция ---
        instruction = ''
        if include_instructions and task.instruction:
            result = self._safe_process(process, task.instruction,
                                        f'instruction задания {task.id}')
            instruction = result['content']
            errors.extend(result['errors'])
            warnings.extend(result['warnings'])

        # --- Изображения ---
        images_data = self._prepare_images(task)

        # --- Weight из VariantTask ---
        weight = getattr(task, '_vt_weight', None)
        max_points = getattr(task, '_vt_max_points', None)

        return {
            'number': order,
            'task_id': str(task.id),
            'text': text_result['content'],
            'answer': answer_content,
            'short_solution': short_solution,
            'full_solution': full_solution,
            'hint': hint,
            'instruction': instruction,
            'weight': weight,
            'max_points': max_points,
            'difficulty': task.difficulty,
            'task_type': task.task_type,
            'images': images_data,
            'has_images': len(images_data) > 0,
            'has_errors': len(errors) > 0,
            'has_warnings': len(warnings) > 0,
            'errors': errors,
            'warnings': warnings,
        }

    def prepare_variant_tasks(self, variant, content_config, formula_processor,
                               process_func_name='render_for_latex_safe'):
        """
        Обрабатывает все задания варианта.

        Returns:
            (prepared_tasks, all_errors, all_warnings)
        """
        from works.models import VariantTask

        vt_map = {}
        for vt in VariantTask.objects.filter(variant=variant).order_by('order'):
            vt_map[vt.task_id] = vt

        tasks = variant.tasks.all().order_by('id')
        prepared = []
        all_errors = []
        all_warnings = []

        for i, task in enumerate(tasks, 1):
            # Прокидываем weight/max_points через атрибуты
            vt = vt_map.get(task.id)
            if vt:
                task._vt_weight = float(vt.weight) if vt.weight else None
                task._vt_max_points = float(vt.max_points) if vt.max_points else None
                order = vt.order
            else:
                task._vt_weight = None
                task._vt_max_points = None
                order = i

            ctx = self.prepare_task_context(
                task, order, content_config,
                formula_processor, process_func_name,
            )
            prepared.append(ctx)
            all_errors.extend(ctx['errors'])
            all_warnings.extend(ctx['warnings'])

        # Сортируем по order
        prepared.sort(key=lambda x: x['number'])

        return prepared, all_errors, all_warnings

    def _safe_process(self, process_func, text, label=''):
        """Безопасная обработка формул с fallback."""
        try:
            return process_func(text)
        except Exception as e:
            logger.error(f'Ошибка обработки {label}: {e}')
            return {
                'content': text,
                'errors': [f'{label}: {str(e)}'],
                'warnings': [],
            }

    def _prepare_images(self, task):
        """Подготовка изображений задания."""
        images = []
        try:
            for img in task.images.all():
                images.append({
                    'id': str(img.id),
                    'path': img.image.path if img.image else '',
                    'url': img.image.url if img.image else '',
                    'position': getattr(img, 'position', 'after_text'),
                    'caption': getattr(img, 'caption', ''),
                    'width': getattr(img, 'width', None),
                })
        except Exception as e:
            logger.warning(f'Ошибка загрузки изображений задания {task.id}: {e}')
        return images
