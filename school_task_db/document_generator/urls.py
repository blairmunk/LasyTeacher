from django.urls import path

from .views import DocumentTemplateCreateView, DocumentTemplateEditorView


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
]
