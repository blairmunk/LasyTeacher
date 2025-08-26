import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = 'django-insecure-замените-на-свой-ключ'
DEBUG = True
ALLOWED_HOSTS = []


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Внешние пакеты
    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks',
    
    # Приложения
    'core',           # Базовые компоненты
    'references',
    'tasks',          # Задания
    'task_groups',         # Группы аналогов
    'works',          # Работы и варианты
    'students',       # Ученики и классы
    'events',         # События
    'reports',        # Отчеты
    'curriculum',     # Учебные курсы
    'review',
    'document_generator',
    'latex_generator',
    'html_generator',      # HTML генератор
    'pdf_generator',       # PDF генератор
]

# Настройки для PDF генерации
PDF_GENERATOR_SETTINGS = {
    'DEFAULT_FORMAT': 'A4',
    'DEFAULT_MARGIN': {'top': '1cm', 'right': '1cm', 'bottom': '1cm', 'left': '1cm'},
    'PRINT_BACKGROUND': True,
    'WAIT_FOR_MATHJAX': True,
    'FAST_MODE': False,  # НОВОЕ: быстрый режим без ожидания MathJax
    'MATHJAX_SCRIPT_TIMEOUT': 5000,   # 5 сек на загрузку скрипта  
    'MATHJAX_RENDER_TIMEOUT': 8000,   # 8 сек на рендеринг формул
    'OUTPUT_DIR': 'pdf_output',
}


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'school_task_db.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],  #  путь к шаблонам
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            BASE_DIR / 'latex_generator' / 'templates',  # НОВЫЙ ПУТЬ
            # BASE_DIR / 'works' / 'latex' / 'templates',  # СТАРЫЙ - можно пока оставить
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]



WSGI_APPLICATION = 'school_task_db.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True


STATIC_URL = '/static/'
STATICFILES_DIRS = [            # ДОБАВЛЯЕМ
    BASE_DIR / "static",
]

# Для разработки также добавить:
STATIC_ROOT = BASE_DIR / 'staticfiles'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# настройки Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Media files (загрузки пользователей)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# Максимальный размер загружаемых файлов (10MB)
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# Настройки кеша redis
#CACHES = {
#    'default': {
#        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#        'LOCATION': 'redis://127.0.0.1:6379/1',
#        'KEY_PREFIX': 'school_math_dev',
#        'VERSION': 1,
#    }
#}

# Настройки кеша локально
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# Или для отладки можно временно отключить кэш:
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
#     }
# }