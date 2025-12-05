"""
Django Settings - Lädt je nach Environment die richtige Konfiguration.

Lokal (DEBUG=True): settings.local
Production (DEBUG=False): settings.production
"""

import os
from pathlib import Path

# WICHTIG: .env MUSS VOR allen anderen Imports geladen werden!
# Sonst verwendet EncryptionManager den falschen Schlüssel
try:
    from dotenv import load_dotenv
    # Expliziter Pfad zur .env
    env_path = Path(__file__).resolve().parent.parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

# Prüfe ob Production-Modus
DEBUG_ENV = os.environ.get('DJANGO_DEBUG', '').lower()
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:  # If DATABASE_URL is set, assume production
    DEBUG = False
    IS_PRODUCTION = True
elif DEBUG_ENV == 'false':
    DEBUG = False
    IS_PRODUCTION = True
elif DEBUG_ENV == 'true':
    DEBUG = True
    IS_PRODUCTION = False
else:
    # Standard für lokale Entwicklung: DEBUG = True
    DEBUG = True
    IS_PRODUCTION = False

# Lade base.py zuerst für SECRET_KEY
from .base import SECRET_KEY

# SECRET_KEY: Fallback nur für lokale Entwicklung, Production MUSS Environment Variable haben
if not SECRET_KEY:
    if IS_PRODUCTION:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured("DJANGO_SECRET_KEY muss in Production gesetzt sein! Bitte setze die Environment Variable auf Render.")
    else:
        # Fallback nur für lokale Entwicklung
        import hashlib
        SECRET_KEY = 'django-insecure-dev-key-change-in-production-' + hashlib.md5(__file__.encode()).hexdigest()[:20]

# Lade die richtige Settings-Datei
if DEBUG:
    from .local import *
else:
    from .production import *

