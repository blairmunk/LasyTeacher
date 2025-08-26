"""Генератор LaTeX для работ с полной обработкой ошибок"""

from typing import Dict, Any
from pathlib import Path

from document_generator.utils.formula_utils import formula_processor
from document_generator.utils.file_utils import sanitize_filename
from latex_generator.utils import sanitize_latex
from latex_generator.utils.latex_image_utils import prepare_images_for_latex, render_task_with_images
from latex_generator.utils.latex_specific import latex_formula_processor
from latex_generator.utils.compilation import latex_compiler, LaTeXCompilationError

from .base import BaseLatexGenerator
import logging

logger = logging.getLogger(__name__)

class WorkLatexGenerator(BaseLatexGenerator):
    """Генератор LaTeX документов для работ с математическими формулами"""
    
    def get_template_name(self) -> str:
        return 'latex/work/all_variants.tex'
    
    def get_output_filename(self, work) -> str:
        return f"{work.name}_all_variants.tex"
    
    def prepare_context(self, work) -> Dict[str, Any]:
        """Подготавливает контекст для работы с обработкой формул"""
        
        variants = work.variant_set.all().order_by('number')
        
        # Подготавливаем данные для каждого варианта
        all_variants_data = []
        document_errors = []
        document_warnings = []
        
        for variant in variants:
            variant_data = self._prepare_variant_context(variant)
            all_variants_data.append(variant_data)
            
            # Собираем ошибки и предупреждения
            document_errors.extend(variant_data.get('errors', []))
            document_warnings.extend(variant_data.get('warnings', []))
        
        # Обрабатываем название работы
        work_name_processed = latex_formula_processor.render_for_latex_safe(work.name)
        document_errors.extend(work_name_processed['errors'])
        document_warnings.extend(work_name_processed['warnings'])
        
        return {
            'work': work,
            'work_name': work_name_processed['content'],
            'variants': all_variants_data,
            'total_variants': len(all_variants_data),
            'with_answers': getattr(self, '_with_answers', False),
            
            # Информация об ошибках формул
            'has_formula_errors': len(document_errors) > 0,
            'has_formula_warnings': len(document_warnings) > 0,
            'formula_errors': document_errors,
            'formula_warnings': document_warnings,
        }
    
    def _prepare_variant_context(self, variant):
        """ОБНОВЛЕНО: Подготовка контекста с поддержкой 4 типов контента"""
        print(f"🔍 DEBUG: Обрабатываем вариант {variant.number}")
        
        # Получаем конфигурацию контента
        content_config = getattr(self, '_content_config', {})
        include_answers = content_config.get('include_answers', False)
        include_short_solutions = content_config.get('include_short_solutions', False) 
        include_full_solutions = content_config.get('include_full_solutions', False)
        
        print(f"🔍 Конфигурация контента: answers={include_answers}, short={include_short_solutions}, full={include_full_solutions}")
        
        tasks = variant.tasks.all().order_by('id')
        
        prepared_tasks = []
        variant_errors = []
        variant_warnings = []
        
        for i, task in enumerate(tasks, 1):
            print(f"🔍 DEBUG: Обрабатываем задание {task.id} (номер {i})")
            
            # Обрабатываем текст задания
            try:
                text_processed = latex_formula_processor.render_for_latex_safe(task.text)
                answer_processed = latex_formula_processor.render_for_latex_safe(task.answer or '')
            except Exception as e:
                print(f"❌ ОШИБКА в обработке формул задания {task.id}: {e}")
                # Fallback - используем исходный текст
                text_processed = {'content': task.text, 'errors': [str(e)], 'warnings': []}
                answer_processed = {'content': task.answer or '', 'errors': [], 'warnings': []}
            
            # Собираем ошибки и предупреждения
            task_errors = []
            task_warnings = []
            
            task_errors.extend(text_processed['errors'])
            task_errors.extend(answer_processed['errors'])
            task_warnings.extend(text_processed['warnings'])
            task_warnings.extend(answer_processed['warnings'])
            
            # Обрабатываем дополнительные поля если есть
            additional_fields = {}
        # Ответы - включаем если любой тип ответов запрошен
            if include_answers:
                additional_fields['answer'] = answer_processed['content']
            else:
                additional_fields['answer'] = ''
            
            # Краткие решения
            if include_short_solutions and task.short_solution:
                try:
                    short_processed = latex_formula_processor.render_for_latex_safe(task.short_solution)
                    additional_fields['short_solution'] = short_processed['content']
                    task_errors.extend(short_processed['errors'])
                    task_warnings.extend(short_processed['warnings'])
                except Exception as e:
                    print(f"❌ ОШИБКА в обработке краткого решения: {e}")
                    additional_fields['short_solution'] = task.short_solution
            else:
                additional_fields['short_solution'] = ''
            
            # Полные решения
            if include_full_solutions and task.full_solution:
                try:
                    full_processed = latex_formula_processor.render_for_latex_safe(task.full_solution)
                    additional_fields['full_solution'] = full_processed['content']
                    task_errors.extend(full_processed['errors'])
                    task_warnings.extend(full_processed['warnings'])
                except Exception as e:
                    print(f"❌ ОШИБКА в обработке полного решения: {e}")
                    additional_fields['full_solution'] = task.full_solution
            else:
                additional_fields['full_solution'] = ''
            
            # Подсказки и инструкции (всегда обрабатываем если есть)
            for field_name in ['hint', 'instruction']:
                field_value = getattr(task, field_name, None)
                if field_value:
                    try:
                        processed = latex_formula_processor.render_for_latex_safe(field_value)
                        additional_fields[field_name] = processed['content']
                        task_errors.extend(processed['errors'])
                        task_warnings.extend(processed['warnings'])
                    except Exception as e:
                        print(f"❌ ОШИБКА в обработке поля {field_name}: {e}")
                        additional_fields[field_name] = field_value  # Fallback
                else:
                    additional_fields[field_name] = ''
            
            # ОТЛАДКА: Проверяем есть ли изображения у задания
            try:
                images_count = task.images.count()
                print(f"🔍 Задание {task.id}: найдено {images_count} изображений")
                
                if images_count > 0:
                    for img in task.images.all():
                        print(f"🔍   Изображение {img.id}: файл={img.image.name}, позиция={img.position}")
                
                # Подготавливаем изображения
                task_images = prepare_images_for_latex(task, self.output_dir)
                print(f"🔍 После prepare_images_for_latex: {len(task_images)} изображений")
                
                # ОТЛАДКА: Проверяем структуру данных изображений
                for idx, img in enumerate(task_images):
                    print(f"🔍 Изображение {idx}: ключи = {list(img.keys())}")
                    if 'minipage_config' in img:
                        print(f"🔍   minipage_config есть, layout = {img['minipage_config']['layout']}")
                    else:
                        print("❌   minipage_config ОТСУТСТВУЕТ!")
                        
            except Exception as e:
                print(f"❌ КРИТИЧЕСКАЯ ОШИБКА при обработке изображений задания {task.id}: {e}")
                print(f"❌ Тип ошибки: {type(e).__name__}")
                import traceback
                print(f"❌ Traceback: {traceback.format_exc()}")
                task_images = []  # Fallback - без изображений
            
            # Базовые данные задания с обработанными формулами
            task_data = {
                'number': i,
                'task': task,
                'text': text_processed['content'],
                'answer': answer_processed['content'],
                'images': task_images,
                
                # Информация об ошибках формул
                'has_formula_errors': len(task_errors) > 0,
                'has_formula_warnings': len(task_warnings) > 0,
                'formula_errors': task_errors,
                'formula_warnings': task_warnings,
            }
            
            # Добавляем дополнительные поля
            task_data.update(additional_fields)
            
            # Генерируем итоговый LaTeX код с учетом изображений
            try:
                if task_images:
                    print(f"🔍 Вызываем render_task_with_images с {len(task_images)} изображениями")
                    latex_content = render_task_with_images(
                        {'text': task_data['text']}, 
                        task_images
                    )
                    print(f"🔍 render_task_with_images вернул: {len(latex_content)} символов")
                    print(f"🔍 Первые 100 символов: {latex_content[:100]}...")
                    task_data['latex_content'] = latex_content
                else:
                    print("🔍 Нет изображений, используем обычный текст")
                    task_data['latex_content'] = task_data['text']
            except Exception as e:
                print(f"❌ ОШИБКА в render_task_with_images: {e}")
                task_data['latex_content'] = task_data['text']  # Fallback
            
            prepared_tasks.append(task_data)
            variant_errors.extend(task_errors)
            variant_warnings.extend(task_warnings)
        
        return {
            'variant': variant,
            'tasks': prepared_tasks,
            'total_tasks': len(prepared_tasks),
            'errors': variant_errors,
            'warnings': variant_warnings,
        }
    
    def generate(self, work, output_format='pdf'):
        """Генерация с полной обработкой ошибок"""
        try:
            # Вызываем базовую генерацию LaTeX файла
            files = super().generate(work, output_format)
            
            # Проверяем наличие ошибок формул в контексте
            context = self.prepare_context(work)
            
            if context.get('has_formula_errors'):
                logger.warning(f"Работа {work.name} содержит ошибки в формулах: {context['formula_errors']}")
            
            if context.get('has_formula_warnings'):
                logger.info(f"Работа {work.name} содержит предупреждения в формулах: {context['formula_warnings']}")
            
            # Если запросили PDF, пытаемся скомпилировать
            if output_format == 'pdf' and files:
                latex_file_path = Path(files[0])
                
                compilation_result = latex_compiler.compile_latex_safe(
                    latex_file_path, 
                    self.output_dir
                )
                
                if compilation_result['success']:
                    # Проверяем что PDF не дублируется
                    pdf_path = compilation_result['pdf_path']
                    if pdf_path not in files:
                        files.append(pdf_path)
                    
                    if compilation_result.get('has_warnings'):
                        logger.info(f"LaTeX компиляция с предупреждениями для {work.name}")
                
                else:
                    # Неудачная компиляция - логируем детали
                    error_msg = compilation_result.get('message', 'Неизвестная ошибка')
                    logger.error(f"LaTeX компиляция неудачна для работы {work.name}: {error_msg}")
                    
                    # Генерируем детальный отчет об ошибке
                    error_report = self._generate_error_report(work, compilation_result)
                    
                    # Сохраняем отчет об ошибках
                    error_file = self.output_dir / f"{work.name}_latex_errors.txt"
                    error_file.write_text(error_report, encoding='utf-8')
                    
                    # Проверяем что файл отчета не дублируется
                    error_file_str = str(error_file)
                    if error_file_str not in files:
                        files.append(error_file_str)
                    
                    # Возвращаем информацию об ошибке в контексте исключения
                    raise LaTeXCompilationError(
                        error_msg, 
                        error_details=compilation_result,
                        latex_log=compilation_result.get('latex_log')
                    )
            
            return files
            
        except LaTeXCompilationError:
            # Пробрасываем LaTeX ошибки как есть
            raise
        except Exception as e:
            logger.error(f"Ошибка генерации LaTeX для работы {work.name}: {e}")
            raise
    
    def _generate_error_report(self, work, compilation_result: Dict) -> str:
        """Генерирует детальный отчет об ошибках компиляции"""
        report_lines = [
            f"ОТЧЕТ ОБ ОШИБКАХ LATEX КОМПИЛЯЦИИ",
            f"======================================",
            f"",
            f"Работа: {work.name}",
            f"Дата: {getattr(work, 'created_at', 'Неизвестно')}",
            f"Тип ошибки: {compilation_result.get('error_type', 'unknown')}",
            f"",
            f"ОСНОВНАЯ ОШИБКА:",
            f"{compilation_result.get('message', 'Описание недоступно')}",
            f"",
        ]
        
        # Добавляем детали ошибок
        errors = compilation_result.get('errors', [])
        if errors:
            report_lines.extend([
                "ДЕТАЛИ ОШИБОК:",
                "==============="
            ])
            
            for i, error in enumerate(errors, 1):
                report_lines.extend([
                    f"{i}. {error.get('message', 'Неизвестная ошибка')}",
                    f"   Строка: {error.get('line_number', 'Неизвестно')}",
                ])
                
                # Добавляем контекст если есть
                context = error.get('context', [])
                if context:
                    report_lines.extend([
                        "   Контекст:"
                    ] + [f"   {line}" for line in context])
                
                report_lines.append("")
        
        # Добавляем предложения
        suggestions = compilation_result.get('suggestions', [])
        if suggestions:
            report_lines.extend([
                "ПРЕДЛОЖЕНИЯ ПО ИСПРАВЛЕНИЮ:",
                "============================"
            ])
            
            for i, suggestion in enumerate(suggestions, 1):
                report_lines.append(f"{i}. {suggestion}")
            
            report_lines.append("")
        
        return "\n".join(report_lines)
    
    def generate_with_answers(self, work, output_format='pdf'):
        """Генерирует работу с ответами"""
        self._with_answers = True
        try:
            return self.generate(work, output_format)
        finally:
            self._with_answers = False
