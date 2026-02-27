from django.urls import path
from . import views

app_name = 'review'

urlpatterns = [
    path('', views.ReviewDashboardView.as_view(), name='dashboard'),
    path('event/<uuid:pk>/', views.EventReviewView.as_view(), name='event-review'),
    path('event/<uuid:pk>/finalize/', views.finalize_event, name='finalize-event'),
    path('participation/<uuid:pk>/', views.ParticipationReviewView.as_view(), name='participation-review'),
    path('ajax/calculate-score/', views.ajax_calculate_score, name='ajax-calculate-score'),
    path('participation/<uuid:pk>/toggle-absent/', views.toggle_absent, name='toggle-absent'),
]