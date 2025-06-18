from django.urls import path
from . import views

app_name = 'task_groups'

urlpatterns = [
    path('', views.AnalogGroupListView.as_view(), name='list'),
    path('<int:pk>/', views.AnalogGroupDetailView.as_view(), name='detail'),
    path('create/', views.AnalogGroupCreateView.as_view(), name='create'),
    path('<int:pk>/update/', views.AnalogGroupUpdateView.as_view(), name='update'),
    path('<int:group_id>/add-tasks/', views.add_tasks_to_group, name='add-tasks'),
    path('<int:group_id>/remove-task/<int:task_id>/', views.remove_task_from_group, name='remove-task'),
]
