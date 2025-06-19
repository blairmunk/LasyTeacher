from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.EventListView.as_view(), name='list'),
    path('<int:pk>/', views.EventDetailView.as_view(), name='detail'),
    path('create/', views.EventCreateView.as_view(), name='create'),
    path('<int:pk>/update/', views.EventUpdateView.as_view(), name='update'),
    path('<int:event_id>/add-participants/', views.add_participants, name='add-participants'),
    path('<int:event_id>/assign-variants/', views.assign_variants, name='assign-variants'),
    path('review/', views.review_works, name='review-works'),
    path('participation/<int:participation_id>/grade/', views.grade_participation, name='grade-participation'),
]
