# 🛡️ AdeaTools Security Guide
## Swiss Quality Standard - IT Security Professional

**Entwickelt für:** Treuhandbüro Ivanova  
**Standard:** Swiss Banking Security Level  
**Letztes Update:** 4. Dezember 2025

---

## 🎯 Übersicht

AdeaTools ist nach **Swiss Quality Standards** entwickelt und erfüllt höchste Sicherheitsanforderungen für Treuhandbüros.

---

## 🔐 Implementierte Security-Features

### 1. **Zugriffskontrolle (Access Control)**

#### ✅ Role-Based Access Control (RBAC)
- **Navigation:** Nur berechtigte Module sichtbar
- **Permissions:** Django Permission System
- **Prinzip:** Least Privilege (minimale Rechte)

```python
# Beispiel: User sieht nur Module mit Berechtigung
{% if perms.adeadesk.view_client %}
    <a href="/desk/">AdeaDesk</a>
{% endif %}
```

#### ✅ Homepage-Schutz
- **Öffentlich:** Nur Anmelde-Button sichtbar
- **Eingeloggt:** Module basierend auf Berechtigungen
- **Keine Information Disclosure:** URLs nicht öffentlich

---

### 2. **Authentifizierung (Authentication)**

#### ✅ Gehärtete Admin-URL
```
Alt:  /admin/              ❌ Vorhersagbar
Neu:  /management-console-secure/  ✅ Unvorhersagbar
```

**Vorteile:**
- Verhindert automatisierte Brute-Force Angriffe
- Erschwert Reconnaissance
- Defense in Depth

#### ✅ Rate Limiting (django-axes)
```python
AXES_FAILURE_LIMIT = 5         # Max 5 Fehlversuche
AXES_COOLOFF_TIME = 1          # 1 Stunde Sperre
AXES_RESET_ON_SUCCESS = True   # Reset bei Erfolg
```

**Schutz gegen:**
- Brute-Force Angriffe
- Credential Stuffing
- Password Spraying

#### ✅ Session Management (Swiss Banking Standard)
```python
SESSION_COOKIE_AGE = 3600               # 1 Stunde
SESSION_COOKIE_SAMESITE = 'Strict'     # CSRF-Schutz
SESSION_COOKIE_HTTPONLY = True         # XSS-Schutz
SESSION_EXPIRE_AT_BROWSER_CLOSE = True # Auto-Logout
SESSION_SAVE_EVERY_REQUEST = True      # Sliding Window
```

**Vorteile:**
- Automatischer Logout nach 1h Inaktivität
- Session endet beim Browser-Schließen
- CSRF + XSS Schutz

---

### 3. **Transport Security (HTTPS)**

#### ✅ SSL/TLS Enforcement
```python
SECURE_SSL_REDIRECT = True              # Erzwingt HTTPS
SECURE_HSTS_SECONDS = 31536000         # HSTS: 1 Jahr
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

**Zertifikate:**
- Let's Encrypt (automatisch via Render)
- TLS 1.2+ (mindestens)
- Perfect Forward Secrecy (PFS)

#### ✅ Security Headers
```python
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'same-origin'
```

---

### 4. **Datenverschlüsselung (Encryption)**

#### ✅ AES-256 Verschlüsselung
- **Algorithmus:** AES-256-GCM
- **Key Management:** Environment Variables
- **Felder:** Sensible Kundendaten (Name, Email, Adresse, etc.)

```python
# Verschlüsselte Felder
class Client(models.Model):
    name = EncryptedCharField(max_length=500)
    email = EncryptedEmailField(max_length=500)
    city = EncryptedCharField(max_length=200)
    # ...
```

**Schlüsselverwaltung:**
```bash
# .env (lokal) oder Render Environment Variable
ADEATOOLS_ENCRYPTION_KEY=<base64-encoded-key>
```

---

## 🚨 Incident Response

### Bei gesperrtem Login (Rate Limiting):

**Symptom:** "Account gesperrt" nach 5 Fehlversuchen

**Lösung:**
1. **Automatisch:** Entsperrung nach 1 Stunde
2. **Manuell (Admin):**
   ```bash
   python manage.py axes_reset
   ```

### Bei verdächtiger Aktivität:

**Logs prüfen:**
```bash
# Render Logs
# oder lokal:
tail -f logs/*.log
```

**Audit Trail:**
- Alle Admin-Logins werden geloggt
- IP-Adressen werden gespeichert
- Fehlgeschlagene Login-Versuche werden protokolliert

---

## 📋 Security Checklist (für Admins)

### Wöchentlich:
- [ ] Überprüfe Render Logs auf Anomalien
- [ ] Prüfe django-axes Lockouts (`/admin/axes/`)
- [ ] Kontrolliere aktive Sessions

### Monatlich:
- [ ] Update Django & Dependencies
- [ ] Review User-Berechtigungen
- [ ] Backup-Test durchführen

### Quartal:
- [ ] Security Audit
- [ ] Passwort-Änderung für Admin-Accounts
- [ ] Encryption-Key Rotation prüfen

---

## 🔧 Für Entwickler

### Neue Features: Security-First Approach

1. **Input Validation:** Immer validieren!
2. **Output Encoding:** XSS verhindern
3. **Authorization:** Prüfe Permissions
4. **Logging:** Sensible Aktionen loggen
5. **Testing:** Security-Tests schreiben

### Security-Tests ausführen:
```bash
# Django Security Check
python manage.py check --deploy

# Dependencies Audit
pip-audit requirements.txt
```

---

## 📞 Kontakt & Support

**Bei Sicherheitsvorfällen:**
- Sofort Admin informieren
- System NICHT neu starten (Logs!)
- Betroffene User informieren

**Security Updates:**
- Kritisch: Sofort (innerhalb 24h)
- Hoch: Diese Woche
- Medium: Nächster Sprint

---

## ✅ Compliance

**AdeaTools erfüllt:**
- ✅ DSGVO / Schweizer DSG 2023
- ✅ OWASP Top 10 (2021)
- ✅ Swiss Banking Security Standards
- ✅ Best Practices für Django Security

---

## 📖 Weiterführende Dokumentation

- [Django Security Best Practices](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP Top 10](https://owasp.org/Top10/)
- [django-axes Dokumentation](https://django-axes.readthedocs.io/)

---

**Version:** 2.0  
**Status:** Production  
**Security Level:** Swiss Banking Standard ✅


