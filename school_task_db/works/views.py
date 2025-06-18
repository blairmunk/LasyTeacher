from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from .models import Work, Variant, WorkAnalogGroup
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
        context['analog_groups'] = WorkAnalogGroup.objects.filter(work=self.object)
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

def generate_variants(request, work_id):
    """Генерация вариантов для работы"""
    work = get_object_or_404(Work, pk=work_id)
    
    if request.method == 'POST':
        form = VariantGenerationForm(request.POST)
        if form.is_valid():
            count = form.cleaned_data['count']
            try:
                variants = work.generate_variants(count)
                messages.success(
                    request, 
                    f'Успешно создано {len(variants)} вариантов!'
                )
                return redirect('works:detail', pk=work.pk)
            except Exception as e:
                messages.error(request, f'Ошибка при создании вариантов: {str(e)}')
    else:
        form = VariantGenerationForm()
    
    return render(request, 'works/generate_variants.html', {
        'work': work,
        'form': form
    })

class VariantListView(ListView):
    model = Variant
    template_name = 'works/variant_list.html'
    context_object_name = 'variants'
    paginate_by = 20

class VariantDetailView(DetailView):
    model = Variant
    template_name = 'works/variant_detail.html'
    context_object_name = 'variant'
