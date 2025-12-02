# 📋 CRM-Erweiterungen für AdeaDesk

**Datum:** 2025-11-26  
**Status:** 📝 **Planungsphase**

---

## ✅ Aktuell vorhanden

### Grunddaten:
- ✅ Name, Typ (FIRMA/PRIVAT)
- ✅ Erstellungsdatum
- ✅ Interne Notizen

### Kontakt:
- ✅ E-Mail, Telefon
- ✅ Kontaktperson (für FIRMA)
- ✅ Adresse (Strasse, Hausnummer, PLZ, Ort)

### Geschäftsdaten:
- ✅ MWST-Nummer, MWST-pflichtig
- ✅ Rechnungs-E-Mail
- ✅ Zahlungsziel
- ✅ Steuerdaten (für PRIVAT)

### Integration:
- ✅ AdeaLohn-Modul
- ✅ Sachbearbeiter-Zuordnung

---

## 🎯 Wichtige CRM-Features (Priorität)

### 🔴 **HOCH - Für Treuhandbüro essentiell**

#### 1. **Status/Lebenszyklus**
- **Warum:** Unterscheidung zwischen aktiven, inaktiven, potenziellen Mandanten
- **Felder:**
  - Status: `AKTIV`, `INAKTIV`, `POTENZIELL`, `GESPERRT`
  - Status-Änderungsdatum
  - Grund für Inaktivität
- **Nutzen:** Übersicht über aktive Mandanten, Follow-up bei inaktiven

#### 2. **Kommunikationshistorie**
- **Warum:** Nachvollziehbarkeit aller Kontakte
- **Features:**
  - E-Mail-Verlauf (Datum, Betreff, Absender/Empfänger)
  - Anruf-Protokoll (Datum, Dauer, Thema)
  - Meeting-Notizen
  - Timeline-Ansicht
- **Nutzen:** Vollständige Historie, bessere Betreuung

#### 3. **Dokumente/Dateien**
- **Warum:** Zentrale Ablage für Verträge, Belege, Steuerdokumente
- **Features:**
  - Datei-Upload (PDF, Word, Excel)
  - Kategorien (Vertrag, Steuer, Rechnung, etc.)
  - Verschlüsselte Speicherung
  - Download-Link für Mandanten
- **Nutzen:** Alles an einem Ort, schneller Zugriff

#### 4. **Rechnungen/Finanzen**
- **Warum:** Übersicht über Rechnungen, Zahlungen, offene Posten
- **Features:**
  - Rechnungsnummer, Datum, Betrag
  - Zahlungsstatus (Offen, Teilweise bezahlt, Bezahlt, Überfällig)
  - Zahlungsdatum
  - Rechnungs-PDF anhängen
- **Nutzen:** Finanzübersicht, Mahnungen

#### 5. **Termine/Events**
- **Warum:** Wichtige Termine nicht vergessen (Steuerfristen, Meetings)
- **Features:**
  - Termin-Typ (Meeting, Frist, Erinnerung)
  - Datum, Uhrzeit
  - Erinnerung (E-Mail, Benachrichtigung)
  - Wiederkehrende Termine
- **Nutzen:** Keine Fristen verpassen, bessere Planung

---

### 🟡 **MITTEL - Nützlich für bessere Organisation**

#### 6. **Tags/Kategorien**
- **Warum:** Flexible Kategorisierung
- **Features:**
  - Mehrere Tags pro Mandant
  - Beispiele: `Steuerberatung`, `Lohnbuchhaltung`, `Jahresabschluss`, `Wichtig`
- **Nutzen:** Schnelle Filterung, Gruppierung

#### 7. **Branche/Sektor**
- **Warum:** Statistik, gezielte Betreuung
- **Felder:**
  - Branche (z.B. `IT`, `Handel`, `Dienstleistung`, `Gastronomie`)
  - Mitarbeiteranzahl
  - Gründungsdatum
  - Rechtsform (AG, GmbH, Einzelunternehmen, etc.)
- **Nutzen:** Branchenkenntnisse, Benchmarking

#### 8. **Mehrere Kontakte pro Firma**
- **Warum:** Verschiedene Ansprechpartner
- **Features:**
  - Kontakt-Modell (Name, E-Mail, Telefon, Rolle)
  - Primärer Kontakt markieren
  - Kontakt-Historie pro Person
- **Nutzen:** Richtige Person erreichen, bessere Kommunikation

#### 9. **Webseite/Social Media**
- **Warum:** Vollständiges Profil
- **Felder:**
  - Webseite
  - LinkedIn
  - Weitere Social Media
- **Nutzen:** Recherche, Marketing

#### 10. **Sprache**
- **Warum:** Mehrsprachige Kommunikation
- **Felder:**
  - Präferierte Sprache (DE, FR, IT, EN)
- **Nutzen:** Korrekte Ansprache, Übersetzungen

#### 11. **Bankverbindung**
- **Warum:** Für Rechnungen, Lohnzahlungen
- **Felder:**
  - IBAN
  - Bankname
  - Kontoinhaber
- **Nutzen:** Schnellere Zahlungen, weniger Fehler

#### 12. **Priorität/Wichtigkeit**
- **Warum:** Fokus auf wichtige Mandanten
- **Felder:**
  - Priorität: `HOCH`, `MITTEL`, `NIEDRIG`
  - Umsatz/Jahresbeitrag
- **Nutzen:** Ressourcen-Planung, Fokus

---

### 🟢 **NIEDRIG - Nice-to-have**

#### 13. **Import/Export**
- **Warum:** Daten-Migration, Backup
- **Features:**
  - CSV-Import
  - Excel-Export
  - Duplikat-Erkennung beim Import
- **Nutzen:** Schnelle Datenerfassung, Backup

#### 14. **Aktivitäts-Dashboard**
- **Warum:** Übersicht über alle Aktivitäten
- **Features:**
  - Letzte Kontakte
  - Offene Aufgaben
  - Überfällige Rechnungen
  - Kommende Termine
- **Nutzen:** Schneller Überblick, nichts vergessen

#### 15. **Notizen mit Zeitstempel**
- **Warum:** Chronologische Notizen
- **Features:**
  - Notizen mit Datum/Uhrzeit
  - Autor
  - Kategorien
- **Nutzen:** Vollständige Historie

#### 16. **Duplikat-Erkennung**
- **Warum:** Doppelte Einträge vermeiden
- **Features:**
  - Automatische Erkennung bei Erstellung
  - Vorschlag zum Zusammenführen
- **Nutzen:** Saubere Datenbank

---

## 🎨 UI/UX-Verbesserungen

### Dashboard:
- 📊 Statistiken (Anzahl Mandanten, Status-Verteilung)
- 📅 Kommende Termine
- 💰 Offene Rechnungen
- 📧 Letzte Kommunikationen

### Suche erweitern:
- 🔍 Suche in Notizen
- 🔍 Suche in Dokumenten
- 🔍 Suche nach Tags
- 🔍 Suche nach Status

### Listen-Ansicht:
- 📋 Spalten auswählbar
- 📋 Sortierung nach verschiedenen Feldern
- 📋 Bulk-Aktionen (Status ändern, Tags hinzufügen)

---

## 📊 Implementierungs-Priorität

### Phase 1 (Sofort):
1. ✅ Status/Lebenszyklus
2. ✅ Kommunikationshistorie (einfach)
3. ✅ Termine/Events
4. ✅ Rechnungen/Finanzen (Basis)

### Phase 2 (Kurzfristig):
5. ✅ Dokumente/Dateien
6. ✅ Tags/Kategorien
7. ✅ Branche/Sektor
8. ✅ Mehrere Kontakte

### Phase 3 (Mittelfristig):
9. ✅ Import/Export
10. ✅ Dashboard
11. ✅ Aktivitäts-Timeline
12. ✅ Bankverbindung

---

## 💡 Empfehlung für Treuhandbüro

**Für ein Treuhandbüro sind besonders wichtig:**

1. **Status** - Wer ist aktiv, wer nicht?
2. **Kommunikationshistorie** - Was wurde wann besprochen?
3. **Termine** - Steuerfristen, Meetings nicht vergessen
4. **Rechnungen** - Finanzübersicht, Mahnungen
5. **Dokumente** - Zentrale Ablage für Steuerdokumente

**Diese 5 Features sollten zuerst implementiert werden!**

---

## 🚀 Nächste Schritte

1. **Prioritäten festlegen** - Welche Features sind am wichtigsten?
2. **Datenmodell erweitern** - Neue Felder/Modelle hinzufügen
3. **UI anpassen** - Formulare und Listen erweitern
4. **Migration erstellen** - Datenbank-Schema aktualisieren

---

**Soll ich mit der Implementierung beginnen? Welche Features sind für Sie am wichtigsten?**




