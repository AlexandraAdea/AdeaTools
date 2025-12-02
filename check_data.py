#!/usr/bin/env python
"""Prüft die wiederhergestellten Daten."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adeacore.settings')
django.setup()

from adeacore.models import Client

clients = Client.objects.all()
print(f'Anzahl Mandanten: {clients.count()}')
print('\nErste 5 Mandanten:')
for c in clients[:5]:
    city = c.city[:30] if c.city else "(leer)"
    email = c.email[:30] if c.email else "(leer)"
    print(f'  - {c.name}: City={city}, Email={email}')




