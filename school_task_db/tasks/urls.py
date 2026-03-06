from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.TaskListView.as_view(), name='list'),
    path('create/', views.TaskCreateView.as_view(), name='create'),
    path('<pk:pk>/', views.TaskDetailView.as_view(), name='detail'),
    path('<pk:pk>/update/', views.TaskUpdateView.as_view(), name='update'),
    path('<pk:pk>/delete/', views.TaskDeleteView.as_view(), name='delete'),

    # Источники
    path('sources/', views.SourceListView.as_view(), name='source-list'),
    path('sources/create/', views.SourceCreateView.as_view(), name='source-create'),

    # AJAX endpoints
    path('ajax/load-subtopics/', views.load_subtopics, name='ajax-load-subtopics'),
    path('ajax/load-codifier/', views.load_codifier_elements, name='ajax-load-codifier'),

    # Bulk actions
    path('ajax/bulk-create-group/', views.bulk_create_group, name='bulk-create-group'),
    path('ajax/bulk-add-to-group/', views.bulk_add_to_group, name='bulk-add-to-group'),
    path('ajax/bulk-remove-from-groups/', views.bulk_remove_from_groups, name='bulk-remove-from-groups'),
    path('ajax/bulk-create-work/', views.bulk_create_work, name='bulk-create-work'),

    # Управление кэшем
    path('admin/refresh-math-cache/', views.refresh_math_cache, name='refresh_math_cache'),
]
