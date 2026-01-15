"""
Gemeinsame Django Settings für alle Umgebungen.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# Dev-Fallback: In lokaler Entwicklung brauchen Tests/Message-Cookies einen SECRET_KEY.
# Production erzwingt DJANGO_SECRET_KEY zusätzlich in settings/production.py.
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY') or None
if not SECRET_KEY:
    import hashlib
    SECRET_KEY = 'django-insecure-dev-key-change-in-production-' + hashlib.md5(
        __file__.encode()
    ).hexdigest()[:20]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'adeacore.apps.AdeacoreConfig',
    # AdeaTools Module
    'adeadesk',
    'adeazeit',
    'adearechnung',  # Fakturierung und Rechnungserstellung (Vertec-Stil)
    'adealohn',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'adeacore.middleware.SessionSecurityMiddleware',  # Session-Sicherheit
]

ROOT_URLCONF = 'adeacore.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'adeacore' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'adeacore.context_processors.current_client',
                'adeacore.context_processors.adeazeit_permissions',
                'adeacore.context_processors.adealohn_permissions',
                'adeacore.context_processors.running_timer',
            ],
        },
    },
]

WSGI_APPLICATION = 'adeacore.wsgi.application'

# Password validation
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

# Internationalization
LANGUAGE_CODE = 'de-ch'
TIME_ZONE = 'Europe/Zurich'
USE_I18N = True
USE_TZ = True

# Authentication
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Static files directory (für collectstatic)
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Session Security (Swiss Banking Standard)
# Session-Timeout: 2 Stunden für produktive Arbeit (Vertec-Analog)
# Wird automatisch verlängert durch Heartbeat während aktiver Eingabe
SESSION_COOKIE_AGE = 7200  # 2 Stunden (angepasst für längere Eingaben)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True  # Verlängert Session bei jedem Request
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'  # Strenger als 'Lax' für besseren CSRF-Schutz
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

# Logging Configuration (Basis)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'adealohn': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'adeacore': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

