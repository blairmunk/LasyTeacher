# Тестовая база

## Быстрый запуск

Из корня репозитория:

```bash
./scripts/create_test_database.sh
```

Сценарий последовательно:

1. применяет миграции;
2. загружает кодификаторы ОГЭ и ЕГЭ;
3. создаёт физические темы и связи с кодификаторами;
4. импортирует три класса по 15 учеников;
5. импортирует источники, группы аналогов и задания;
6. создаёт курсы, работы, варианты, события и результаты.
7. создаёт локального администратора `admin` с паролем `admin`.

Сценарий можно запускать повторно. Он обновляет банк заданий и пересобирает
только принадлежащие manifest-файлу курсы, работы, варианты и события.
Остальные пользовательские записи не удаляются.

Учётные данные тестового администратора можно переопределить:

```bash
TEST_ADMIN_USERNAME=teacher TEST_ADMIN_PASSWORD=local-password \
  ./scripts/create_test_database.sh
```

## Файлы данных

- `school_task_db/data/test_students_7_8_9.csv` — классы и ученики;
- `school_task_db/data/test_task_bank.json` — источники, группы и задания;
- `school_task_db/data/test_scenario.json` — учебный процесс поверх банка.

Можно передать собственные файлы:

```bash
./scripts/create_test_database.sh \
  /path/to/students.csv \
  /path/to/tasks.json \
  /path/to/scenario.json
```

Первым логично заменить `test_task_bank.json` реальной выжимкой из
сборников. UUID заданий и групп должны быть постоянными: тогда режим
`update` обновит записи, а не создаст дубликаты. Связь задания с группой
может хранить роль:

```json
{
  "groups": [
    {
      "id": "UUID-группы",
      "bank_role": "control"
    }
  ]
}
```

Поддерживаются роли `demo`, `practice`, `control` и `remedial`.

## Что покрывает сценарий

В тестовой базе есть:

- активный учебный год и настройки сайта;
- три класса и 45 учеников;
- кодификаторы, темы и подтемы;
- текст теории для секций документов;
- источники, задания и группы аналогов;
- роли заданий внутри групп;
- три курса и назначения работ в курсы;
- три работы с текстовыми, теоретическими и заданийными блоками;
- оцениваемые и демонстрационные строки спецификации;
- пустые клетки и разные режимы вывода решения;
- три иммутабельных варианта каждой работы;
- события `planned`, `in_progress`, `completed`, `reviewing`, `graded`;
- назначения вариантов, отсутствия и частично проверенные события;
- отметки, баллы по заданиям и `StudentTaskLog` для аналитики и РнО;
- один профиль оформления для проверки CSS и LaTeX-настроек.

Не создаются сканы работ и готовые remedial-варианты. Проверенное событие
`7А — итог по механике (проверено)` предназначено для ручной проверки
создания индивидуальных листов РнО штатным пользовательским маршрутом.

## Отдельные команды

Каждый этап можно выполнить вручную:

```bash
cd school_task_db
../venv/bin/python manage.py migrate
../venv/bin/python manage.py load_codifier_oge
../venv/bin/python manage.py load_codifier_ege
../venv/bin/python manage.py load_physics_topics
../venv/bin/python manage.py import_students_csv data/test_students_7_8_9.csv
../venv/bin/python manage.py import_tasks \
  data/test_task_bank.json \
  --mode update \
  --create-groups \
  --create-topics
../venv/bin/python manage.py build_test_scenario data/test_scenario.json
```

Проверка manifest без сохранения:

```bash
../venv/bin/python manage.py build_test_scenario \
  data/test_scenario.json \
  --dry-run
```
