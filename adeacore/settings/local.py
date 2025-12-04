"""
Lokale Development Settings für AdeaTools.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# ALLOWED_HOSTS für lokale Entwicklung + Custom Domains (falls auf Render geladen)
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'adeacore-web.onrender.com',
    'app.adea-treuhand.ch',
    'www.app.adea-treuhand.ch',
    '.adea-treuhand.ch',
]

# Database - SQLite für lokale Entwicklung
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Static files - Development
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Logging - File Handler für Development
import os
logs_dir = BASE_DIR / 'logs'
logs_dir.mkdir(exist_ok=True)

LOGGING['handlers']['file'] = {
    'class': 'logging.FileHandler',
    'filename': logs_dir / 'adealohn.log',
    'formatter': 'verbose',
}
LOGGING['loggers']['adealohn']['handlers'].append('file')
LOGGING['loggers']['adeacore']['handlers'].append('file')

# Keine Production Security Settings (für Development)

