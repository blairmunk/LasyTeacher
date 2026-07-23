from django.urls import path

from .views import (
    DocumentTemplateCreateView,
    DocumentTemplateEditorView,
    DocumentTemplateUpdateView,
)


app_name = 'document_generator'

urlpatterns = [
    path(
        'print-profiles/',
        DocumentTemplateEditorView.as_view(),
        name='print-profile-editor',
    ),
    path(
        'print-profiles/create/',
        DocumentTemplateCreateView.as_view(),
        name='print-profile-create',
    ),
    path(
        'print-profiles/<uuid:pk>/edit/',
        DocumentTemplateUpdateView.as_view(),
        name='print-profile-update',
    ),
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
