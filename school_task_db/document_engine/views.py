from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect
from django.views.generic import TemplateView

from infrastructure.container import container
from infrastructure.forms.print_settings_django_forms import (
    PrintSettingsForm,
)
from core_logic.use_cases.get_print_settings_form_data import (
    GetPrintSettingsFormDataRequest,
)
from core_logic.value_objects.document_recipes import WORK_DOCUMENT_TYPE


class PrintSettingsEditorView(TemplateView):
    template_name = 'document_engine/print_settings_editor.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        adapter = container.print_settings_form_adapter
        request = adapter.editor_data_request_from_query(self.request.GET)
        editor_data = (
            container
            .get_print_settings_editor_data_use_case()
            .execute(request)
        )
        context.update(adapter.editor_context(editor_data, request))
        return context


class PrintSettingsCreateView(TemplateView):
    template_name = 'document_engine/print_settings_form.html'
    page_title = 'Новые настройки печати'

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
            container.print_settings_form_adapter.create_context(
                form=form,
                document_types=form_data.document_types,
                sections=form_data.sections,
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

        result = container.create_print_settings_use_case().execute(
            container
            .print_settings_form_adapter
            .create_print_settings_params_from_form(form)
        )
        if not result.success:
            for error in result.errors:
                form.add_error(None, error)
            return self.render_to_response(
                self.get_context_data(form=form, form_data=form_data),
            )

        messages.success(request, 'Настройки печати созданы.')
        return redirect('document_engine:print-profile-editor')

    def _form(self, *args, form_data=None, **kwargs):
        form_data = form_data or self._form_data()
        return PrintSettingsForm(
            *args,
            document_types=form_data.document_types,
            sections=form_data.sections,
            **kwargs,
        )

    def _form_data(self, print_settings_id=''):
        return (
            container
            .get_print_settings_form_data_use_case()
            .execute(
                GetPrintSettingsFormDataRequest(
                    print_settings_id=print_settings_id,
                    renderable_only=True,
                ),
            )
        )


class PrintSettingsUpdateView(PrintSettingsCreateView):
    page_title = 'Редактирование настроек печати'

    def _form_data(self, print_settings_id=''):
        form_data = super()._form_data(
            print_settings_id or str(self.kwargs['pk']),
        )
        if form_data.print_profile is None:
            raise Http404('Настройки печати не найдены')
        return form_data

    def get_context_data(self, **kwargs):
        form_data = kwargs.pop('form_data', None) or self._form_data()
        print_profile = form_data.print_profile
        form = kwargs.get('form') or self._form(
            form_data=form_data,
            initial=(
                container
                .print_settings_form_adapter
                .form_initial_from_print_settings(print_profile)
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
        form = self._form(data=request.POST, form_data=form_data)
        if not form.is_valid():
            return self.render_to_response(
                self.get_context_data(form=form, form_data=form_data),
            )

        adapter = container.print_settings_form_adapter
        result = container.update_print_settings_use_case().execute(
            adapter.update_print_settings_params_from_form(
                form,
                print_settings_id=str(self.kwargs['pk']),
            )
        )
        if not result.success:
            if result.status == 'not_found':
                raise Http404('Настройки печати не найдены')
            for error in result.errors:
                form.add_error(None, error)
            return self.render_to_response(
                self.get_context_data(form=form, form_data=form_data),
            )

        messages.success(request, 'Настройки печати обновлены.')
        return redirect('document_engine:print-profile-editor')
