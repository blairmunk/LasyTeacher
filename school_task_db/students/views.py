from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from .models import Student, StudentGroup
from .forms import StudentForm, StudentGroupForm

class StudentListView(ListView):
    model = Student
    template_name = 'students/list.html'
    context_object_name = 'students'
    paginate_by = 50

class StudentDetailView(DetailView):
    model = Student
    template_name = 'students/detail.html'
    context_object_name = 'student'

class StudentCreateView(CreateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/form.html'
    success_url = reverse_lazy('students:list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Ученик успешно добавлен!')
        return super().form_valid(form)

class StudentUpdateView(UpdateView):
    model = Student
    form_class = StudentForm
    template_name = 'students/form.html'
    success_url = reverse_lazy('students:list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Данные ученика обновлены!')
        return super().form_valid(form)

class StudentGroupListView(ListView):
    model = StudentGroup
    template_name = 'students/group_list.html'
    context_object_name = 'student_groups'

class StudentGroupDetailView(DetailView):
    model = StudentGroup
    template_name = 'students/group_detail.html'
    context_object_name = 'studentgroup'

class StudentGroupCreateView(CreateView):
    model = StudentGroup
    form_class = StudentGroupForm
    template_name = 'students/group_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Класс успешно создан!')
        return super().form_valid(form)

class StudentGroupUpdateView(UpdateView):
    model = StudentGroup
    form_class = StudentGroupForm
    template_name = 'students/group_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, 'Класс успешно обновлен!')
        return super().form_valid(form)

