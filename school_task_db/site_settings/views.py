from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import SiteSettings
from .forms import SiteSettingsForm


class SiteSettingsView(UpdateView):
    model = SiteSettings
    form_class = SiteSettingsForm
    template_name = 'site_settings/settings.html'
    success_url = reverse_lazy('site_settings:index')

    def get_object(self, queryset=None):
        return SiteSettings.get()

    def form_valid(self, form):
        messages.success(self.request, 'Настройки сохранены!')
        return super().form_valid(form)
