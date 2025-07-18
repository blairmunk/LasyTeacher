from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import path
from django.shortcuts import render
from django.contrib import messages
from .generators.registry import registry
from works.models import Work

class LaTeXGeneratorAdmin:
    """Админка для управления LaTeX генераторами"""
    
    def __init__(self, admin_site):
        self.admin_site = admin_site
    
    def get_urls(self):
        urls = [
            path('latex-generator/', self.admin_site.admin_view(self.generate_view), name='latex_generator_generate'),
        ]
        return urls
    
    def generate_view(self, request):
        """Представление для генерации документов"""
        if request.method == 'POST':
            doc_type = request.POST.get('type')
            object_id = request.POST.get('object_id')
            output_format = request.POST.get('format', 'pdf')
            with_answers = request.POST.get('with_answers') == 'on'
            
            try:
                generator_class = registry.get_generator(doc_type)
                
                if doc_type == 'work':
                    work = Work.objects.get(pk=object_id)
                    generator = generator_class(output_dir='latex_output')
                    
                    if with_answers:
                        files = generator.generate_with_answers(work, output_format)
                    else:
                        files = generator.generate(work, output_format)
                    
                    messages.success(request, f'Документ создан: {", ".join(files)}')
                
            except Exception as e:
                messages.error(request, f'Ошибка генерации: {e}')
            
            return HttpResponseRedirect(request.path)
        
        # GET запрос - показываем форму
        context = {
            'title': 'Генерация LaTeX документов',
            'available_generators': registry.get_available_types(),
            'works': Work.objects.all()[:10],  # Показываем первые 10 работ
        }
        
        return render(request, 'admin/latex_generator/generate.html', context)

# ВРЕМЕННО УБИРАЕМ РЕГИСТРАЦИЮ АДМИНКИ
# admin.site.register(LaTeXGeneratorProxy, LaTeXGeneratorAdmin)
