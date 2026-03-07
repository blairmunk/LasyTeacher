from django.urls import path
from . import views, views_generation

app_name = 'works'

urlpatterns = [
    path('', views.WorkListView.as_view(), name='list'),
    path('create/', views.WorkCreateView.as_view(), name='create'),
    path('variants/', views.VariantListView.as_view(), name='variant-list'),
    path('variants/orphans/', views.OrphanVariantListView.as_view(), name='orphan-variants'),
    path('variants/<pk:pk>/delete/', views.VariantDeleteView.as_view(), name='variant-delete'),
    path('<pk:work_id>/bulk-delete-variants/', views.bulk_delete_variants, name='bulk-delete-variants'),
    path('variants/<pk:pk>/', views.VariantDetailView.as_view(), name='variant-detail'),
    path('<pk:pk>/', views.WorkDetailView.as_view(), name='detail'),
    path('<pk:pk>/update/', views.WorkUpdateView.as_view(), name='update'),
    path('<pk:work_id>/generate-variants/', views.generate_variants, name='generate-variants'),
    path('<pk:work_id>/sync-groups/', views.sync_analog_groups, name='sync-groups'),

    # Генерация документов
    path('download/<str:file_type>/<str:filename>/', views_generation.download_generated_file, name='download_generated_file'),
    path('ajax/generate/<pk:work_id>/', views_generation.generate_work_ajax, name='generate_work_ajax'),
    path('ajax/generate/variant/<pk:variant_id>/', views_generation.generate_variant_ajax, name='generate_variant_ajax'),
    path('ajax/generation-status/', views_generation.generation_status_ajax, name='generation_status_ajax'),
    path('create-from-orphans/', views.create_work_from_orphans, name='create-work-from-orphans'),

]

