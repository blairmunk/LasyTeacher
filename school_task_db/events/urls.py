from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.EventListView.as_view(), name='list'),
    path('<int:pk>/', views.EventDetailView.as_view(), name='detail'),
    path('create/', views.EventCreateView.as_view(), name='create'),
    path('<int:pk>/update/', views.EventUpdateView.as_view(), name='update'),
    path('<int:event_id>/assign-variants/', views.assign_variants, name='assign-variants'),
]
