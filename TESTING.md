# Тестовые срезы

Из каталога `school_task_db` тесты можно запускать именованными наборами:

```bash
python manage.py test_slice --list
python manage.py test_slice reports --keepdb
python manage.py test_slice documents --keepdb
```

По умолчанию команда печатает только краткий итог и ошибки. Для обычного или
подробного вывода добавьте `-v 1` или `-v 2`. `--failfast` останавливает прогон
после первой ошибки.

Доступные срезы:

- `clean` — все чистые use cases, сервисы и value objects;
- `reports` — отчёты, дайджесты, журнал, heatmap и snapshots попыток;
- `documents` — document engine, рецепты, секции, HTML/PDF/LaTeX;
- `works` — работы, варианты и спецификации;
- `students` — ученики и результаты заданий;
- `tasks` — банк заданий, группы, кодификаторы и импорт;
- `events` — события, проверка, remedial и snapshots;
- `infrastructure` — все Django-адаптеры;
- `web` — интеграционные тесты Django views;
- `all` — полный набор.

Срезы пересекаются намеренно. Для проверки конкретного файла или класса всё ещё
можно вызвать штатную команду Django напрямую:

```bash
python manage.py test core_logic.tests.test_student_digests --keepdb -v 0
python manage.py test reports.tests.ReportsViewsTests --keepdb -v 0
```

Перед завершением широкого изменения запускается `all`. Для локального изменения
сначала используется ближайший предметный срез.
