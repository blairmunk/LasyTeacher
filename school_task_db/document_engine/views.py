from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.views.generic import TemplateView

from infrastructure.container import container
from infrastructure.forms.presentation_profile_django_forms import (
    PresentationProfileForm,
)
from core_logic.use_cases.get_presentation_profile_form_data import (
    GetPresentationProfileFormDataRequest,
)
from core_logic.value_objects.document_recipes import WORK_DOCUMENT_TYPE


class PresentationProfileEditorView(TemplateView):
    template_name = 'document_engine/presentation_profile_editor.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        adapter = container.presentation_profile_form_adapter
        request = adapter.editor_data_request_from_query(self.request.GET)
        editor_data = (
            container
            .get_presentation_profile_editor_data_use_case()
            .execute(request)
        )
        context.update(adapter.editor_context(editor_data, request))
        return context


class PresentationProfileCreateView(TemplateView):
    template_name = 'document_engine/presentation_profile_form.html'
    page_title = 'Новый профиль оформления'

    def get_context_data(self, **kwargs):
        form_data = kwargs.pop('form_data', None) or self._form_data()
        context = super().get_context_data(**kwargs)
        form = kwargs.get('form') or self._form(
            form_data=form_data,
            initial={
                'document_type': self.request.GET.get(
                    'type',
                    WORK_DOCUMENT_TYPE,
                ),
            },
        )
        context.update(
            container.presentation_profile_form_adapter.create_context(
                form=form,
                document_types=form_data.document_types,
            )
        )
        context['page_title'] = self.page_title
        context['submit_label'] = 'Сохранить'
        return context

    def post(self, request, *args, **kwargs):
        form_data = self._form_data()
        form = self._form(data=request.POST, form_data=form_data)
        if not form.is_valid():
            return self.render_to_response(
                self.get_context_data(form=form, form_data=form_data),
            )

        result = container.create_presentation_profile_use_case().execute(
            container
            .presentation_profile_form_adapter
            .create_presentation_profile_params_from_form(form)
        )
        if not result.success:
            for error in result.errors:
                form.add_error(None, error)
            return self.render_to_response(
                self.get_context_data(form=form, form_data=form_data),
            )

        messages.success(request, 'Профиль оформления создан.')
        return redirect('document_engine:print-profile-editor')

    def _form(self, *args, form_data=None, **kwargs):
        form_data = form_data or self._form_data()
        return PresentationProfileForm(
            *args,
            document_types=form_data.document_types,
            **kwargs,
        )

    def _form_data(self, presentation_profile_id=''):
        return (
            container
            .get_presentation_profile_form_data_use_case()
            .execute(
                GetPresentationProfileFormDataRequest(
                    presentation_profile_id=presentation_profile_id,
                    renderable_only=True,
                ),
            )
        )


class PresentationProfileUpdateView(PresentationProfileCreateView):
    page_title = 'Редактирование профиля оформления'

    def _form_data(self, presentation_profile_id=''):
        form_data = super()._form_data(
            presentation_profile_id or str(self.kwargs['pk']),
        )
        if form_data.presentation_profile is None:
            raise Http404('Профиль оформления не найден')
        return form_data

    def get_context_data(self, **kwargs):
        form_data = kwargs.pop('form_data', None) or self._form_data()
        presentation_profile = form_data.presentation_profile
        form = kwargs.get('form') or self._form(
            form_data=form_data,
            initial=(
                container
                .presentation_profile_form_adapter
                .form_initial_from_profile(presentation_profile)
            ),
        )
        context = super().get_context_data(
            form=form,
            form_data=form_data,
            **kwargs,
        )
        context['page_title'] = self.page_title
        context['submit_label'] = 'Сохранить изменения'
        return context

    def post(self, request, *args, **kwargs):
        form_data = self._form_data()
        form = self._form(
            data=request.POST,
            form_data=form_data,
            initial=(
                container
                .presentation_profile_form_adapter
                .form_initial_from_profile(form_data.presentation_profile)
            ),
        )
        if not form.is_valid():
            return self.render_to_response(
                self.get_context_data(form=form, form_data=form_data),
            )

        adapter = container.presentation_profile_form_adapter
        result = container.update_presentation_profile_use_case().execute(
            adapter.update_presentation_profile_params_from_form(
                form,
                presentation_profile_id=str(self.kwargs['pk']),
            )
        )
        if not result.success:
            if result.status == 'not_found':
                raise Http404('Профиль оформления не найден')
            for error in result.errors:
                form.add_error(None, error)
            return self.render_to_response(
                self.get_context_data(form=form, form_data=form_data),
            )

        messages.success(request, 'Профиль оформления обновлён.')
        return redirect('document_engine:print-profile-editor')
