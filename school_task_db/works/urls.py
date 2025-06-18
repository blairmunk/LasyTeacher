from django.urls import path
from . import views

app_name = 'works'

urlpatterns = [
    path('', views.WorkListView.as_view(), name='list'),
    path('<int:pk>/', views.WorkDetailView.as_view(), name='detail'),
    path('create/', views.WorkCreateView.as_view(), name='create'),
    path('<int:pk>/update/', views.WorkUpdateView.as_view(), name='update'),
    path('<int:work_id>/generate-variants/', views.generate_variants, name='generate-variants'),
    path('variants/', views.VariantListView.as_view(), name='variant-list'),
    path('variants/<int:pk>/', views.VariantDetailView.as_view(), name='variant-detail'),
]
