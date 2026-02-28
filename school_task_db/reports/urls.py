from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportsDashboardView.as_view(), name='dashboard'),
    path('heatmap/', views.HeatmapView.as_view(), name='heatmap'),
    path('heatmap/legacy/', views.HeatmapLegacyView.as_view(), name='heatmap-legacy'),
    path('heatmap/topic/<uuid:topic_pk>/', views.HeatmapDrilldownView.as_view(), name='heatmap-drilldown'),
    path('heatmap/topic/<uuid:topic_pk>/student/<uuid:student_pk>/', views.HeatmapStudentView.as_view(), name='heatmap-student'),
    path('heatmap/subtopic/<uuid:subtopic_pk>/', views.HeatmapSubtopicView.as_view(), name='heatmap-subtopic'),
    path('students/', views.StudentPerformanceView.as_view(), name='student-performance'),
    path('works/', views.WorkAnalysisView.as_view(), name='work-analysis'),
    path('events/', views.EventsStatusView.as_view(), name='events-status'),
]
