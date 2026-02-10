"""
Production Settings für AdeaTools.
Funktioniert sowohl auf Render als auch auf Hetzner (Docker).
"""

from .base import *
import os
from django.core.exceptions import ImproperlyConfigured

# SECRET_KEY ist in Production Pflicht. Wir akzeptieren KEINEN Dev-Fallback.
_env_secret = os.environ.get("DJANGO_SECRET_KEY")
if not _env_secret:
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY muss in Production gesetzt sein! "
        "Bitte setze die Environment Variable."
    )
SECRET_KEY = _env_secret

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# ALLOWED_HOSTS - aus Environment-Variable (MUSS gesetzt sein)
# Beispiel: DJANGO_ALLOWED_HOSTS=app.adea-treuhand.ch,46.225.123.33
ALLOWED_HOSTS_ENV = os.environ.get('DJANGO_ALLOWED_HOSTS', '')
if ALLOWED_HOSTS_ENV:
    ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_ENV.split(',') if host.strip()]
    # localhost immer erlauben (für Health-Checks und interne Zugriffe)
    for local in ['localhost', '127.0.0.1']:
        if local not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(local)
else:
    import warnings
    warnings.warn(
        "DJANGO_ALLOWED_HOSTS nicht gesetzt - verwende Fallback-Liste. "
        "Bitte setze die Environment Variable für bessere Sicherheit!",
        UserWarning
    )
    ALLOWED_HOSTS = [
        'adeacore-web.onrender.com',
        'app.adea-treuhand.ch',
        'www.app.adea-treuhand.ch',
        'localhost',
        '127.0.0.1',
    ]

# Database - PostgreSQL
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
# SSL-Redirect per Environment steuerbar (deaktivieren wenn Nginx/Caddy SSL terminiert)
SECURE_SSL_REDIRECT = os.environ.get('DJANGO_SECURE_SSL_REDIRECT', 'true').lower() == 'true'
SESSION_COOKIE_SECURE = os.environ.get('DJANGO_SESSION_COOKIE_SECURE', 'true').lower() == 'true'
CSRF_COOKIE_SECURE = os.environ.get('DJANGO_CSRF_COOKIE_SECURE', 'true').lower() == 'true'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
PERMISSIONS_POLICY = 'geolocation=(), microphone=(), camera=()'

# Logging - nur Console für Production (keine File-Handler)
# (Bereits in base.py konfiguriert)

