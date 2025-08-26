from django.apps import AppConfig

class PdfGeneratorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pdf_generator'
    verbose_name = 'PDF Generator (HTML→PDF)'
    
    def ready(self):
        """Инициализация PDF генератора"""
        # Проверяем что Playwright доступен
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            import warnings
            warnings.warn(
                "Playwright не установлен. PDF генерация недоступна. "
                "Установите: pip install playwright && playwright install chromium"
            )
