"""HTML→PDF генератор через Playwright"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urljoin
from urllib.request import pathname2url

from playwright.async_api import async_playwright, Browser, Page
from django.conf import settings

logger = logging.getLogger(__name__)

class HtmlToPdfGenerator:
    """Генератор PDF из HTML файлов через Playwright/Chromium"""
    
    def __init__(self, **options):
        self.options = self._get_default_options()
        self.options.update(options)
    
    def _get_default_options(self) -> Dict[str, Any]:
        """Возвращает настройки по умолчанию"""
        pdf_settings = getattr(settings, 'PDF_GENERATOR_SETTINGS', {})
        
        return {
            'format': pdf_settings.get('DEFAULT_FORMAT', 'A4'),
            'margin': pdf_settings.get('DEFAULT_MARGIN', {
                'top': '1cm', 'right': '1cm', 'bottom': '1cm', 'left': '1cm'
            }),
            'print_background': pdf_settings.get('PRINT_BACKGROUND', True),
            'wait_for_mathjax': pdf_settings.get('WAIT_FOR_MATHJAX', True),
            'mathjax_timeout': pdf_settings.get('MATHJAX_TIMEOUT', 10000),
            'browser_timeout': 30000,  # 30 секунд
            'headless': True,
        }
    
    async def generate_pdf_async(self, html_file_path: Path, output_path: Path) -> Path:
        """ИСПРАВЛЕНО: Асинхронная генерация PDF из HTML файла"""
        html_file_path = Path(html_file_path)
        output_path = Path(output_path)
        
        # ИСПРАВЛЕНО: Преобразуем в абсолютный путь
        if not html_file_path.is_absolute():
            html_file_path = html_file_path.resolve()
        
        if not html_file_path.exists():
            raise FileNotFoundError(f"HTML файл не найден: {html_file_path}")
        
        # ИСПРАВЛЕНО: Преобразуем output тоже в абсолютный
        if not output_path.is_absolute():
            output_path = output_path.resolve()
        
        # Создаем выходную директорию если нужно
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Начинаем генерацию PDF: {html_file_path} → {output_path}")
        
        async with async_playwright() as playwright:
            # Запускаем headless Chromium
            browser = await playwright.chromium.launch(
                headless=self.options['headless']
            )
            
            try:
                page = await browser.new_page()
                
                # ИСПРАВЛЕНО: Используем абсолютный путь для file:// URL
                file_url = html_file_path.as_uri()
                logger.debug(f"Загружаем HTML: {file_url}")
                
                await page.goto(file_url, timeout=self.options['browser_timeout'])
                
                # Ждем загрузки MathJax если включено
                if self.options['wait_for_mathjax']:
                    await self._wait_for_mathjax(page)
                
                # Генерируем PDF
                pdf_options = {
                    'path': str(output_path),
                    'format': self.options['format'],
                    'margin': self.options['margin'],
                    'print_background': self.options['print_background'],
                    'prefer_css_page_size': True,  # Используем CSS @page правила
                }
                
                logger.debug(f"Генерируем PDF с настройками: {pdf_options}")
                await page.pdf(**pdf_options)
                
                logger.info(f"✅ PDF успешно создан: {output_path}")
                return output_path
                
            except Exception as e:
                logger.error(f"Ошибка генерации PDF: {e}")
                raise
            finally:
                await browser.close()
    
    async def _wait_for_mathjax(self, page: Page):
        """КАРДИНАЛЬНО УЛУЧШЕННОЕ: Умное ожидание MathJax с быстрой диагностикой"""
        logger.debug("Проверяем наличие и статус MathJax...")
        
        try:
            # ШАГ 1: Быстрая проверка - есть ли MathJax в HTML
            has_mathjax_script = await page.evaluate("""
                () => {
                    const scripts = Array.from(document.querySelectorAll('script'));
                    return scripts.some(script => 
                        script.src && script.src.includes('mathjax') || 
                        script.innerHTML.includes('MathJax')
                    );
                }
            """)
            
            if not has_mathjax_script:
                logger.debug("❌ MathJax скрипт не найден в HTML - пропускаем ожидание")
                return
            
            # ШАГ 2: Проверяем есть ли формулы для рендеринга
            has_math_content = await page.evaluate("""
                () => {
                    const text = document.body.innerText;
                    // Ищем формулы $...$ или $$...$$
                    return /\$[^$]+\$/.test(text);
                }
            """)
            
            if not has_math_content:
                logger.debug("ℹ️ Формулы не найдены - MathJax не нужен")
                return
            
            logger.debug("✅ MathJax скрипт найден, формулы есть - ожидаем загрузки...")
            
            # ШАГ 3: Ждем загрузки MathJax (но не более 5 сек)
            try:
                await page.wait_for_function(
                    "typeof window.MathJax !== 'undefined'",
                    timeout=5000  # Только 5 сек на загрузку скрипта
                )
                logger.debug("✅ MathJax объект загружен")
            except:
                logger.warning("⚠️ MathJax не загрузился за 5 сек - возможно проблема с CDN")
                return
            
            # ШАГ 4: Используем правильный колбэк для MathJax 3.x
            await page.evaluate("""
                () => {
                    if (window.MathJax && window.MathJax.startup) {
                        // Устанавливаем флаг готовности
                        window.mathJaxReady = false;
                        
                        // Для MathJax 3.x используем promise
                        window.MathJax.startup.promise.then(() => {
                            console.log('MathJax 3.x полностью готов');
                            window.mathJaxReady = true;
                        }).catch((err) => {
                            console.log('MathJax 3.x ошибка:', err);
                            window.mathJaxReady = true; // Считаем готовым даже с ошибкой
                        });
                    } else if (window.MathJax && window.MathJax.Hub) {
                        // Для MathJax 2.x используем StartupHook
                        window.mathJaxReady = false;
                        window.MathJax.Hub.Register.StartupHook("End", function() {
                            console.log('MathJax 2.x полностью готов');
                            window.mathJaxReady = true;
                        });
                    } else {
                        // Неизвестная версия - считаем готовым
                        window.mathJaxReady = true;
                    }
                }
            """)
            
            # ШАГ 5: Ждем флаг готовности (максимум 8 сек)
            await page.wait_for_function(
                "window.mathJaxReady === true",
                timeout=8000  # 8 сек на рендеринг формул
            )
            
            # Небольшая задержка для стабильности
            await page.wait_for_timeout(500)
            
            logger.debug("✅ MathJax полностью готов к генерации PDF")
            
        except Exception as e:
            logger.warning(f"MathJax таймаут или ошибка: {e}")
            
            # Диагностируем проблему
            try:
                diagnosis = await page.evaluate("""
                    () => {
                        return {
                            mathJaxExists: typeof window.MathJax !== 'undefined',
                            mathJaxVersion: window.MathJax ? (window.MathJax.version || 'unknown') : 'none',
                            hasStartup: window.MathJax && !!window.MathJax.startup,
                            hasHub: window.MathJax && !!window.MathJax.Hub,
                            readyFlag: window.mathJaxReady,
                            mathElements: document.querySelectorAll('.MathJax').length,
                            errorElements: document.querySelectorAll('.MathJax_Error').length
                        };
                    }
                """)
                logger.debug(f"MathJax диагностика: {diagnosis}")
                
                # Если есть ошибки MathJax - предупреждаем
                if diagnosis.get('errorElements', 0) > 0:
                    logger.warning("⚠️ Обнаружены ошибки рендеринга MathJax в документе")
                    
            except:
                logger.debug("Не удалось получить диагностику MathJax")
            
            # Даем еще 2 сек и продолжаем
            await page.wait_for_timeout(2000)
            logger.info("Продолжаем генерацию PDF несмотря на проблемы с MathJax")
    
    def generate_pdf(self, html_file_path: Path, output_path: Path) -> Path:
        """Синхронный wrapper для асинхронной генерации PDF"""
        try:
            # Проверяем есть ли уже running event loop
            loop = asyncio.get_running_loop()
            # Если есть, создаем новый loop в thread (для Django)
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    lambda: asyncio.run(self.generate_pdf_async(html_file_path, output_path))
                )
                return future.result()
        except RuntimeError:
            # Нет running loop, можем использовать asyncio.run
            return asyncio.run(self.generate_pdf_async(html_file_path, output_path))
    
    async def generate_multiple_pdfs_async(self, html_files: list) -> list:
        """Генерирует несколько PDF файлов параллельно"""
        tasks = []
        
        for html_file, output_file in html_files:
            task = self.generate_pdf_async(html_file, output_file)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = []
        errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append((html_files[i][0], result))
            else:
                successful.append(result)
        
        if errors:
            logger.warning(f"Ошибки при генерации {len(errors)} PDF файлов")
            for html_file, error in errors:
                logger.error(f"  {html_file}: {error}")
        
        logger.info(f"✅ Успешно создано PDF файлов: {len(successful)}")
        return successful, errors
