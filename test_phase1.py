"""
Test-Script für Phase 1: Verschlüsselung & Audit-Logging
"""

import os
import sys
import django

# Django Setup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adeacore.settings')
django.setup()

from adeacore.models import Client
from adeacore.encryption import get_encryption_manager
from adeacore.audit import get_audit_logger
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

print("=" * 70)
print("PHASE 1 TESTS: Verschlüsselung & Audit-Logging")
print("=" * 70)
print()

# Test 1: Verschlüsselung
print("TEST 1: Verschlüsselungs-Utility")
print("-" * 70)
try:
    manager = get_encryption_manager()
    test_value = "test@example.com"
    encrypted = manager.encrypt(test_value)
    decrypted = manager.decrypt(encrypted)
    
    assert decrypted == test_value, f"Verschlüsselung fehlgeschlagen: {decrypted} != {test_value}"
    assert encrypted != test_value, "Verschlüsselung hat nicht funktioniert"
    # Verschlüsselung ist base64-kodiert, sollte nicht mit Klartext übereinstimmen
    assert len(encrypted) > len(test_value), "Verschlüsselung zu kurz"
    
    print(f"[OK] Verschlusselung funktioniert")
    print(f"   Original: {test_value}")
    print(f"   Verschlüsselt: {encrypted[:50]}...")
    print(f"   Entschlüsselt: {decrypted}")
except Exception as e:
    print(f"[FEHLER] Verschlusselung fehlgeschlagen: {e}")
    sys.exit(1)

print()

# Test 2: Bestehende Daten lesen
print("TEST 2: Bestehende verschlüsselte Daten lesen")
print("-" * 70)
try:
    clients = Client.objects.all()[:3]
    if clients:
        for client in clients:
            print(f"[OK] Client '{client.name}':")
            print(f"   Email: {client.email[:30] if client.email else 'None'}...")
            print(f"   Phone: {client.phone[:30] if client.phone else 'None'}...")
            print(f"   MWST-Nr: {client.mwst_nr[:30] if client.mwst_nr else 'None'}...")
    else:
        print("[WARN] Keine Clients vorhanden")
except Exception as e:
    print(f"[FEHLER] Fehler beim Lesen: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 3: Neuen Client erstellen (verschlüsselt)
print("TEST 3: Neuen Client erstellen (sollte verschlüsselt werden)")
print("-" * 70)
try:
    # Erstelle Test-Client
    test_client = Client(
        name="Test Client Verschlüsselung",
        client_type="FIRMA",
        email="test.verschluesselung@example.com",
        phone="+41 79 123 45 67",
        mwst_nr="CHE-123.456.789",
        rechnungs_email="rechnung@example.com",
        street="Teststrasse",
        house_number="42",
        zipcode="8000",
        city="Zürich"
    )
    
    # Setze User für Audit-Log (optional)
    try:
        admin_user = User.objects.filter(is_superuser=True).first()
        if admin_user:
            test_client._current_user = admin_user
    except:
        pass
    
    test_client.save()
    
    # Lade wieder und prüfe Verschlüsselung
    loaded_client = Client.objects.get(pk=test_client.pk)
    
    # Prüfe ob Daten korrekt sind
    assert loaded_client.email == "test.verschluesselung@example.com", f"Email falsch: {loaded_client.email}"
    assert loaded_client.phone == "+41 79 123 45 67", f"Phone falsch: {loaded_client.phone}"
    assert loaded_client.mwst_nr == "CHE-123.456.789", f"MWST-Nr falsch: {loaded_client.mwst_nr}"
    
    print(f"[OK] Client erstellt: {loaded_client.name}")
    print(f"   Email: {loaded_client.email}")
    print(f"   Phone: {loaded_client.phone}")
    print(f"   MWST-Nr: {loaded_client.mwst_nr}")
    
    # Prüfe ob in DB verschlüsselt gespeichert
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT email, phone, mwst_nr FROM adeacore_client WHERE id = %s", [loaded_client.pk])
        row = cursor.fetchone()
        if row:
            db_email, db_phone, db_mwst = row
            # Prüfe ob verschlüsselt (base64-kodiert, sollte lang sein)
            if db_email and len(db_email) > 50 and db_email != loaded_client.email:
                print(f"   [OK] Email in DB verschlusselt")
            if db_phone and len(db_phone) > 50 and db_phone != loaded_client.phone:
                print(f"   [OK] Phone in DB verschlusselt")
            if db_mwst and len(db_mwst) > 50 and db_mwst != loaded_client.mwst_nr:
                print(f"   [OK] MWST-Nr in DB verschlusselt")
    
    # Lösche Test-Client
    test_client.delete()
    print(f"   [OK] Test-Client geloscht")
    
except Exception as e:
    print(f"[FEHLER] Fehler beim Erstellen: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 4: Client aktualisieren (Audit-Log)
print("TEST 4: Client aktualisieren (Audit-Log prüfen)")
print("-" * 70)
try:
    clients = Client.objects.all()[:1]
    if clients:
        client = clients[0]
        old_email = client.email
        
        # Setze User für Audit-Log
        try:
            admin_user = User.objects.filter(is_superuser=True).first()
            if admin_user:
                client._current_user = admin_user
        except:
            pass
        
        # Ändere Email
        client.email = "updated@example.com"
        client.save()
        
        # Prüfe Audit-Log
        audit_logger = get_audit_logger()
        logs = audit_logger.get_logs(model_name='Client', limit=5)
        
        if logs:
            latest_log = logs[0]
            if latest_log.get('action') == 'UPDATE' and latest_log.get('object_id') == client.pk:
                print(f"[OK] Audit-Log erstellt:")
                print(f"   Aktion: {latest_log.get('action')}")
                print(f"   Benutzer: {latest_log.get('user')}")
                print(f"   Objekt: {latest_log.get('object_repr')}")
                if latest_log.get('changes'):
                    print(f"   Anderungen: {latest_log.get('changes')}")
            else:
                print(f"[WARN] Audit-Log gefunden, aber nicht fur dieses Update")
        else:
            print(f"[WARN] Kein Audit-Log gefunden (moglicherweise User nicht gesetzt)")
        
        # Stelle alte Email wieder her
        client.email = old_email
        client.save()
        print(f"   [OK] Email wiederhergestellt")
    else:
        print("[WARN] Keine Clients vorhanden zum Testen")
except Exception as e:
    print(f"[FEHLER] Fehler beim Update: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 5: Audit-Log-Datei prüfen
print("TEST 5: Audit-Log-Datei prüfen")
print("-" * 70)
try:
    audit_logger = get_audit_logger()
    log_file = audit_logger.log_file
    
    if log_file.exists():
        print(f"[OK] Audit-Log-Datei existiert: {log_file}")
        
        # Zaehle Zeilen
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"   Anzahl Eintrage: {len(lines)}")
            
            # Zeige letzten Eintrag
            if lines:
                import json
                last_entry = json.loads(lines[-1])
                print(f"   Letzter Eintrag:")
                print(f"      Zeit: {last_entry.get('timestamp')}")
                print(f"      Aktion: {last_entry.get('action')}")
                print(f"      Model: {last_entry.get('model')}")
                print(f"      Benutzer: {last_entry.get('user')}")
    else:
        print(f"[WARN] Audit-Log-Datei existiert nicht: {log_file}")
except Exception as e:
    print(f"[FEHLER] Fehler beim Prufen der Log-Datei: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 6: Verschlüsselte Felder mit verschiedenen Werten
print("TEST 6: Verschlüsselte Felder mit verschiedenen Werten")
print("-" * 70)
try:
    manager = get_encryption_manager()
    
    test_cases = [
        ("email", "test@example.com"),
        ("phone", "+41 79 123 45 67"),
        ("mwst_nr", "CHE-123.456.789"),
        ("street", "Musterstrasse 42"),
        ("zipcode", "8000"),
        ("city", "Zürich"),
    ]
    
    all_passed = True
    for field_name, test_value in test_cases:
        encrypted = manager.encrypt(test_value)
        decrypted = manager.decrypt(encrypted)
        
        if decrypted == test_value:
            print(f"   [OK] {field_name}: OK")
        else:
            print(f"   [FEHLER] {field_name}: FEHLER ({decrypted} != {test_value})")
            all_passed = False
    
    if all_passed:
        print(f"[OK] Alle Feldtypen funktionieren korrekt")
    else:
        print(f"[FEHLER] Einige Feldtypen haben Fehler")
        
except Exception as e:
    print(f"[FEHLER] Fehler beim Testen der Felder: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
print("TESTS ABGESCHLOSSEN")
print("=" * 70)

