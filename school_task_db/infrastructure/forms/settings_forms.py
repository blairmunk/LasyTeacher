"""Infrastructure helpers for Django site settings forms."""

from core_logic.entities.site_settings import SaveSiteSettingsParams


class SettingsFormAdapter:
    def settings_form_initial(self, settings):
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

    def settings_params_from_form(self, form):
        logo = form.cleaned_data.get('logo')
        return SaveSiteSettingsParams(
            school_name=form.cleaned_data.get('school_name', ''),
            teacher_name=form.cleaned_data.get('teacher_name', ''),
            default_subject=form.cleaned_data.get('default_subject', ''),
            current_academic_year=form.cleaned_data.get(
                'current_academic_year',
                '',
            ),
            points_scale=form.cleaned_data['points_scale'],
            default_variants_count=form.cleaned_data['default_variants_count'],
            logo=None if logo is False else logo,
            clear_logo=logo is False,
            pdf_font_size=form.cleaned_data['pdf_font_size'],
            pdf_margin_top=form.cleaned_data['pdf_margin_top'],
            pdf_margin_bottom=form.cleaned_data['pdf_margin_bottom'],
        )
