"""
Gemeinsame Django Settings für alle Umgebungen.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-2sq0xh0_=kcvx63ib^=2_&2_zf+$*vjr+mfn62h@cxb2^$+qw!')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Security: Rate Limiting & Brute-Force Protection
    'axes',  # django-axes MUSS nach django.contrib.auth sein!
    'adeacore.apps.AdeacoreConfig',
    # AdeaTools Module
    'adeadesk',
    'adeazeit',
    'adealohn',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # Security: Rate Limiting Middleware (nach Auth!)
    'axes.middleware.AxesMiddleware',  # django-axes
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

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

# Session Security
SESSION_COOKIE_AGE = 86400  # 24 Stunden
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

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

# ===================================================
# django-axes: Brute-Force Protection (Swiss Banking Standard)
# ===================================================

# Authentication Backend (mit axes)
AUTHENTICATION_BACKENDS = [
    # AxesStandaloneBackend sollte VOR ModelBackend sein
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# axes Configuration
AXES_FAILURE_LIMIT = 5  # Max 5 Fehlversuche
AXES_COOLOFF_TIME = 1  # 1 Stunde Sperre (in Stunden)
AXES_LOCKOUT_TEMPLATE = None  # Nutze Default 403-Seite
AXES_RESET_ON_SUCCESS = True  # Reset Counter bei erfolgreichem Login
AXES_VERBOSE = True  # Logging aktiviert
AXES_LOCK_OUT_BY_COMBINATION_USER_AND_IP = True  # Lock by User+IP (sicherer)
AXES_ONLY_ADMIN_SITE = False  # Schütze ALLE Login-Seiten
AXES_ENABLED = True  # Aktiviert in Production

