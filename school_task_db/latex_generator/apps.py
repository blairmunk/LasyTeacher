from django.apps import AppConfig

class LatexGeneratorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'latex_generator'
    verbose_name = 'LaTeX Generator'
    
    def ready(self):
        """Инициализация при запуске приложения"""
        pass
