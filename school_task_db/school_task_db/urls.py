from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),          # Главная страница
    path('tasks/', include('tasks.urls')),    # Задания
    path('task_groups/', include('task_groups.urls')),  # Группы аналогичных заданий
    path('works/', include('works.urls')),    # Работы
    path('students/', include('students.urls')),  # Ученики
    path('events/', include('events.urls')),  # События
    path('reports/', include('reports.urls')), # Отчеты
    path('curriculum/', include('curriculum.urls')), # Учебные курсы
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
