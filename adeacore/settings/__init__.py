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
if DEBUG_ENV == 'false':
    DEBUG = False
elif DEBUG_ENV == 'true':
    DEBUG = True
else:
    # Standard für lokale Entwicklung: DEBUG = True
    DEBUG = True

# Lade die richtige Settings-Datei
if DEBUG:
    from .local import *
else:
    from .production import *

