from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib import messages

from core_logic.entities.site_settings import SaveSiteSettingsParams
from infrastructure.container import container
from .forms import SiteSettingsForm


class SiteSettingsView(TemplateView):
    template_name = 'site_settings/settings.html'

    def _get_settings(self):
        return container.get_site_settings_use_case().execute()

    def _form_initial(self, settings):
        return {
            'school_name': settings.school_name,
            'teacher_name': settings.teacher_name,
            'default_subject': settings.default_subject,
            'current_academic_year': settings.current_academic_year,
            'points_scale': settings.points_scale,
            'default_variants_count': settings.default_variants_count,
            'logo': settings.logo,
            'pdf_font_size': settings.pdf_font_size,
            'pdf_margin_top': settings.pdf_margin_top,
            'pdf_margin_bottom': settings.pdf_margin_bottom,
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        settings = kwargs.get('object') or self._get_settings()
        context['object'] = settings
        context['form'] = kwargs.get('form') or SiteSettingsForm(
            initial=self._form_initial(settings),
        )
        return context

    def post(self, request, *args, **kwargs):
        settings = self._get_settings()
        form = SiteSettingsForm(
            request.POST,
            request.FILES,
            initial=self._form_initial(settings),
        )
        if not form.is_valid():
            return self.render_to_response(
                self.get_context_data(form=form, object=settings),
            )

        logo = form.cleaned_data.get('logo')
        container.save_site_settings_use_case().execute(
            SaveSiteSettingsParams(
                school_name=form.cleaned_data.get('school_name', ''),
                teacher_name=form.cleaned_data.get('teacher_name', ''),
                default_subject=form.cleaned_data.get('default_subject', ''),
                current_academic_year=form.cleaned_data.get(
                    'current_academic_year',
                    '',
                ),
                points_scale=form.cleaned_data['points_scale'],
                default_variants_count=form.cleaned_data[
                    'default_variants_count'
                ],
                logo=None if logo is False else logo,
                clear_logo=logo is False,
                pdf_font_size=form.cleaned_data['pdf_font_size'],
                pdf_margin_top=form.cleaned_data['pdf_margin_top'],
                pdf_margin_bottom=form.cleaned_data['pdf_margin_bottom'],
            )
        )
        messages.success(request, 'Настройки сохранены!')
        return redirect('site_settings:index')
