#!/usr/bin/env python
"""Prüft Backups auf verschlüsselte/unverschlüsselte Daten."""
import sqlite3
from pathlib import Path

backup_db = Path('backups/auto_20251126_145026_test/database/db.sqlite3')

if backup_db.exists():
    conn = sqlite3.connect(str(backup_db))
    cursor = conn.cursor()
    
    # Prüfe Furrer Networks
    cursor.execute('SELECT name, city, email, phone, street, zipcode FROM adeacore_client WHERE name="Furrer Networks"')
    row = cursor.fetchone()
    
    if row:
        print('=== FURRER NETWORKS - Daten aus Backup ===')
        print(f'Name: {row[0]}')
        print(f'\nCity:')
        print(f'  Wert: {row[1][:100] if row[1] else "(leer)"}...')
        print(f'  Länge: {len(row[1]) if row[1] else 0}')
        print(f'  Startet mit Z0FBQUFBQnBK: {row[1].startswith("Z0FBQUFBQnBK") if row[1] else False}')
        
        print(f'\nEmail:')
        print(f'  Wert: {row[2][:100] if row[2] else "(leer)"}...')
        print(f'  Länge: {len(row[2]) if row[2] else 0}')
        
        print(f'\nPhone:')
        print(f'  Wert: {row[3][:100] if row[3] else "(leer)"}...')
        
        print(f'\nStreet:')
        print(f'  Wert: {row[4][:100] if row[4] else "(leer)"}...')
        
        print(f'\nZipcode:')
        print(f'  Wert: {row[5][:100] if row[5] else "(leer)"}...')
        
        # Prüfe ob es verschlüsselt aussieht
        encrypted_pattern = 'Z0FBQUFBQnBK'
        is_encrypted = any(field and field.startswith(encrypted_pattern) for field in row[1:])
        print(f'\n=== STATUS ===')
        print(f'Daten sind verschlüsselt: {is_encrypted}')
        print(f'Verschlüsselungsformat: Fernet (Base64)')
    
    conn.close()
else:
    print(f'Backup nicht gefunden: {backup_db}')




