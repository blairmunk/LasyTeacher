from django import forms
from django.forms import inlineformset_factory
from .models import Event, EventParticipation, Mark
from students.models import Student, StudentGroup
from works.models import Variant

class EventForm(forms.ModelForm):
    """Форма для создания события"""
    class Meta:
        model = Event
        fields = [
            'name', 'work', 'planned_date', 'status', 'course', 
            'description', 'location'
        ]  # ОБНОВЛЕННЫЕ ПОЛЯ
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'work': forms.Select(attrs={'class': 'form-select'}),
            'planned_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
        }

class EventParticipationForm(forms.ModelForm):
    """Форма для участия в событии"""
    class Meta:
        model = EventParticipation
        fields = ['student', 'variant', 'status', 'seat_number']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'variant': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'seat_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

# Формсет для участников события
EventParticipationFormSet = inlineformset_factory(
    Event, EventParticipation, form=EventParticipationForm, 
    extra=1, can_delete=True
)

class StudentSelectionForm(forms.Form):
    """Форма для выбора учеников для события"""
    student_group = forms.ModelChoiceField(
        queryset=StudentGroup.objects.all(),
        required=False,
        label='Выбрать весь класс',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    individual_students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.all(),
        required=False,
        label='Или выбрать отдельных учеников',
        widget=forms.CheckboxSelectMultiple()
    )
    
    def clean(self):
        cleaned_data = super().clean()
        student_group = cleaned_data.get('student_group')
        individual_students = cleaned_data.get('individual_students')
        
        if not student_group and not individual_students:
            raise forms.ValidationError('Необходимо выбрать либо класс, либо отдельных учеников')
        
        return cleaned_data

class MarkForm(forms.ModelForm):
    """Форма для оценивания работы"""
    class Meta:
        model = Mark
        fields = [
            'score', 'points', 'max_points', 'teacher_comment', 
            'mistakes_analysis', 'recommendations', 'work_scan',
            'is_retake', 'is_excellent', 'needs_attention'
        ]
        widgets = {
            'score': forms.Select(choices=[(i, i) for i in range(1, 6)], attrs={'class': 'form-select'}),
            'points': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'max_points': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'teacher_comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'mistakes_analysis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'recommendations': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'work_scan': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
            'is_retake': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_excellent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'needs_attention': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class VariantAssignmentForm(forms.Form):
    """Форма для назначения вариантов участникам"""
    def __init__(self, event, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Получаем участников события
        participations = EventParticipation.objects.filter(event=event)
        variants = Variant.objects.filter(work=event.work)
        
        for participation in participations:
            field_name = f'variant_{participation.id}'
            self.fields[field_name] = forms.ModelChoiceField(
                queryset=variants,
                required=False,
                label=participation.student.get_full_name(),
                initial=participation.variant,
                widget=forms.Select(attrs={'class': 'form-select'})
            )

class QuickMarkForm(forms.Form):
    """Быстрая форма для простановки оценок"""
    score = forms.ChoiceField(
        choices=[(i, i) for i in range(1, 6)],
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    comment = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Краткий комментарий'})
    )
