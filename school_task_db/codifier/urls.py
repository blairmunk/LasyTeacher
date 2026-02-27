# codifier/urls.py

from django.urls import path
from . import views

app_name = 'codifier'

urlpatterns = [
    path('', views.CodifierListView.as_view(), name='list'),
    path('<uuid:pk>/', views.CodifierDetailView.as_view(), name='spec-detail'),
]
