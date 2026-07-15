"""Infrastructure helpers for Django work forms."""

from works.forms import WorkAnalogGroupFormSet


class WorkFormAdapter:
    def build_analog_group_formset(self, data=None, instance=None):
        if data is not None:
            return WorkAnalogGroupFormSet(data, instance=instance)
        return WorkAnalogGroupFormSet(instance=instance)

    def save_analog_group_formset(self, formset, work):
        formset.instance = work
        formset.save()
