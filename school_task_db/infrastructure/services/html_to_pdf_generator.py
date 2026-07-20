"""HTML to PDF rendering backend for document engine infrastructure."""

import asyncio
import concurrent.futures
import logging
from pathlib import Path
from typing import Any

from django.conf import settings
from playwright.async_api import Page, async_playwright

logger = logging.getLogger(__name__)


class HtmlToPdfGenerator:
    def __init__(self, **options):
        self.options = self._default_options()
        self.options.update(options)

    def _default_options(self) -> dict[str, Any]:
        pdf_settings = getattr(settings, 'PDF_GENERATOR_SETTINGS', {})
        return {
            'format': pdf_settings.get('DEFAULT_FORMAT', 'A4'),
            'margin': pdf_settings.get(
                'DEFAULT_MARGIN',
                {
                    'top': '1cm',
                    'right': '1cm',
                    'bottom': '1cm',
                    'left': '1cm',
                },
            ),
            'print_background': pdf_settings.get('PRINT_BACKGROUND', True),
            'wait_for_mathjax': pdf_settings.get('WAIT_FOR_MATHJAX', True),
            'mathjax_timeout': pdf_settings.get('MATHJAX_TIMEOUT', 10000),
            'browser_timeout': 30000,
            'headless': True,
        }

    async def generate_pdf_async(
        self,
        html_file_path: Path,
        output_path: Path,
    ) -> Path:
        html_file_path = self._absolute_path(html_file_path)
        output_path = self._absolute_path(output_path)

        if not html_file_path.exists():
            raise FileNotFoundError(f'HTML file not found: {html_file_path}')

        output_path.parent.mkdir(parents=True, exist_ok=True)

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=self.options['headless'],
            )
            try:
                page = await browser.new_page()
                await page.goto(
                    html_file_path.as_uri(),
                    timeout=self.options['browser_timeout'],
                )
                if self.options['wait_for_mathjax']:
                    await self._wait_for_mathjax(page)

                await page.pdf(
                    path=str(output_path),
                    format=self.options['format'],
                    margin=self.options['margin'],
                    print_background=self.options['print_background'],
                    prefer_css_page_size=True,
                )
                return output_path
            finally:
                await browser.close()

    def generate_pdf(self, html_file_path: Path, output_path: Path) -> Path:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(
                self.generate_pdf_async(html_file_path, output_path),
            )

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                lambda: asyncio.run(
                    self.generate_pdf_async(html_file_path, output_path),
                )
            )
            return future.result()

    async def generate_multiple_pdfs_async(self, html_files: list) -> tuple:
        tasks = [
            self.generate_pdf_async(html_file, output_file)
            for html_file, output_file in html_files
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        successful = []
        errors = []
        for index, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append((html_files[index][0], result))
            else:
                successful.append(result)

        if errors:
            logger.warning('PDF generation failed for %s files', len(errors))
            for html_file, error in errors:
                logger.error('%s: %s', html_file, error)

        return successful, errors

    async def _wait_for_mathjax(self, page: Page):
        has_mathjax_script = await page.evaluate(
            """
            () => {
                const scripts = Array.from(document.querySelectorAll('script'));
                return scripts.some(script =>
                    script.src && script.src.includes('mathjax') ||
                    script.innerHTML.includes('MathJax')
                );
            }
            """
        )
        if not has_mathjax_script:
            return

        has_math_content = await page.evaluate(
            """
            () => {
                const text = document.body.innerText;
                return /\\$[^$]+\\$/.test(text);
            }
            """
        )
        if not has_math_content:
            return

        try:
            await page.wait_for_function(
                "typeof window.MathJax !== 'undefined'",
                timeout=5000,
            )
            await page.evaluate(
                """
                () => {
                    if (window.MathJax && window.MathJax.startup) {
                        window.mathJaxReady = false;
                        window.MathJax.startup.promise
                            .then(() => { window.mathJaxReady = true; })
                            .catch(() => { window.mathJaxReady = true; });
                    } else if (window.MathJax && window.MathJax.Hub) {
                        window.mathJaxReady = false;
                        window.MathJax.Hub.Register.StartupHook(
                            "End",
                            function() { window.mathJaxReady = true; }
                        );
                    } else {
                        window.mathJaxReady = true;
                    }
                }
                """
            )
            await page.wait_for_function(
                'window.mathJaxReady === true',
                timeout=8000,
            )
            await page.wait_for_timeout(500)
        except Exception as exc:
            logger.warning('MathJax wait failed: %s', exc)
            await page.wait_for_timeout(2000)

    def _absolute_path(self, path: Path) -> Path:
        path = Path(path)
        if path.is_absolute():
            return path
        return path.resolve()
