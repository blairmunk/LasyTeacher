"""Infrastructure helpers for Django task group forms."""

from core_logic.use_cases.save_analog_group import SaveAnalogGroupRequest


class TaskGroupFormAdapter:
    def analog_group_params_from_form(self, form, group_id=''):
        return SaveAnalogGroupRequest(
            group_id=group_id,
            name=form.cleaned_data['name'],
            description=form.cleaned_data.get('description', ''),
        )

    def analog_group_form_initial(self, group):
        return {
            'name': group.name,
            'description': group.description,
        }
