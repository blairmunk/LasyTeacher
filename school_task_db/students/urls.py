from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.StudentListView.as_view(), name='list'),
    path('<int:pk>/', views.StudentDetailView.as_view(), name='detail'),
    path('create/', views.StudentCreateView.as_view(), name='create'),
    path('<int:pk>/update/', views.StudentUpdateView.as_view(), name='update'),
    
    path('student_groups/', views.StudentGroupListView.as_view(), name='group-list'),
    path('student_groups/<int:pk>/', views.StudentGroupDetailView.as_view(), name='group-detail'),
    path('student_groups/create/', views.StudentGroupCreateView.as_view(), name='group-create'),
    path('student_groups/<int:pk>/update/', views.StudentGroupUpdateView.as_view(), name='group-update'),
]
