from django.urls import path
from . import views


app_name = 'task_manager'  # Добавляем namespace


urlpatterns = [
    # Главная страница
    path('', views.index, name='index'),
    
    # Задания
    path('tasks/', views.TaskListView.as_view(), name='task-list'),
    path('tasks/<int:pk>/', views.TaskDetailView.as_view(), name='task-detail'),
    path('tasks/new/', views.TaskCreateView.as_view(), name='task-create'),
    path('tasks/<int:pk>/edit/', views.TaskUpdateView.as_view(), name='task-update'),
    
    # Группы аналогов
    path('analog-groups/', views.AnalogGroupListView.as_view(), name='analoggroup-list'),
    path('analog-groups/<int:pk>/', views.AnalogGroupDetailView.as_view(), name='analoggroup-detail'),
    
    # Работы
    path('works/', views.WorkListView.as_view(), name='work-list'),
    path('works/<int:pk>/', views.WorkDetailView.as_view(), name='work-detail'),
    path('works/new/', views.WorkCreateView.as_view(), name='work-create'),
    path('works/<int:work_id>/generate-variants/', views.generate_variants, name='generate-variants'),
    
    # Варианты
    path('variants/', views.VariantListView.as_view(), name='variant-list'),
    path('variants/<int:pk>/', views.VariantDetailView.as_view(), name='variant-detail'),
    
    # Ученики
    path('students/', views.StudentListView.as_view(), name='student-list'),
    path('students/new/', views.StudentCreateView.as_view(), name='student-create'),
    
    # Классы
    path('groups/', views.StudentGroupListView.as_view(), name='studentgroup-list'),
    path('groups/<int:pk>/', views.StudentGroupDetailView.as_view(), name='studentgroup-detail'),
    
    # События
    path('events/', views.EventListView.as_view(), name='event-list'),
    path('events/<int:pk>/', views.EventDetailView.as_view(), name='event-detail'),
    path('events/new/', views.EventCreateView.as_view(), name='event-create'),
    path('events/<int:event_id>/assign-variants/', views.assign_variants, name='assign-variants'),
    
    # Отчёты
    path('reports/', views.reports_view, name='reports'),
    
    # API
    path('api/analog-groups/<int:group_id>/tasks/', views.analog_group_tasks_api, name='analog-group-tasks-api'),
]