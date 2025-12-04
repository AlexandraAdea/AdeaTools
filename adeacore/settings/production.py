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
        '.adea-treuhand.ch',  # Wildcard für alle Subdomains
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

# Session Security (Swiss Banking Standard)
SESSION_COOKIE_AGE = 3600  # 1 Stunde (statt 2 Wochen Default)
SESSION_COOKIE_SAMESITE = 'Strict'  # Verhindert CSRF
SESSION_COOKIE_HTTPONLY = True  # Verhindert XSS
SESSION_SAVE_EVERY_REQUEST = True  # Erneuert Session bei jeder Anfrage
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Session endet beim Schließen

# HSTS (HTTP Strict Transport Security) - Swiss Standard
SECURE_HSTS_SECONDS = 31536000  # 1 Jahr
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Zusätzliche Security Headers
SECURE_REFERRER_POLICY = 'same-origin'
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Logging - nur Console für Production (keine File-Handler)
# (Bereits in base.py konfiguriert)

