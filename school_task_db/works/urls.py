from django.urls import path
from . import views, views_rendering

app_name = 'works'

urlpatterns = [
    path('', views.WorkListView.as_view(), name='list'),
    path('create/', views.WorkCreateView.as_view(), name='create'),
    path('variants/', views.VariantListView.as_view(), name='variant-list'),
    path(
        'variants/orphans/',
        views.OrphanVariantListView.as_view(),
        name='orphan-variants',
    ),
    path(
        'variants/<pk:pk>/delete/',
        views.VariantDeleteView.as_view(),
        name='variant-delete',
    ),
    path(
        '<pk:work_id>/bulk-delete-variants/',
        views.bulk_delete_variants,
        name='bulk-delete-variants',
    ),
    path('variants/<pk:pk>/', views.VariantDetailView.as_view(), name='variant-detail'),
    path('<pk:pk>/', views.WorkDetailView.as_view(), name='detail'),
    path('<pk:pk>/update/', views.WorkUpdateView.as_view(), name='update'),
    path('<pk:work_id>/compose/', views.compose_variants, name='compose-variants'),
    path(
        '<pk:work_id>/generate-variants/',
        views.compose_variants,
        name='generate-variants',
    ),
    path('<pk:work_id>/sync-groups/', views.sync_analog_groups, name='sync-groups'),
    path(
        'create-from-orphans/',
        views.create_work_from_orphans,
        name='create-work-from-orphans',
    ),

    # Рендеринг документов
    path(
        'download/<str:file_type>/<str:filename>/',
        views_rendering.download_rendered_file,
        name='download_rendered_file',
    ),
    path(
        'ajax/render/<pk:work_id>/',
        views_rendering.render_work_ajax,
        name='render_work_ajax',
    ),
    path(
        'ajax/render/variant/<pk:variant_id>/',
        views_rendering.render_variant_ajax,
        name='render_variant_ajax',
    ),
    path(
        'ajax/render-status/',
        views_rendering.render_status_ajax,
        name='render_status_ajax',
    ),
    path(
        'ajax/render/remedial/<uuid:variant_id>/',
        views_rendering.render_remedial_sheet_ajax,
        name='render-remedial-sheet',
    ),
]
