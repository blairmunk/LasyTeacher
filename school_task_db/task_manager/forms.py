from django import forms
from django.forms import inlineformset_factory
from .models import (
    Task, TaskImage, AnalogGroup, Work, WorkAnalogGroup, Variant,
    Student, StudentGroup, Event, Mark
)


class TaskImageForm(forms.ModelForm):
    class Meta:
        model = TaskImage
        fields = ['image', 'position', 'caption', 'order']
        widgets = {
            'caption': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Подпись к изображению (необязательно)'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'position': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }


# Формсет для изображений задания
TaskImageFormSet = inlineformset_factory(
    Task, TaskImage, form=TaskImageForm, extra=1, can_delete=True
)


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = '__all__'
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4}),
            'answer': forms.Textarea(attrs={'rows': 3}),
            'short_solution': forms.Textarea(attrs={'rows': 3}),
            'full_solution': forms.Textarea(attrs={'rows': 5}),
            'hint': forms.Textarea(attrs={'rows': 2}),
            'instruction': forms.Textarea(attrs={'rows': 2}),
            'analog_groups': forms.CheckboxSelectMultiple(),
        }


class AnalogGroupForm(forms.ModelForm):
    class Meta:
        model = AnalogGroup
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class WorkForm(forms.ModelForm):
    class Meta:
        model = Work
        fields = ['name', 'duration']


class WorkAnalogGroupForm(forms.ModelForm):
    class Meta:
        model = WorkAnalogGroup
        fields = ['analog_group', 'count']


# Формсет для групп аналогов в работе
WorkAnalogGroupFormSet = inlineformset_factory(
    Work, WorkAnalogGroup, form=WorkAnalogGroupForm, extra=1, can_delete=True
)


class VariantGenerationForm(forms.Form):
    count = forms.IntegerField(
        label='Количество вариантов',
        min_value=1,
        max_value=50,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'middle_name', 'email']


class StudentGroupForm(forms.ModelForm):
    class Meta:
        model = StudentGroup
        fields = ['name', 'students']
        widgets = {
            'students': forms.CheckboxSelectMultiple(),
        }


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
