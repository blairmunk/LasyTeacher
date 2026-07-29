# LasyTeacher

Локальное Django-приложение для подготовки учебных работ, проверки
результатов и анализа успеваемости.

## Запуск

```bash
python -m venv venv
venv/bin/pip install -r school_task_db/requirements.txt
venv/bin/playwright install chromium
cd school_task_db
../venv/bin/python manage.py migrate
../venv/bin/python manage.py runserver
```

После установки приложение, HTML-документы и PDF-рендерер не требуют
подключения к интернету: Bootstrap, Font Awesome, MathJax и Plotly хранятся
в `school_task_db/static/vendor/`.

Для production-развёртывания перед запуском необходимо собрать статику:

```bash
cd school_task_db
../venv/bin/python manage.py collectstatic --noinput
```
