# 🔐 Daten-Wiederherstellung - IT-Analyse

**Datum:** 2025-11-26  
**Status:** ⚠️ **Kritisch - Daten verschlüsselt ohne verfügbaren Key**

---

## 🔍 Problem-Analyse

### Situation:
- ✅ **11 Mandanten** sind in der Datenbank vorhanden
- ❌ **Verschlüsselte Felder** (E-Mail, Telefon, Ort, etc.) können nicht entschlüsselt werden
- ❌ **Encryption-Key** ist nicht mehr verfügbar

### Technische Details:
- **Verschlüsselungsmethode:** Fernet (AES-128 CBC + HMAC)
- **Format:** Base64-kodiert
- **Verschlüsselte Felder:** E-Mail, Telefon, Strasse, PLZ, Ort, MWST-Nr, etc.
- **Key-Status:** Nicht verfügbar (wurde bei jedem Neustart neu generiert)

---

## 💡 Lösungsmöglichkeiten

### Option 1: Daten manuell neu eingeben ✅ **EMPFOHLEN**
**Vorteile:**
- Funktioniert sofort
- Daten sind aktuell
- Verschlüsselung funktioniert dann korrekt

**Nachteile:**
- Zeitaufwand
- Manche Daten könnten verloren sein

**Schritte:**
1. Öffnen Sie http://127.0.0.1:8000/desk/
2. Bearbeiten Sie jeden Mandanten
3. Geben Sie die verschlüsselten Daten neu ein

---

### Option 2: Backup vor Verschlüsselung finden 🔍
**Falls verfügbar:**
- Prüfen Sie, ob es ein Backup gibt, das **VOR** der Verschlüsselung erstellt wurde
- Prüfen Sie andere Systeme/Computer, wo die Daten vielleicht unverschlüsselt vorhanden sind

**Wo suchen:**
- Ältere Backups (vor 2025-11-26)
- Andere Computer/Systeme
- E-Mail-Archiv
- Papier-Dokumente

---

### Option 3: Daten aus anderen Quellen importieren 📥
**Mögliche Quellen:**
- Excel-Export
- CSV-Dateien
- E-Mail-Korrespondenz
- Rechnungen/Belege
- Andere Systeme (z.B. alte Zeiterfassung)

---

## ⚠️ Warum können die Daten nicht entschlüsselt werden?

**Das ist das Prinzip der Verschlüsselung:**
- Verschlüsselung ist **sicher** - ohne den Key sind die Daten **nicht entschlüsselbar**
- Der ursprüngliche Encryption-Key wurde nicht gespeichert
- Bei jedem Neustart wurde ein neuer Key generiert
- Ohne den ursprünglichen Key sind die Daten **sicher verschlüsselt** (aber für uns nicht lesbar)

**Das ist KEIN Fehler, sondern das gewünschte Verhalten:**
- Verschlüsselung schützt die Daten vor unbefugtem Zugriff
- Ohne den Key können auch Angreifer die Daten nicht lesen

---

## 🔧 Technische Lösung (für IT-Profis)

### Wenn der alte Key gefunden wird:
1. Setze `ADEATOOLS_ENCRYPTION_KEY` in `.env` auf den alten Key
2. Daten werden automatisch entschlüsselt angezeigt
3. Dann: Migriere zu neuem Key (Daten neu speichern)

### Migration zu neuem Key:
1. Alten Key setzen
2. Alle Daten laden (werden entschlüsselt)
3. Neuen Key setzen
4. Alle Daten neu speichern (werden mit neuem Key verschlüsselt)

---

## 📋 Nächste Schritte

1. **Sofort:** Prüfen Sie, ob Sie die Daten aus anderen Quellen haben
2. **Kurzfristig:** Daten manuell neu eingeben
3. **Langfristig:** 
   - Encryption-Key immer in `.env` speichern
   - Regelmäßige Backups mit Key-Sicherung
   - Key-Backup an sicherer Stelle aufbewahren

---

## ✅ Prävention für die Zukunft

1. **Encryption-Key immer sichern:**
   ```bash
   # Key aus .env kopieren und sicher aufbewahren
   # z.B. in Passwort-Manager, verschlüsseltes Archiv, etc.
   ```

2. **Backup-Strategie:**
   - Regelmäßige Backups (täglich)
   - Key-Backup separat sichern
   - Backups testen (Restore testen)

3. **Dokumentation:**
   - Key-Speicherort dokumentieren
   - Backup-Prozess dokumentieren

---

**Status:** ⚠️ Daten verschlüsselt - manuelle Eingabe erforderlich oder Backup vor Verschlüsselung finden



