from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.TaskListView.as_view(), name='list'),
    path('<pk:pk>/', views.TaskDetailView.as_view(), name='detail'),  # int:pk → pk:pk
    path('create/', views.TaskCreateView.as_view(), name='create'),
    path('<pk:pk>/update/', views.TaskUpdateView.as_view(), name='update'),
    path('<pk:pk>/delete/', views.TaskDeleteView.as_view(), name='delete'),
    
    # AJAX endpoints
    path('ajax/load-subtopics/', views.load_subtopics, name='ajax-load-subtopics'),
    path('ajax/load-codifier/', views.load_codifier_elements, name='ajax-load-codifier'),

    # Управление кэшем (только для администраторов)
    path('admin/refresh-math-cache/', views.refresh_math_cache, name='refresh_math_cache'),
]
