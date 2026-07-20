from django.urls import path

from .views import (
    DocumentTemplateCreateView,
    DocumentTemplateEditorView,
    DocumentTemplateUpdateView,
)


app_name = 'document_generator'

urlpatterns = [
    path(
        'templates/',
        DocumentTemplateEditorView.as_view(),
        name='template-editor',
    ),
    path(
        'templates/create/',
        DocumentTemplateCreateView.as_view(),
        name='template-create',
    ),
    path(
        'templates/<uuid:pk>/edit/',
        DocumentTemplateUpdateView.as_view(),
        name='template-update',
    ),
]
