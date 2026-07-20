from django.urls import path

from .views import DocumentTemplateEditorView


app_name = 'document_generator'

urlpatterns = [
    path(
        'templates/',
        DocumentTemplateEditorView.as_view(),
        name='template-editor',
    ),
]
