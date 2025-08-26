from django.urls import path
from . import views

app_name = 'task_groups'

urlpatterns = [
    path('', views.AnalogGroupListView.as_view(), name='list'),
    path('<pk:pk>/', views.AnalogGroupDetailView.as_view(), name='detail'),
    path('create/', views.AnalogGroupCreateView.as_view(), name='create'),
    path('<pk:pk>/update/', views.AnalogGroupUpdateView.as_view(), name='update'),
    path('<pk:group_id>/add-tasks/', views.add_tasks_to_group, name='add-tasks'),
    path('<pk:group_id>/remove-task/<pk:task_id>/', views.remove_task_from_group, name='remove-task'),
]
