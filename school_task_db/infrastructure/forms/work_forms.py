"""Infrastructure helpers for Django work forms."""

from core_logic.interfaces.work_repo import (
    CreateWorkAnalogGroupParams,
    CreateWorkParams,
)
from works.forms import WorkAnalogGroupFormSet
from works.models import Work


class WorkFormAdapter:
    def _get_work_instance(self, work_id=None):
        if not work_id:
            return None
        return Work.objects.filter(pk=work_id).first()

    def build_analog_group_formset(self, data=None, instance=None, work_id=None):
        if instance is None:
            instance = self._get_work_instance(work_id)
        if data is not None:
            return WorkAnalogGroupFormSet(data, instance=instance)
        return WorkAnalogGroupFormSet(instance=instance)

    def work_params_from_form(self, form, work_id=''):
        return CreateWorkParams(
            work_id=work_id,
            name=form.cleaned_data['name'],
            work_type=form.cleaned_data.get('work_type', 'test'),
            duration=form.cleaned_data.get('duration') or 45,
            max_score=form.cleaned_data.get('max_score') or 0,
        )

    def work_form_initial(self, work):
        return {
            'name': work.name,
            'work_type': work.work_type,
            'duration': work.duration,
            'max_score': work.max_score,
        }

    def work_specs_from_formset(self, formset, work_id):
        specs = []
        for row in formset.cleaned_data:
            if not row or row.get('DELETE'):
                continue

            analog_group = row.get('analog_group')
            if not analog_group:
                continue

            specs.append(
                CreateWorkAnalogGroupParams(
                    work_id=work_id,
                    analog_group_id=str(analog_group.pk),
                    order=row.get('order') or 0,
                    count=row.get('count') or 1,
                    weight=row.get('weight') or 1,
                )
            )
        return specs
