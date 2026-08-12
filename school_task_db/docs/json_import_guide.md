# Руководство по импорту заданий из JSON

Актуальный формат банка заданий — `1.4`. Задания и группы переносятся по UUID,
а классификации — по устойчивому естественному ключу кодификатора.

## 🚀 Быстрый старт

```bash
# Предварительный просмотр
python manage.py import_tasks tasks.json --dry-run --verbose

# Базовый импорт с созданием зависимостей
python manage.py import_tasks tasks.json --create-groups --create-topics

# Обновление существующих данных
python manage.py import_tasks tasks.json --mode update --verbose
```


## 📄 Формат JSON файла

### Минимальная структура:

```json
{
  "version": "1.4",
  "tasks": [
    {
      "id": "22222222-2222-2222-2222-222222222222",
      "text": "Решите уравнение: $x^2 - 5x + 6 = 0$",
      "answer": "$x_1 = 2, x_2 = 3$",
      "topic": {
        "name": "Квадратные уравнения",
        "subject": "Математика",
        "grade_level": 8
      }
    }
  ]
}
```

### Полная структура:

```json
{
  "version": "1.4",
  "description": "Импорт заданий по математике 8 класс",
  "topics": [
    {
      "name": "Квадратные уравнения",
      "subject": "Математика",
      "grade_level": 8,
      "section": "Алгебра",
      "description": "Решение квадратных уравнений различными способами",
      "order": 1
    }
  ],
  "analog_groups": [
    {
      "id": "11111111-1111-1111-1111-111111111111",
      "name": "Квадратные уравнения - базовый уровень",
      "description": "Простые квадратные уравнения с целыми коэффициентами"
    }
  ],
  "tasks": [
    {
      "id": "22222222-2222-2222-2222-222222222222",
      "text": "Решите уравнение: $x^2 - 5x + 6 = 0$",
      "answer": "$x_1 = 2, x_2 = 3$",
      "short_solution": "Используем формулу корней квадратного уравнения",
      "full_solution": "Дано: $x^2 - 5x + 6 = 0$\\n$a=1, b=-5, c=6$\\n...",
      "hint": "Попробуйте разложить на множители",
      "instruction": "Найдите все корни уравнения",
      "topic": {
        "name": "Квадратные уравнения",
        "subject": "Математика",
        "grade_level": 8
      },
      "subtopic": {
        "name": "Полные квадратные уравнения"
      },
      "codifier_content_entries": [
        {
          "subject": "Математика",
          "exam_type": "oge",
          "year": 2026,
          "code": "2.3.1"
        }
      ],
      "codifier_requirements": [
        {
          "subject": "Математика",
          "exam_type": "oge",
          "year": 2026,
          "code": "2.1.3"
        }
      ],
      "task_type": "computational",
      "difficulty": 3,
      "cognitive_level": "apply",
      "estimated_time": 5,
      "groups": [
        {
          "id": "11111111-1111-1111-1111-111111111111",
          "bank_role": "control"
        }
      ]
    }
  ],
  "task_images": [
    {
      "id": "33333333-3333-3333-3333-333333333333",
      "task_id": "22222222-2222-2222-2222-222222222222",
      "filename": "graph.png",
      "base64_data": "iVBORw0KGgoAAAANSUhEUgAA...",
      "position": "right_40",
      "caption": "График функции y = x² - 5x + 6",
      "order": 1
    }
  ]
}
```

## Классификация заданий

`codifier_content_entries` и `codifier_requirements` содержат ссылки на уже
импортированный кодификатор. Внутренние UUID записей кодификатора не
используются: они могут различаться в разных базах.

```json
{
  "subject": "Физика",
  "exam_type": "oge",
  "year": 2026,
  "code": "1.2.3"
}
```

При обновлении задания действуют следующие правила:

* поле отсутствует — существующие связи этого типа сохраняются;
* передан пустой массив `[]` — существующие связи очищаются;
* передан массив ссылок — связи заменяются найденными элементами.

Старые поля `content_element` и `requirement_element` всё ещё принимаются для
совместимости. Они сохраняют текст кода, но не создают однозначную связь с
конкретным кодификатором. Для старого банка после импорта используйте:

```bash
python manage.py backfill_task_classifications
python manage.py backfill_task_classifications --apply
```

## ⚙️ Параметры команды

### Основные параметры:

| Параметр    | Описание    | По умолчанию|
|-------------|:-----------:|------------:|
| json_file    | Путь к JSON файлу    | Обязательный    |
| --mode    | Режим обработки существующих UUID    | update    |
| --create-groups    | Создавать отсутствующие группы    | False    |
| --create-topics    | Создавать отсутствующие темы    | False    |
| --dry-run    | Предварительный просмотр    | False    |
| --verbose    | Подробный вывод    | False    |


### Режимы импорта:

* `strict`: Ошибка если UUID уже существует  
* `update`: Обновление существующих записей
* `skip`: Пропуск существующих записей

## 📊 Экспорт данных

```bash
# Экспорт всех заданий с группами и темами
python manage.py export_tasks all_tasks.json --include-groups --include-topics

# Экспорт по предмету
python manage.py export_tasks math_tasks.json --filter-subject "Математика" --include-groups

# Экспорт ограниченного количества
python manage.py export_tasks sample_tasks.json --limit 50 --verbose
```

## 🔍 Валидация файлов

```bash
# Проверка одного файла
python manage.py validate_json tasks.json --verbose

# Проверка множественных файлов
python manage.py validate_json *.json

#Результат валидации:
✅ Файл валиден 📊 Заданий: 25, групп: 5

```

## 🎯 Примеры использования

### Импорт новых данных:

```bash
python manage.py import_tasks new_tasks.json --create-groups --create-topics --verbose
```

### Обновление существующих:

```bash
python manage.py import_tasks updated_tasks.json --mode update --verbose
```

### Безопасный импорт (только новые):

```bash
python manage.py import_tasks tasks.json --mode skip --create-groups
```

### Round-trip тестирование:

```bash
# 1. Экспорт
python manage.py export_tasks exported.json --include-groups --include-topics

# 2. Валидация
python manage.py validate_json exported.json --verbose

# 3. Импорт обратно (должен пропустить все)
python manage.py import_tasks exported.json --mode skip --verbose
```

## 🖼️ Импорт изображений

### Base64 формат:
```json
{
  "task_images": [
    {
      "id": "img-uuid",
      "task_uuid": "task-uuid", 
      "base64_data": "data:image/png;base64,iVBORw0KGgo...",
      "filename": "image.png",
      "position": "right_40",
      "caption": "График функции"
    }
  ]
}
```

### Файловый импорт:
```bash
python manage.py import_tasks tasks.json --import-images --images-dir ./images/
```


## ❌ Типичные ошибки

### 1. Некорректный UUID:

```
❌ Задание 5: некорректный UUID 'invalid-uuid-format'
```

Решение: Используйте UUID формат или оставьте поле пустым для автогенерации.

### 2. Отсутствующие темы:

```
⚠️ Не удалось найти/создать тему для задания 2222
```

Решение: Добавьте --create-topics или включите темы в JSON.

### 3. Конфликт в strict режиме:

```
❌ Объект с UUID 2222 уже существует в strict режиме
```

Решение: Используйте режим update или skip.

## 📈 Оптимизация производительности

### Большие файлы:

* Используйте --verbose для отслеживания прогресса
* Разбивайте большие файлы на части по 1000-5000 заданий
* Импортируйте группы отдельно перед заданиями*

### Повторный импорт:

* Используйте режим skip для быстрого пропуска существующих
* Кэширование UUID работает в пределах одной команды

## 🛠️ Устранение проблем

### Отладка импорта:

```bash
# Подробный анализ зависимостей
python manage.py import_tasks tasks.json --dry-run --verbose
```

### Проверка отдельного файла

```bash
python manage.py validate_json tasks.json --verbose
```

### Логи ошибок:

Все ошибки сохраняются с контекстом для последующего анализа.

## 🎯 Результат импорта

```
📊 ИТОГИ ИМПОРТА: ✅ Создано: 25 ✏️ Обновлено: 5
⏭️ Пропущено: 0 ❌ Ошибок: 0 ⚠️ Предупреждений: 2 🎯 Успешность: 100.0%
```
