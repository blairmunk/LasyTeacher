from django.apps import AppConfig

class HtmlGeneratorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'html_generator'
    verbose_name = 'HTML Document Generator'
    
    def ready(self):
        """Инициализация HTML генератора"""
        pass
