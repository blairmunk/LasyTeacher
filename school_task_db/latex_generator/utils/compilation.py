"""Безопасная компиляция LaTeX с обработкой ошибок"""

import subprocess
import tempfile
import shutil
import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from django.conf import settings

logger = logging.getLogger(__name__)

class LaTeXCompilationError(Exception):
    """Ошибка компиляции LaTeX"""
    def __init__(self, message, error_details=None, latex_log=None):
        super().__init__(message)
        self.error_details = error_details or []
        self.latex_log = latex_log

class LaTeXCompiler:
    """Безопасный компилятор LaTeX с детальной обработкой ошибок"""
    
    def __init__(self):
        self.latex_command = self._detect_latex_command()
        self.timeout = getattr(settings, 'LATEX_COMPILATION_TIMEOUT', 300)  # 5 минут
        self.max_file_size = getattr(settings, 'LATEX_MAX_FILE_SIZE', 50 * 1024 * 1024)  # 50MB
    
    def _detect_latex_command(self) -> Optional[str]:
        """Определяет доступную команду LaTeX"""
        commands_to_try = ['pdflatex', 'xelatex', 'lualatex']
        
        for cmd in commands_to_try:
            try:
                result = subprocess.run(
                    [cmd, '--version'], 
                    capture_output=True, 
                    timeout=10,
                    check=False
                )
                if result.returncode == 0:
                    logger.info(f"Найдена LaTeX команда: {cmd}")
                    return cmd
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        logger.warning("LaTeX команды не найдены в системе")
        return None
    
    def is_available(self) -> bool:
        """Проверяет доступность LaTeX"""
        return self.latex_command is not None
    
    def _safe_decode_bytes(self, byte_content: bytes) -> str:
        """НОВОЕ: Безопасное декодирование байтов в строку"""
        if not byte_content:
            return ""
        
        encodings_to_try = ['utf-8', 'latin1', 'cp1251', 'cp866', 'iso-8859-1']
        
        for encoding in encodings_to_try:
            try:
                return byte_content.decode(encoding)
            except UnicodeDecodeError:
                continue
        
        # Если все кодировки не сработали, декодируем с игнорированием ошибок
        return byte_content.decode('utf-8', errors='ignore')
    
    def _safe_read_log(self, log_file_path: Path) -> str:
        """Безопасное чтение лог файла с разными кодировками"""
        if not log_file_path.exists():
            return ""
        
        # Пробуем разные кодировки
        encodings_to_try = ['utf-8', 'latin1', 'cp1251', 'cp866', 'iso-8859-1']
        
        for encoding in encodings_to_try:
            try:
                with open(log_file_path, 'r', encoding=encoding, errors='ignore') as f:
                    content = f.read()
                logger.debug(f"Успешно прочитан лог с кодировкой: {encoding}")
                return content
            except Exception as e:
                logger.debug(f"Не удалось прочитать лог с кодировкой {encoding}: {e}")
                continue
        
        # Если все кодировки не сработали, читаем как binary и декодируем с игнорированием ошибок
        try:
            with open(log_file_path, 'rb') as f:
                content = f.read().decode('utf-8', errors='ignore')
            logger.warning("Лог прочитан в режиме binary с игнорированием ошибок")
            return content
        except Exception as e:
            logger.error(f"Не удалось прочитать лог файл: {e}")
            return f"Ошибка чтения лог файла: {e}"
    
    def parse_latex_log(self, log_content: str) -> Dict[str, any]:
        """Парсит лог LaTeX и извлекает ошибки"""
        errors = []
        warnings = []
        
        if not log_content:
            return {
                'errors': [],
                'warnings': [],
                'has_errors': False,
                'has_warnings': False,
                'total_issues': 0
            }
        
        # Регулярные выражения для поиска ошибок и предупреждений
        error_patterns = [
            r'! (.+)',  # Основные ошибки LaTeX
            r'.*Error: (.+)',  # Ошибки с префиксом Error
            r'.*Fatal error (.+)',  # Критические ошибки
        ]
        
        warning_patterns = [
            r'Warning: (.+)',  # Предупреждения
            r'LaTeX Warning: (.+)',  # LaTeX предупреждения
            r'Package .+ Warning: (.+)',  # Предупреждения пакетов
        ]
        
        lines = log_content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Ищем ошибки
            for pattern in error_patterns:
                try:
                    match = re.search(pattern, line)
                    if match:
                        error_context = self._get_error_context(lines, i)
                        errors.append({
                            'message': match.group(1).strip(),
                            'line_number': i + 1,
                            'context': error_context,
                            'severity': 'error'
                        })
                except Exception as e:
                    logger.debug(f"Ошибка при парсинге строки {i}: {e}")
            
            # Ищем предупреждения
            for pattern in warning_patterns:
                try:
                    match = re.search(pattern, line)
                    if match:
                        warnings.append({
                            'message': match.group(1).strip(),
                            'line_number': i + 1,
                            'severity': 'warning'
                        })
                except Exception as e:
                    logger.debug(f"Ошибка при парсинге предупреждения строки {i}: {e}")
        
        return {
            'errors': errors,
            'warnings': warnings,
            'has_errors': len(errors) > 0,
            'has_warnings': len(warnings) > 0,
            'total_issues': len(errors) + len(warnings)
        }
    
    def _get_error_context(self, lines: List[str], error_line: int, context_size: int = 2) -> List[str]:
        """Получает контекст вокруг строки с ошибкой"""
        start = max(0, error_line - context_size)
        end = min(len(lines), error_line + context_size + 1)
        
        context = []
        for i in range(start, end):
            prefix = '>>> ' if i == error_line else '    '
            context.append(f"{prefix}{lines[i].strip()}")
        
        return context
    
    def compile_latex_safe(self, latex_file: Path, output_dir: Path, 
                          max_attempts: int = 3) -> Dict[str, any]:
        """Безопасная компиляция LaTeX с детальной обработкой ошибок"""
        
        if not self.is_available():
            return {
                'success': False,
                'error_type': 'system_error',
                'message': 'LaTeX не установлен в системе',
                'pdf_path': None,
                'suggestions': [
                    'Установите LaTeX: sudo apt-get install texlive-full (Ubuntu)',
                    'Или используйте HTML генератор для создания документов'
                ]
            }
        
        # Проверяем размер файла
        try:
            if latex_file.stat().st_size > self.max_file_size:
                return {
                    'success': False,
                    'error_type': 'file_too_large',
                    'message': f'Файл слишком большой: {latex_file.stat().st_size / 1024 / 1024:.1f}MB',
                    'pdf_path': None
                }
        except Exception as e:
            logger.error(f"Ошибка проверки размера файла: {e}")
        
        # Создаем временную папку для компиляции
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            
            try:
                # Копируем LaTeX файл во временную папку
                temp_latex_file = temp_dir_path / latex_file.name
                shutil.copy2(latex_file, temp_latex_file)
                
                # Копируем все изображения
                try:
                    for image_file in output_dir.glob('*.png'):
                        shutil.copy2(image_file, temp_dir_path)
                    for image_file in output_dir.glob('*.jpg'):
                        shutil.copy2(image_file, temp_dir_path)
                    for image_file in output_dir.glob('*.jpeg'):
                        shutil.copy2(image_file, temp_dir_path)
                except Exception as e:
                    logger.warning(f"Ошибка копирования изображений: {e}")
                
                # Пытаемся скомпилировать
                for attempt in range(max_attempts):
                    try:
                        logger.info(f"LaTeX компиляция, попытка {attempt + 1}/{max_attempts}")
                        
                        # ИСПРАВЛЕНО: Убираем text=True для безопасной обработки кодировки
                        result = subprocess.run(
                            [
                                self.latex_command,
                                '-interaction=nonstopmode',  # Не останавливаться на ошибках
                                '-output-directory', str(temp_dir_path),
                                '-file-line-error',  # Показывать номера строк в ошибках
                                str(temp_latex_file)
                            ],
                            cwd=temp_dir_path,
                            capture_output=True,
                            # УБРАНО: text=True  <- Это вызывало ошибку кодировки
                            timeout=self.timeout
                        )
                        
                        # ИСПРАВЛЕНО: Безопасно декодируем вывод subprocess
                        stdout_content = self._safe_decode_bytes(result.stdout)
                        stderr_content = self._safe_decode_bytes(result.stderr)
                        
                        # Читаем лог файл безопасно
                        log_file = temp_dir_path / f"{temp_latex_file.stem}.log"
                        log_content = self._safe_read_log(log_file)
                        
                        # Парсим лог
                        log_analysis = self.parse_latex_log(log_content)
                        
                        # Проверяем результат компиляции
                        pdf_file = temp_dir_path / f"{temp_latex_file.stem}.pdf"
                        
                        if pdf_file.exists() and pdf_file.stat().st_size > 0:
                            # Успешная компиляция - копируем PDF в output_dir
                            output_pdf = output_dir / f"{latex_file.stem}.pdf"
                            shutil.copy2(pdf_file, output_pdf)
                            
                            return {
                                'success': True,
                                'pdf_path': str(output_pdf),
                                'attempts': attempt + 1,
                                'warnings': log_analysis.get('warnings', []),
                                'has_warnings': log_analysis.get('has_warnings', False),
                                'latex_log': log_content[:5000] if log_content else None  # Первые 5KB лога
                            }
                        
                        else:
                            # Неудачная компиляция
                            if attempt == max_attempts - 1:  # Последняя попытка
                                return {
                                    'success': False,
                                    'error_type': 'compilation_failed',
                                    'message': 'LaTeX компиляция завершилась с ошибками',
                                    'errors': log_analysis.get('errors', []),
                                    'warnings': log_analysis.get('warnings', []),
                                    'latex_log': log_content,
                                    'subprocess_stdout': stdout_content,  # ДОБАВЛЕНО: вывод процесса
                                    'subprocess_stderr': stderr_content,  # ДОБАВЛЕНО: ошибки процесса
                                    'suggestions': self._get_error_suggestions(log_analysis.get('errors', [])),
                                    'pdf_path': None
                                }
                            else:
                                # Не последняя попытка - продолжаем
                                logger.warning(f"Попытка {attempt + 1} неудачна, повторяем")
                                continue
                    
                    except subprocess.TimeoutExpired:
                        if attempt == max_attempts - 1:
                            return {
                                'success': False,
                                'error_type': 'timeout',
                                'message': f'Компиляция превысила лимит времени: {self.timeout}s',
                                'pdf_path': None,
                                'suggestions': [
                                    'Упростите документ или уменьшите количество изображений',
                                    'Проверьте наличие циклических зависимостей в формулах'
                                ]
                            }
                    
                    except Exception as e:
                        error_msg = f'Системная ошибка: {str(e)}'
                        logger.error(f"Попытка {attempt + 1} завершилась с ошибкой: {e}")
                        
                        if attempt == max_attempts - 1:
                            return {
                                'success': False,
                                'error_type': 'system_error', 
                                'message': error_msg,
                                'pdf_path': None
                            }
                        else:
                            continue
                            
            except Exception as e:
                logger.error(f"Ошибка подготовки к компиляции: {e}")
                return {
                    'success': False,
                    'error_type': 'preparation_error',
                    'message': f'Ошибка подготовки к компиляции: {str(e)}',
                    'pdf_path': None
                }
    
    def _get_error_suggestions(self, errors: List[Dict]) -> List[str]:
        """Генерирует предложения по исправлению ошибок"""
        suggestions = set()  # Используем set для избежания дубликатов
        
        for error in errors:
            message = error.get('message', '').lower()
            
            if 'undefined control sequence' in message:
                suggestions.add('Проверьте правильность написания LaTeX команд')
                suggestions.add('Убедитесь что используете только разрешенные математические команды')
            
            elif 'missing' in message and '$' in message:
                suggestions.add('Проверьте парность математических символов $ и $$')
                suggestions.add('Убедитесь что все формулы правильно закрыты')
            
            elif 'file not found' in message:
                suggestions.add('Проверьте что все изображения существуют и доступны')
                suggestions.add('Убедитесь что пути к файлам указаны корректно')
            
            elif 'package' in message and 'not found' in message:
                suggestions.add('Установите недостающие LaTeX пакеты')
                suggestions.add('Обратитесь к администратору для установки пакетов')
        
        # Общие предложения
        if not suggestions:
            suggestions.update([
                'Проверьте синтаксис LaTeX команд',
                'Убедитесь что все скобки закрыты правильно',
                'Попробуйте упростить формулы или разбить на части'
            ])
        
        return list(suggestions)

# Глобальный экземпляр компилятора
latex_compiler = LaTeXCompiler()

def compile_latex_to_pdf(latex_file: Path, output_dir: Path) -> Optional[str]:
    """Обертка для обратной совместимости"""
    result = latex_compiler.compile_latex_safe(latex_file, output_dir)
    
    if result['success']:
        return result['pdf_path']
    else:
        logger.error(f"LaTeX компиляция неудачна: {result.get('message')}")
        return None
