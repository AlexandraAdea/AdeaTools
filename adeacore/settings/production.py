"""
Production Settings für AdeaTools (Render Deployment).
"""

from .base import *
import os
from django.core.exceptions import ImproperlyConfigured

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# ALLOWED_HOSTS - aus Environment-Variable oder hardcoded
ALLOWED_HOSTS_ENV = os.environ.get('DJANGO_ALLOWED_HOSTS', '')
if ALLOWED_HOSTS_ENV:
    ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_ENV.split(',') if host.strip()]
else:
    # Hardcoded Hosts für Render und Custom Domain
    ALLOWED_HOSTS = [
        'adeacore-web.onrender.com',
        'app.adea-treuhand.ch',
        'www.app.adea-treuhand.ch',
    ]

# Database - PostgreSQL für Render
try:
    import dj_database_url
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        DATABASES = {
            'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
        }
    else:
        raise ValueError("DATABASE_URL nicht gesetzt für Production!")
except ImportError:
    raise ImproperlyConfigured("dj-database-url benötigt für Production!")

# WhiteNoise Middleware für statische Dateien
try:
    import whitenoise
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
except ImportError:
    raise ImproperlyConfigured("WhiteNoise benötigt für Production!")

# Production Security Settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Logging - nur Console für Production (keine File-Handler)
# (Bereits in base.py konfiguriert)

