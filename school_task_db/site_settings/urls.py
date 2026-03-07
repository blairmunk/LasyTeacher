from django.urls import path
from . import views

app_name = 'site_settings'

urlpatterns = [
    path('', views.SiteSettingsView.as_view(), name='index'),
]
