from django.urls import path
from . import views


app_name = 'core'


urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('search/', views.global_search, name='search'),  # ДОБАВИТЬ ЭТУ СТРОКУ
]