from django.urls import path

from .views import (
    PrintSettingsCreateView,
    PrintSettingsEditorView,
    PrintSettingsUpdateView,
)


app_name = 'document_engine'

urlpatterns = [
    path(
        'print-profiles/',
        PrintSettingsEditorView.as_view(),
        name='print-profile-editor',
    ),
    path(
        'print-profiles/create/',
        PrintSettingsCreateView.as_view(),
        name='print-profile-create',
    ),
    path(
        'print-profiles/<uuid:pk>/edit/',
        PrintSettingsUpdateView.as_view(),
        name='print-profile-update',
    ),
]
