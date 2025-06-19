from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportsDashboardView.as_view(), name='dashboard'),
    path('students/', views.StudentPerformanceView.as_view(), name='student-performance'),
    path('works/', views.WorkAnalysisView.as_view(), name='work-analysis'),
    path('events/', views.EventsStatusView.as_view(), name='events-status'),
]
