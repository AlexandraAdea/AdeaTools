# Rechnungsfunktion - Gesetzliche Anforderungen & Implementierung

## Gesetzliche Anforderungen für Rechnungen in der Schweiz (Stand 2025)

### Pflichtangaben (gemäß Art. 26 MWSTG):

1. **Name und Adresse des Leistungserbringers (Adea Treuhand):**
   - Vollständiger Name
   - Vollständige Adresse (Strasse, PLZ, Ort)
   - **MWST-Nummer (UID + "MWST")** - Seit 1.1.2014 Pflicht (z.B. "CHE-123.456.789 MWST")

2. **Name und Adresse des Leistungsempfängers (Client):**
   - Vollständiger Name
   - Vollständige Adresse (Strasse, PLZ, Ort)
   - MWST-Nummer (falls vorhanden)

3. **Datum oder Zeitraum der Leistung:**
   - Datum der Leistungserbringung (aus TimeEntry)

4. **Art, Gegenstand und Umfang der Leistung:**
   - Service-Typ (z.B. STEU, BUCH, BERA)
   - Kommentar/Beschreibung
   - Mitarbeiterin
   - Anzahl Stunden

5. **Entgelt:**
   - Nettobetrag (ohne MWST)
   - Anzahl/Einheit (Stunden)
   - Einzelpreis (Stundensatz)
   - Gesamtpreis pro Position

6. **Mehrwertsteuerbetrag oder gültiger Mehrwertsteuersatz:**
   - MWST-Satz (7.7% Standard, 2.5% reduziert, 3.7% Beherbergung)
   - MWST-Betrag
   - Bruttobetrag (Nettobetrag + MWST)

7. **Rechnungsdatum** (empfohlen, nicht zwingend Pflicht)

8. **Rechnungsnummer** (nicht zwingend Pflicht, aber organisatorisch sinnvoll)

### WICHTIG: QR-Rechnung (seit 1. Oktober 2022)

- **Nur noch QR-Rechnungen sind gültig** (traditionelle Einzahlungsscheine nicht mehr)
- QR-Code muss enthalten sein für Zahlungen
- Enthält: IBAN, Betrag, Referenz, Name, Adresse

### E-Rechnung (2025)

- **Keine allgemeine Pflicht** im B2B-Bereich
- Empfohlen: eBill-Integration (optional)
- Für Lieferanten des Bundes (>5'000 CHF/Jahr): E-Rechnungspflicht seit 2016

## Aktuelle Situation

### ✅ Vorhanden:
- Client-Model mit Adresse, MwSt-Nr, Zahlungsziel
- TimeEntry-Model mit allen notwendigen Daten
- Invoice-Model (basiert, aber nicht vollständig genutzt)
- Kundenübersicht mit Auswahl-Funktion

### ❌ Fehlt:
- Firmendaten-Model für Adea Treuhand (Name, Adresse, MwSt-Nr, IBAN)
- Rechnungsfunktion (Zeiteinträge → Rechnung)
- PDF-Generierung für Rechnungen
- Rechnungsnummern-Generierung
- MwSt-Berechnung
- Rechnungsansicht und -export

## Implementierungsplan

### Phase 1: Firmendaten-Model
- Model für Firmendaten erstellen (Singleton)
- Admin-Interface für Firmendaten
- Standardwerte setzen

### Phase 2: Rechnungsfunktion
- View für Rechnungserstellung aus Zeiteinträgen
- Rechnungsnummern-Generierung
- MwSt-Berechnung
- Verknüpfung TimeEntry → Invoice

### Phase 3: PDF-Generierung
- PDF-Template erstellen
- WeasyPrint oder ReportLab verwenden
- Alle gesetzlich erforderlichen Angaben

### Phase 4: Rechnungsansicht
- Rechnungsliste
- Rechnungsdetail-Ansicht
- PDF-Download
- Status-Verwaltung (Offen, Bezahlt, etc.)

## Empfehlung

Die aktuelle Kundenübersicht enthält bereits alle notwendigen Informationen für eine Rechnung. Wir sollten:

1. **Kurzfristig:** Eine einfache Rechnungsfunktion erstellen, die:
   - Ausgewählte Zeiteinträge in eine Rechnung umwandelt
   - Ein PDF generiert (mit allen gesetzlich erforderlichen Angaben)
   - Die verrechneten Einträge markiert

2. **Mittelfristig:** Ein vollständiges Rechnungsmodul mit:
   - Firmendaten-Verwaltung
   - Rechnungsnummern-Verwaltung
   - Zahlungsstatus-Tracking
   - Rechnungsarchiv

## Gesetzliche Compliance

Die vorgeschlagene Lösung erfüllt alle gesetzlichen Anforderungen:
- ✅ Alle Pflichtangaben vorhanden
- ✅ MwSt-Berechnung korrekt
- ✅ Rechnungsnummer eindeutig
- ✅ Vollständige Adressen
- ✅ Leistungsbeschreibung detailliert

**WICHTIGE Änderungen 2025:**
- **MWST-Nummer muss im Format "UID MWST" sein** (z.B. "CHE-123.456.789 MWST") - seit 1.1.2014 Pflicht
- **QR-Rechnung ist Pflicht** für Zahlungen (seit 1.10.2022) - traditionelle Einzahlungsscheine nicht mehr gültig
- **E-Rechnung**: Keine allgemeine Pflicht im B2B, aber empfohlen (eBill)

**Hinweis:** Für die MWST-Berechnung müssen wir prüfen, ob der Client mwst_pflichtig ist. Falls ja, wird 7.7% MWST berechnet (Standard in CH für Dienstleistungen). Die MWST-Nummer des Rechnungsstellers muss im Format "UID MWST" angegeben werden.

