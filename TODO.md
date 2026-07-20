# TODO: Задачи для будущего развития

## 🎨 HIGH PRIORITY: CSS стили для HTML/PDF генерации

### Проблема:
Текущие CSS стили секционного HTML/PDF renderer требуют **полной переработки**:

- ❌ **Печать side-by-side**: изображения "right_20/right_40" не позиционируются корректно при печати
- ❌ **BEM методология нарушена**: классы не следуют строгой BEM структуре  
- ❌ **Responsive поведение**: требует улучшения для мобильных устройств
- ❌ **Типографика**: межстрочные интервалы, размеры шрифтов не оптимизированы

### Требуемые изменения:

1. **Переработать CSS архитектуру**:
   ```scss
   // Строгая BEM структура
   .task-with-image_layout_horizontal
   .task-with-image_image-size_20
   .task-with-image__text
   .task-with-image__image

2. **Исправить печать side-by-side:**

    * Использовать CSS Grid или улучшенный flexbox
    * Тестирование в Chrome/Firefox/Safari печать
    * Поддержка различных размеров бумаги (A4/A3/Letter)
    
    
3. **Типографические улучшения:**
        
    * Правильные межстрочные интервалы для формул
    * Размеры шрифтов для печати vs экрана
    * Поля и отступы оптимизировать

### Файлы для изменения:

    `school_task_db/infrastructure/services/sectioned_document_templates.py` - HTML/CSS шаблоны секционного renderer
    `school_task_db/infrastructure/services/django_document_section_payloads.py` - payload-структуры секций
    `school_task_db/infrastructure/services/template_document_section_renderer.py` - рендеринг отдельных секций

### Приоритет: *HIGH* (после завершения основной функциональности)


## 🚀 MEDIUM PRIORITY: Другие улучшения

### PDF генерация:

* Прогресс-бары для длительных операций
* Параллельная обработка множественных файлов
* Watermarks и headers/footers

### Web интерфейс:

* Кнопки генерации PDF в веб-интерфейсе
* Ajax генерация с индикаторами прогресса
* Настройки генерации через форму
