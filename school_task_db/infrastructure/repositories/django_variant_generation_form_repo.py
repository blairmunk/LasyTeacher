"""Django read adapter for the work variant generation form."""

from core_logic.entities.work import (
    VariantGenerationGroupSource,
    VariantGenerationWork,
)
from core_logic.interfaces.variant_generation_form_repo import (
    IVariantGenerationFormRepository,
)
from task_groups.models import TaskGroup
from works.models import Work, WorkAnalogGroup


class DjangoVariantGenerationFormRepository(
    IVariantGenerationFormRepository,
):
    def get_work_generation_target(self, work_id: str):
        work = Work.objects.filter(pk=work_id).first()
        if work is None:
            return None

        return VariantGenerationWork(
            pk=str(work.pk),
            name=work.name,
            duration=work.duration,
            variant_counter=work.variant_counter,
            assessment_mode=work.assessment_mode,
        )

    def get_variant_generation_group_sources(self, work_id: str):
        return tuple(
            VariantGenerationGroupSource(
                group_name=work_group.analog_group.name,
                requested_count=work_group.count,
                bank_role_filter=work_group.bank_role_filter,
                task_bank_roles=self._task_bank_roles(
                    work_group.analog_group_id,
                ),
            )
            for work_group in WorkAnalogGroup.objects.filter(
                work_id=work_id,
            ).select_related(
                'analog_group',
            ).order_by('order', 'pk')
        )

    @staticmethod
    def _task_bank_roles(analog_group_id):
        return tuple(
            TaskGroup.objects.filter(
                group_id=analog_group_id,
            ).order_by('pk').values_list('bank_role', flat=True)
        )
