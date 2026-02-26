from django.urls import path
from . import views
from . import views_import


app_name = 'core'


urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('search/', views.global_search, name='search'), 
    
    # Импорт
    path('import/', views_import.ImportPageView.as_view(), name='import'),
    path('import/validate/', views_import.validate_json_ajax, name='import-validate'),
    path('import/execute/', views_import.execute_import_ajax, name='import-execute'),
    path('import/history/', views_import.ImportHistoryView.as_view(), name='import-history'),
    path('import/sample/', views_import.download_sample_json, name='import-sample'),
    
    # Экспорт
    path('export/', views_import.export_tasks_ajax, name='export'),
]
