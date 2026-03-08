from django.urls import path
from django.views import View
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.StudentListView.as_view(), name='list'),
    path('<uuid:pk>/', views.StudentDetailView.as_view(), name='detail'),
    path('create/', views.StudentCreateView.as_view(), name='create'),
    path('<uuid:pk>/update/', views.StudentUpdateView.as_view(), name='update'),
    
    path('student_groups/', views.StudentGroupListView.as_view(), name='group-list'),
    path('student_groups/<uuid:pk>/', views.StudentGroupDetailView.as_view(), name='group-detail'),
    path('student_groups/create/', views.StudentGroupCreateView.as_view(), name='group-create'),
    path('student_groups/<uuid:pk>/update/', views.StudentGroupUpdateView.as_view(), name='group-update'),
    path('<pk>/remedial/', views.RemedialWorkView.as_view(), name='remedial'),
    path('remedial-wizard/', views.RemedialWizardView.as_view(), name='remedial-wizard'),
    path('remedial-from-event/<uuid:event_pk>/', views.RemedialFromEventView.as_view(), name='remedial-from-event'),


]
