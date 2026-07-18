from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib import messages
from .models import SiteSettings
from .forms import SiteSettingsForm


class SiteSettingsView(TemplateView):
    template_name = 'site_settings/settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        settings = kwargs.get('object') or SiteSettings.get()
        context['object'] = settings
        context['form'] = kwargs.get('form') or SiteSettingsForm(instance=settings)
        return context

    def post(self, request, *args, **kwargs):
        settings = SiteSettings.get()
        form = SiteSettingsForm(
            request.POST,
            request.FILES,
            instance=settings,
        )
        if not form.is_valid():
            return self.render_to_response(
                self.get_context_data(form=form, object=settings),
            )

        form.save()
        messages.success(request, 'Настройки сохранены!')
        return redirect('site_settings:index')
