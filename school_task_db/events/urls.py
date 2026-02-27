from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.EventListView.as_view(), name='list'),
    path('<uuid:pk>/', views.EventDetailView.as_view(), name='detail'),
    path('create/', views.EventCreateView.as_view(), name='create'),
    path('<uuid:pk>/update/', views.EventUpdateView.as_view(), name='update'),
    path('<uuid:event_id>/add-participants/', views.add_participants, name='add-participants'),
    path('<uuid:event_id>/assign-variants/', views.assign_variants, name='assign-variants'),
    path('<uuid:event_id>/change-status/', views.change_status, name='change-status'),
    path('review/', views.review_works, name='review-works'),
    path('participation/<uuid:participation_id>/grade/', views.grade_participation, name='grade-participation'),
]
