from django.urls import path
from . import views

app_name = 'latex_generator'

urlpatterns = [
    # Временно убираем URL'ы
    # path('generate/', views.GenerateView.as_view(), name='generate'),
    # path('status/', views.StatusView.as_view(), name='status'),
]
