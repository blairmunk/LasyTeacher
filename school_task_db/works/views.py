from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from task_groups.models import AnalogGroup
from .models import Work, Variant, VariantTask, WorkAnalogGroup
from .forms import WorkForm, WorkAnalogGroupFormSet, VariantGenerationForm


class WorkListView(ListView):
    model = Work
    template_name = 'works/list.html'
    context_object_name = 'works'
    paginate_by = 20


class WorkDetailView(DetailView):
    model = Work
    template_name = 'works/detail.html'
    context_object_name = 'work'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['variants'] = Variant.objects.filter(work=self.object)
        context['analog_groups'] = WorkAnalogGroup.objects.filter(
            work=self.object
        ).select_related('analog_group').order_by('order', 'pk')
        context['spec_preview'] = self.object.get_spec_preview()

        has_variants = context['variants'].exists()
        has_groups = context['analog_groups'].exists()
        context['show_sync_button'] = has_variants and not has_groups
        return context


class WorkCreateView(CreateView):
    model = Work
    form_class = WorkForm
    template_name = 'works/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = WorkAnalogGroupFormSet(self.request.POST)
        else:
            context['formset'] = WorkAnalogGroupFormSet()
        context['analog_group_options'] = AnalogGroup.objects.all()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            response = super().form_valid(form)
            formset.instance = self.object
            formset.save()
            messages.success(self.request, 'Работа успешно создана!')
            return response
        else:
            return self.render_to_response(self.get_context_data(form=form))



class WorkUpdateView(UpdateView):
    model = Work
    form_class = WorkForm
    template_name = 'works/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = WorkAnalogGroupFormSet(
                self.request.POST, instance=self.object
            )
        else:
            context['formset'] = WorkAnalogGroupFormSet(instance=self.object)
        context['analog_group_options'] = AnalogGroup.objects.all()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            response = super().form_valid(form)
            formset.save()
            messages.success(self.request, 'Работа успешно обновлена!')
            return response
        else:
            return self.render_to_response(self.get_context_data(form=form))



def generate_variants(request, work_id):
    work = get_object_or_404(Work, pk=work_id)
    if request.method == 'POST':
        form = VariantGenerationForm(request.POST)
        if form.is_valid():
            count = form.cleaned_data['count']
            try:
                variants = work.generate_variants(count)
                messages.success(request, f'Успешно создано {len(variants)} вариантов!')
                return redirect('works:detail', pk=work.pk)
            except Exception as e:
                messages.error(request, f'Ошибка при создании вариантов: {str(e)}')
    else:
        form = VariantGenerationForm()
    return render(request, 'works/generate_variants.html', {
        'work': work, 'form': form,
    })


def sync_analog_groups(request, work_id):
    work = get_object_or_404(Work, pk=work_id)
    if request.method == 'POST':
        created = work.sync_analog_groups_from_variants()
        if created > 0:
            messages.success(request, f'Создано {created} групп заданий из вариантов.')
        else:
            messages.info(request, 'Группы заданий уже соответствуют вариантам.')
    return redirect('works:detail', pk=work.pk)


class VariantListView(ListView):
    model = Variant
    template_name = 'works/variant_list.html'
    context_object_name = 'variants'
    paginate_by = 20


class VariantDetailView(DetailView):
    model = Variant
    template_name = 'works/variant_detail.html'
    context_object_name = 'variant'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['variant_tasks'] = self.object.varianttask_set.select_related(
            'task', 'task__topic', 'task__subtopic'
        ).order_by('order')
        context['total_max_points'] = self.object.total_max_points
        return context

class OrphanVariantListView(ListView):
    """Варианты без привязки к работе (сироты)"""
    model = Variant
    template_name = 'works/orphan_variants.html'
    context_object_name = 'variants'
    paginate_by = 20

    def get_queryset(self):
        return Variant.objects.filter(work__isnull=True).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_orphans'] = Variant.objects.filter(work__isnull=True).count()
        return context

