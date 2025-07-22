from django.apps import AppConfig

class DocumentGeneratorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'document_generator'
    verbose_name = 'Document Generator Core'
    
    def ready(self):
        """Инициализация общих компонентов для генерации документов"""
        pass
