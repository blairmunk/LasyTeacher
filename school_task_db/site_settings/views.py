from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib import messages

from infrastructure.container import container
from infrastructure.forms.site_settings_django_forms import SiteSettingsForm


class SiteSettingsView(TemplateView):
    template_name = 'site_settings/settings.html'

    def _get_settings(self):
        return container.get_site_settings_use_case().execute()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        settings = kwargs.get('object') or self._get_settings()
        form = kwargs.get('form') or SiteSettingsForm(
            initial=container.settings_form_adapter.settings_form_initial(settings),
        )
        context.update(container.settings_form_adapter.settings_context(settings, form))
        return context

    def post(self, request, *args, **kwargs):
        settings = self._get_settings()
        form = SiteSettingsForm(
            request.POST,
            request.FILES,
            initial=container.settings_form_adapter.settings_form_initial(settings),
        )
        if not form.is_valid():
            return self.render_to_response(
                self.get_context_data(form=form, object=settings),
            )

        container.save_site_settings_use_case().execute(
            container.settings_form_adapter.settings_params_from_form(form),
        )
        messages.success(request, 'Настройки сохранены!')
        return redirect('site_settings:index')
