from django.db import models
from django.urls import reverse
from core.models import BaseModel

class Student(BaseModel):
    """Ученик"""
    first_name = models.CharField('Имя', max_length=100)
    last_name = models.CharField('Фамилия', max_length=100)
    middle_name = models.CharField('Отчество', max_length=100, blank=True)
    email = models.EmailField('Email', blank=True)
    
    class Meta:
        verbose_name = 'Ученик'
        verbose_name_plural = 'Ученики'
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.last_name} {self.first_name}"
    
    def get_full_name(self):
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return ' '.join(parts)

class StudentGroup(BaseModel):
    """Класс"""
    name = models.CharField('Название класса', max_length=100)
    students = models.ManyToManyField(Student, verbose_name='Ученики', blank=True)
    
    class Meta:
        verbose_name = 'Класс'
        verbose_name_plural = 'Классы'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('students:group-detail', kwargs={'pk': self.pk})
