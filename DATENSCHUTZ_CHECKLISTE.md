# ✅ Datenschutz-Checkliste für AdeaTools

**Für produktiven Einsatz mit Kundendaten**

---

## 🔴 KRITISCH (SOFORT)

### 1. Render Data Processing Agreement (DPA)

- [ ] Gehe zu https://render.com/dpa
- [ ] Akzeptiere das DPA
- [ ] Speichere Kopie für Unterlagen
- [ ] Dokumentiere: Datum, Version

**Warum:** Pflicht für Auftragsverarbeitung (Art. 28 DSGVO)

---

### 2. Datenschutzerklärung

- [ ] Verwende Muster (`DATENSCHUTZ_MUSTER.md`)
- [ ] Passe an (deine Adresse, Kontakt)
- [ ] Füge zur Webseite hinzu (Footer-Link)
- [ ] Auf Render deployen

**Warum:** Informationspflicht (Art. 13 DSGVO)

---

### 3. Impressum

- [ ] Erstelle Impressum mit:
  - Firmenname
  - Adresse
  - Kontakt (E-Mail, Telefon)
  - UID/Handelsregister
- [ ] Füge zur Webseite hinzu

**Warum:** Rechtliche Pflicht in CH/EU

---

## 🟡 WICHTIG (erste 3 Monate)

### 4. Verzeichnis der Verarbeitungstätigkeiten

- [ ] Dokumentiere alle Datenverarbeitungen
- [ ] Liste Zwecke, Kategorien, Speicherdauer
- [ ] Aktualisiere bei Änderungen

**Warum:** Pflicht ab 250 Mitarbeiter oder sensible Daten (Art. 30 DSGVO)

---

### 5. Technische & Organisatorische Maßnahmen (TOM)

- [ ] Dokumentiere alle Sicherheitsmaßnahmen:
  - ✅ Verschlüsselung (AES-256)
  - ✅ HTTPS
  - ✅ Zugriffskontrolle
  - ✅ Audit-Logging
  - ✅ Backups
  - ✅ Session-Security

**Warum:** Nachweis der Datensicherheit (Art. 32 DSGVO)

---

### 6. Datenschutz-Folgenabschätzung (DSFA)

- [ ] Risikoanalyse durchführen
- [ ] Bewerte Risiken für Betroffene
- [ ] Definiere zusätzliche Maßnahmen
- [ ] Dokumentiere Ergebnis

**Warum:** Pflicht bei hohem Risiko (Art. 35 DSGVO)

---

### 7. Betroffenenrechte implementieren

**Auskunftsrecht:**
- [ ] Funktion: "Meine Daten herunterladen"
- [ ] Export in JSON/PDF

**Löschrecht:**
- [ ] Funktion: "Konto löschen"
- [ ] Berücksichtige Aufbewahrungsfristen

**Datenportabilität:**
- [ ] Export in CSV/JSON

---

## 🟢 OPTIONAL (Best Practice)

### 8. Cookie-Banner

- [ ] Prüfe ob Tracking-Cookies verwendet werden
- [ ] Falls ja: Cookie-Banner implementieren
- [ ] Consent-Management

**AdeaTools:** Verwendet nur Session-Cookies (technisch notwendig) → Kein Banner nötig

---

### 9. Datenschutz-Management

- [ ] Datenschutzbeauftragter bestellen (ab 20 Personen)
- [ ] Regelmäßige Audits (jährlich)
- [ ] Mitarbeiter-Schulungen

---

## 📊 Aktueller Status

### ✅ Bereits implementiert:

1. Verschlüsselung sensibler Daten (Art. 32)
2. Zugriffskontrolle & Berechtigungen
3. Audit-Logging
4. Session-Security
5. Automatische Backups
6. HTTPS (auf Render)
7. EU-Hosting (Frankfurt)

### ❌ Fehlt noch:

1. 🔴 Render DPA abschließen
2. 🔴 Datenschutzerklärung
3. 🔴 Impressum
4. 🟡 Verzeichnis der Verarbeitungstätigkeiten
5. 🟡 TOM-Dokumentation
6. 🟡 DSFA
7. 🟡 Betroffenenrechte (Auskunft, Löschung)

---

## 🎯 Handlungsplan

### Diese Woche:

1. **Render DPA:** Abschließen und dokumentieren
2. **Datenschutzerklärung:** Anpassen und deployen
3. **Impressum:** Erstellen und deployen

### Dieser Monat:

4. **TOM-Dokumentation:** Sicherheitsmaßnahmen auflisten
5. **Verzeichnis:** Verarbeitungstätigkeiten dokumentieren

### Nächste 3 Monate:

6. **Betroffenenrechte:** Export-Funktion implementieren
7. **DSFA:** Risikoanalyse durchführen

---

## ⚠️ Rechtlicher Hinweis

**Ich bin kein Rechtsanwalt.**

Für verbindliche Rechtsberatung zu DSGVO/DSG 2023:
- Kontaktiere einen spezialisierten Anwalt
- Oder einen Datenschutzbeauftragten

Diese Checkliste ist eine technische Hilfestellung, keine Rechtsberatung.

---

**Bewertung Datenschutz: 7/10**
- Technisch gut
- Rechtlich: Dokumentation fehlt noch

