from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.EventListView.as_view(), name='list'),
    path('<pk:pk>/', views.EventDetailView.as_view(), name='detail'),
    path('create/', views.EventCreateView.as_view(), name='create'),
    path('<pk:pk>/update/', views.EventUpdateView.as_view(), name='update'),
    path('<pk:event_id>/add-participants/', views.add_participants, name='add-participants'),
    path('<pk:event_id>/assign-variants/', views.assign_variants, name='assign-variants'),
    path('review/', views.review_works, name='review-works'),
    path('participation/<pk:participation_id>/grade/', views.grade_participation, name='grade-participation'),
]
