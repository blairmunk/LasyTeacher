from django.urls import path

from .views import (
    PresentationProfileCreateView,
    PresentationProfileEditorView,
    PresentationProfileUpdateView,
)


app_name = 'document_engine'

urlpatterns = [
    path(
        'print-profiles/',
        PresentationProfileEditorView.as_view(),
        name='print-profile-editor',
    ),
    path(
        'print-profiles/create/',
        PresentationProfileCreateView.as_view(),
        name='print-profile-create',
    ),
    path(
        'print-profiles/<uuid:pk>/edit/',
        PresentationProfileUpdateView.as_view(),
        name='print-profile-update',
    ),
]
