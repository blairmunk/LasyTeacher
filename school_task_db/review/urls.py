from django.urls import path
from . import views

app_name = 'review'

urlpatterns = [
    path('', views.ReviewDashboardView.as_view(), name='dashboard'),
    path('event/<int:pk>/', views.EventReviewView.as_view(), name='event-review'),
    path('participation/<int:pk>/', views.ParticipationReviewView.as_view(), name='participation-review'),
    path('ajax/calculate-score/', views.ajax_calculate_score, name='ajax-calculate-score'),
]
