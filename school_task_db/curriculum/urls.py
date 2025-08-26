from django.urls import path
from . import views

app_name = 'curriculum'

urlpatterns = [
    path('topics/', views.TopicListView.as_view(), name='topic-list'),
    path('topics/<pk:pk>/', views.TopicDetailView.as_view(), name='topic-detail'),
    path('courses/', views.CourseListView.as_view(), name='course-list'),
    path('courses/<pk:pk>/', views.CourseDetailView.as_view(), name='course-detail'),
    
    # API endpoints
    path('api/topics/<pk:topic_id>/subtopics/', views.topic_subtopics_api, name='topic-subtopics-api'),
]
