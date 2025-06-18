from django import forms
from .models import Event, Mark

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'date', 'work', 'student_group', 'status']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class MarkForm(forms.ModelForm):
    class Meta:
        model = Mark
        fields = ['student', 'variant', 'event', 'score']

class StudentVariantAssignmentForm(forms.Form):
    """Форма для назначения вариантов ученикам"""
    def __init__(self, event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = event
        
        # Получаем всех учеников класса
        students = event.student_group.students.all()
        # Получаем все варианты работы
        from works.models import Variant
        variants = Variant.objects.filter(work=event.work)
        
        for student in students:
            field_name = f'student_{student.id}'
            # Проверяем, есть ли уже назначенный вариант
            existing_mark = Mark.objects.filter(
                student=student,
                event=event
            ).first()
            
            initial_variant = existing_mark.variant if existing_mark else None
            
            self.fields[field_name] = forms.ModelChoiceField(
                queryset=variants,
                label=student.get_full_name(),
                required=False,
                initial=initial_variant,
                widget=forms.Select(attrs={'class': 'form-control'})
            )
    
    def save(self):
        """Сохраняем назначения вариантов"""
        from students.models import Student
        for field_name, variant in self.cleaned_data.items():
            if field_name.startswith('student_') and variant:
                student_id = int(field_name.split('_')[1])
                student = Student.objects.get(pk=student_id)
                
                # Создаем или обновляем отметку
                mark, created = Mark.objects.get_or_create(
                    student=student,
                    event=self.event,
                    defaults={'variant': variant}
                )
                if not created:
                    mark.variant = variant
                    mark.save()
