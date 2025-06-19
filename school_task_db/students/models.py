from django.db import models
from django.urls import reverse
from core.models import BaseModel

class Student(BaseModel):
    """Ученик"""
    first_name = models.CharField('Имя', max_length=50)
    last_name = models.CharField('Фамилия', max_length=50)
    middle_name = models.CharField('Отчество', max_length=50, blank=True)
    email = models.EmailField('Email', blank=True)
    
    class Meta:
        verbose_name = 'Ученик'
        verbose_name_plural = 'Ученики'
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"[{self.get_short_uuid()}] {self.get_full_name()}"
    
    def get_absolute_url(self):
        return reverse('students:detail', kwargs={'pk': self.pk})
    
    def get_full_name(self):
        """Полное имя ученика"""
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return ' '.join(parts)
    
    def get_short_name(self):
        """Краткое имя (Фамилия И.О.)"""
        result = self.last_name
        if self.first_name:
            result += f" {self.first_name[0]}."
        if self.middle_name:
            result += f"{self.middle_name[0]}."
        return result

class StudentGroup(BaseModel):
    """Класс"""
    name = models.CharField('Название класса', max_length=10)
    students = models.ManyToManyField(Student, verbose_name='Ученики', blank=True)
    
    class Meta:
        verbose_name = 'Класс'
        verbose_name_plural = 'Классы'
        ordering = ['name']
    
    def __str__(self):
        return f"[{self.get_short_uuid()}] {self.name}"
    
    def get_absolute_url(self):
        return reverse('students:group-detail', kwargs={'pk': self.pk})
    
    def get_students_count(self):  # ДОБАВИТЬ ЭТОТ МЕТОД
        """Количество учеников в классе"""
        return self.students.count()
    
    def get_active_students(self):
        """Получить активных учеников класса"""
        return self.students.all().order_by('last_name', 'first_name')
    
    def get_grade_level(self):
        """Извлечь номер класса из названия"""
        try:
            return int(self.name[0]) if self.name and self.name[0].isdigit() else None
        except (ValueError, IndexError):
            return None
