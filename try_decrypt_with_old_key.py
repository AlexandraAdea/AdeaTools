#!/usr/bin/env python
"""Versucht, die verschlüsselten Daten mit verschiedenen Keys zu entschlüsseln."""
import os
import django
import base64
from cryptography.fernet import Fernet

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adeacore.settings')
django.setup()

from adeacore.models import Client

# Verschlüsselte Daten aus Backup
encrypted_city = "Z0FBQUFBQnBKd1NPZjliOEhlREpBcHpZZmc1bmpySzh0OGlzSkRBanA5TzZobjZXZGFqdzExZE9EQVdIQXI5ZWlSU0ZMN3pZWU9GT0U4eXk3bUE2OERZeEl3eWtKY3R0SDN6dEl"

# Versuche mit aktuellem Key
print("=== Versuch 1: Aktueller Key aus .env ===")
try:
    from dotenv import load_dotenv
    load_dotenv()
    current_key = os.environ.get('ADEATOOLS_ENCRYPTION_KEY')
    if current_key:
        cipher = Fernet(current_key.encode('utf-8'))
        decrypted = cipher.decrypt(base64.b64decode(encrypted_city))
        print(f"✅ ERFOLG! Entschlüsselt: {decrypted.decode('utf-8')}")
    else:
        print("❌ Kein Key in .env gefunden")
except Exception as e:
    print(f"❌ Fehler: {e}")

# Prüfe ob es einen alten Key gibt
print("\n=== Versuch 2: Suche nach altem Key ===")
possible_key_locations = [
    '.env.backup',
    '.env.old',
    'config/master.key',
    'data/encryption.key',
]

for key_path in possible_key_locations:
    if os.path.exists(key_path):
        print(f"  Gefunden: {key_path}")
        try:
            with open(key_path, 'rb') as f:
                key = f.read()
            if len(key) == 44:  # Fernet key length
                cipher = Fernet(key)
                decrypted = cipher.decrypt(base64.b64decode(encrypted_city))
                print(f"  ✅ ERFOLG mit {key_path}!")
                print(f"  Entschlüsselt: {decrypted.decode('utf-8')}")
                break
        except Exception as e:
            print(f"  ❌ Fehler mit {key_path}: {e}")

# Prüfe Environment-Variablen
print("\n=== Versuch 3: Environment-Variablen ===")
for env_var in ['ADEATOOLS_ENCRYPTION_KEY', 'ENCRYPTION_KEY', 'FERNET_KEY']:
    key = os.environ.get(env_var)
    if key:
        print(f"  Gefunden: {env_var}")
        try:
            cipher = Fernet(key.encode('utf-8') if isinstance(key, str) else key)
            decrypted = cipher.decrypt(base64.b64decode(encrypted_city))
            print(f"  ✅ ERFOLG mit {env_var}!")
            print(f"  Entschlüsselt: {decrypted.decode('utf-8')}")
            break
        except Exception as e:
            print(f"  ❌ Fehler: {e}")

print("\n=== Fazit ===")
print("Wenn kein Key gefunden wurde, sind die Daten ohne den ursprünglichen Key nicht entschlüsselbar.")
print("Das ist das Prinzip der Verschlüsselung - ohne den Key sind die Daten sicher verschlüsselt.")



