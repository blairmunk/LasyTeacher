from django.urls import path
from . import views, views_generation

app_name = 'works'

urlpatterns = [
    path('', views.WorkListView.as_view(), name='list'),
    path('<int:pk>/', views.WorkDetailView.as_view(), name='detail'),
    path('create/', views.WorkCreateView.as_view(), name='create'),
    path('<int:pk>/update/', views.WorkUpdateView.as_view(), name='update'),
    path('<int:work_id>/generate-variants/', views.generate_variants, name='generate-variants'),
    path('variants/', views.VariantListView.as_view(), name='variant-list'),
    path('variants/<int:pk>/', views.VariantDetailView.as_view(), name='variant-detail'),
    path('download/<str:file_type>/<str:filename>/', views_generation.download_generated_file, name='download_generated_file'),
    path('ajax/generate/<int:work_id>/', views_generation.generate_work_ajax, name='generate_work_ajax'),
    path('ajax/generate/variant/<int:variant_id>/', views_generation.generate_variant_ajax, name='generate_variant_ajax'), 
    path('ajax/generation-status/', views_generation.generation_status_ajax, name='generation_status_ajax'),
]
