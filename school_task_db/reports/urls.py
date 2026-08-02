from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportsDashboardView.as_view(), name='dashboard'),
    path('heatmap/', views.HeatmapView.as_view(), name='heatmap'),
    path('heatmap/course/<uuid:course_pk>/', views.HeatmapCourseView.as_view(), name='heatmap-course'),
    path('heatmap/topic/<uuid:topic_pk>/', views.HeatmapDrilldownView.as_view(), name='heatmap-drilldown'),
    path('heatmap/topic/<uuid:topic_pk>/student/<uuid:student_pk>/', views.HeatmapStudentView.as_view(), name='heatmap-student'),
    path('heatmap/subtopic/<uuid:subtopic_pk>/', views.HeatmapSubtopicView.as_view(), name='heatmap-subtopic'),
    path('students/', views.StudentPerformanceView.as_view(), name='student-performance'),
    path('works/', views.WorkAnalysisView.as_view(), name='work-analysis'),
    path('events/', views.EventsStatusView.as_view(), name='events-status'),
    path(
        'events/<uuid:event_pk>/performance/',
        views.EventPerformanceReportView.as_view(),
        name='event-performance',
    ),
    path(
        'events/<uuid:event_pk>/performance/document/',
        views.EventPerformanceReportDocumentView.as_view(),
        name='event-performance-document',
    ),
    path('student-digests/', views.StudentDigestView.as_view(), name='student-digests'),
    path(
        'student-digests/document/',
        views.StudentDigestDocumentView.as_view(),
        name='student-digests-document',
    ),
    path('journal/', views.JournalSelectView.as_view(), name='journal-select'),
    path('journal/<uuid:course_pk>/<uuid:group_pk>/', views.JournalView.as_view(), name='journal'),
    path('db-health/', views.TaskDBHealthView.as_view(), name='db-health'),
]
