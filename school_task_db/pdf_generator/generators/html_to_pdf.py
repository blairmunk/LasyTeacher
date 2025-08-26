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
        """ИСПРАВЛЕНО: Улучшенное ожидание MathJax с graceful fallback"""
        logger.debug("Ожидаем загрузки MathJax...")
        
        try:
            # Проверяем наличие MathJax
            mathjax_exists = await page.evaluate("typeof window.MathJax !== 'undefined'")
            
            if not mathjax_exists:
                logger.debug("MathJax не найден на странице, пропускаем ожидание")
                return
            
            # ИСПРАВЛЕНО: Более надежная проверка готовности MathJax
            await page.wait_for_function(
                """
                () => {
                    try {
                        if (typeof window.MathJax === 'undefined') return true;
                        
                        // MathJax 3.x проверка
                        if (window.MathJax.startup) {
                            const state = window.MathJax.startup.document.state();
                            console.log('MathJax state:', state);
                            return state >= 8; // ИСПРАВЛЕНО: Менее строгий критерий (было >= 10)
                        }
                        
                        // MathJax 2.x проверка (fallback)
                        if (window.MathJax.Hub) {
                            return window.MathJax.Hub.queue.pending === 0;
                        }
                        
                        // Если неизвестная версия, считаем готовым через 3 сек
                        return true;
                    } catch (e) {
                        console.log('MathJax check error:', e);
                        return true; // При ошибке считаем готовым
                    }
                }
                """,
                timeout=15000  # ИСПРАВЛЕНО: Увеличен timeout до 15 сек
            )
            
            # ИСПРАВЛЕНО: Дополнительное ожидание завершения рендеринга
            await page.wait_for_timeout(2000)  # 2 секунды буфера
            
            logger.debug("✅ MathJax готов")
            
        except Exception as e:
            # ИСПРАВЛЕНО: Более детальная диагностика
            logger.warning(f"Таймаут MathJax (продолжаем генерацию): {e}")
            
            # Дополнительная диагностика
            try:
                mathjax_info = await page.evaluate("""
                    () => {
                        if (typeof window.MathJax !== 'undefined') {
                            return {
                                version: window.MathJax.version || 'unknown',
                                startup_state: window.MathJax.startup ? window.MathJax.startup.document.state() : 'no startup',
                                hub_pending: window.MathJax.Hub ? window.MathJax.Hub.queue.pending : 'no hub'
                            };
                        }
                        return 'MathJax not found';
                    }
                """)
                logger.debug(f"MathJax диагностика: {mathjax_info}")
            except:
                pass
            
            # Даем еще немного времени и продолжаем
            await page.wait_for_timeout(3000)
    
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
