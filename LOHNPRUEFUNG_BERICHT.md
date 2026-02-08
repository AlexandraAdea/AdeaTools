# Prüfbericht: Lohnabrechnung und Lohnberechnung
## Prüfung nach HR- und Sozialversicherungsstandards

**Datum:** {{ aktuelles_datum }}  
**Prüfer:** Automatisierte Code-Prüfung  
**Geprüftes Modul:** AdeaLohn (AdeaTools)

---

## 1. EXECUTIVE SUMMARY

### ✅ Stärken
- **Rundungen korrekt:** Alle Sozialversicherungsbeiträge werden auf 5 Rappen gerundet (AHV, ALV, UVG, BVG, KTG, QST)
- **YTD-Logik implementiert:** Jahr-zu-Datum Berechnungen für ALV, UVG, BVG mit korrekter Kappung
- **Rentnerfreibetrag:** AHV-Freibetrag für Rentner korrekt implementiert
- **Basis-Berechnung:** Korrekte Berechnung der Basen aus PayrollItems mit Rundung auf 2 Dezimalstellen
- **Validierung:** Umfassende Validierung in `clean()` Methode

### ⚠️ Kritische Punkte (MUSS behoben werden)

1. **Code-Duplikat in `recompute_bases_from_items()`**
   - **Problem:** Zeilen 690-691 und 695-703 setzen `_manual_bvg_employee` und `_manual_bvg_employer` doppelt
   - **Risiko:** Inkonsistente Berechnungen, schwer nachvollziehbar
   - **Priorität:** HOCH
   - **Datei:** `adeacore/models.py`, Zeilen 677-703

2. **Fehlende Dokumentation auf Lohnabrechnung**
   - **Problem:** Lohnabrechnung zeigt nicht alle erforderlichen Informationen für Prüfer
   - **Fehlt:**
     - AHV-Nummer des Mitarbeiters
     - Geburtsdatum
     - Eintrittsdatum
     - Arbeitskanton (für FAK)
     - BVG-Koordinationsabzug explizit
     - BVG-Korridore (Min/Max versicherter Lohn)
   - **Priorität:** MITTEL
   - **Datei:** `adealohn/templates/adealohn/payroll/print.html`

3. **BVG-Basis in Druckansicht**
   - **Problem:** Druckansicht zeigt `bvg_basis` statt `bvg_insured_month` für BVG-Berechnung
   - **Risiko:** Prüfer sehen falsche Basis (sollte versicherter Lohn des Monats sein)
   - **Priorität:** HOCH
   - **Datei:** `adealohn/templates/adealohn/payroll/print.html`, Zeile 290

### ⚠️ Verbesserungspotenzial

4. **QST-Berechnung nicht vollständig dokumentiert**
   - **Problem:** QST-Basis wird nicht explizit auf Lohnabrechnung gezeigt
   - **Empfehlung:** QST-Basis und Tarif sollten sichtbar sein
   - **Priorität:** NIEDRIG

5. **Fehlende Prüfsummen**
   - **Problem:** Keine automatische Prüfsumme für Prüfer (z.B. Summe aller Basen = Bruttolohn)
   - **Empfehlung:** Prüfsummen-Sektion hinzufügen
   - **Priorität:** NIEDRIG

---

## 2. DETAILLIERTE PRÜFUNG

### 2.1 Rundungen (✅ KORREKT)

**Geprüft:**
- ✅ AHV: `round_to_5_rappen()` verwendet
- ✅ ALV: `round_to_5_rappen()` verwendet
- ✅ UVG: `round_to_5_rappen()` verwendet
- ✅ BVG: `round_to_5_rappen()` verwendet
- ✅ KTG: `round_to_5_rappen()` verwendet
- ✅ QST: `round_to_5_rappen()` verwendet
- ✅ Basen: Rundung auf 2 Dezimalstellen mit `ROUND_HALF_UP`

**Bewertung:** ✅ Entspricht Schweizer Standards (5 Rappen für Beiträge, 2 Dezimalstellen für Basen)

### 2.2 AHV-Berechnung (✅ KORREKT)

**Geprüft:**
- ✅ Rentnerfreibetrag: 1'400 CHF/Monat korrekt angewendet
- ✅ Effective Basis: Korrekt berechnet (`basis - rentner_freibetrag`)
- ✅ Beitragssatz: 5.3% (konfigurierbar über AHVParameter)
- ✅ Rundung: Auf 5 Rappen

**Bewertung:** ✅ Entspricht AHV-Gesetz

### 2.3 ALV-Berechnung (✅ KORREKT)

**Geprüft:**
- ✅ YTD-Kappung: Korrekt bei 148'200 CHF/Jahr
- ✅ Rentner: Keine ALV für Rentner
- ✅ Effective Basis: Korrekt berechnet mit YTD-Logik
- ✅ Beitragssatz: 1.1% (konfigurierbar über ALVParameter)
- ✅ Rundung: Auf 5 Rappen

**Bewertung:** ✅ Entspricht ALV-Gesetz

### 2.4 UVG-Berechnung (✅ KORREKT)

**Geprüft:**
- ✅ YTD-Kappung: Korrekt bei 148'200 CHF/Jahr
- ✅ BU: Nur Arbeitgeberbeitrag
- ✅ NBU: Nur Arbeitnehmerbeitrag (bei >8h/Woche)
- ✅ Effective Basis: Korrekt berechnet mit YTD-Logik
- ✅ Rundung: Auf 5 Rappen

**Bewertung:** ✅ Entspricht UVG-Gesetz

### 2.5 BVG-Berechnung (⚠️ TEILWEISE PROBLEMATISCH)

**Geprüft:**
- ✅ Eintrittsschwelle: Korrekt geprüft
- ✅ Koordinationsabzug: Korrekt angewendet
- ✅ Korridore: Min/Max versicherter Lohn korrekt angewendet
- ✅ YTD-Logik: Korrekt für versicherten Lohn
- ✅ Manuelle Beiträge: Korrekt addiert (BVG_AN, BVG_AG)
- ⚠️ **PROBLEM:** Druckansicht zeigt `bvg_basis` statt `bvg_insured_month`
- ⚠️ **PROBLEM:** BVG-Koordinationsabzug nicht explizit auf Lohnabrechnung

**Bewertung:** ⚠️ Berechnung korrekt, Dokumentation unvollständig

### 2.6 QST-Berechnung (✅ KORREKT)

**Geprüft:**
- ✅ QST-Pflicht: Korrekt geprüft
- ✅ Fixbetrag: Hat Vorrang
- ✅ Prozentsatz: Fallback auf Prozentsatz
- ✅ Tarif: QSTParameter mit effektivem Tarif
- ✅ Basis: qst_basis verwendet (ALV-Basis - AN-Sozialabzüge)
- ✅ Rundung: Auf 5 Rappen
- ⚠️ **VERBESSERUNG:** QST-Basis sollte auf Lohnabrechnung sichtbar sein

**Bewertung:** ✅ Berechnung korrekt, Dokumentation verbesserungswürdig

### 2.7 Netto-Lohn Berechnung (✅ KORREKT)

**Geprüft:**
- ✅ Abzüge: AHV, ALV, NBU, KTG, BVG, QST korrekt abgezogen
- ✅ Familienzulagen: Korrekt addiert
- ✅ Rundung: Auf 5 Rappen für Auszahlung

**Bewertung:** ✅ Korrekt

### 2.8 YTD-Reset (✅ KORREKT)

**Geprüft:**
- ✅ Januar-Reset: Korrekt implementiert
- ✅ Race Condition: `select_for_update()` verwendet
- ✅ Doppel-Reset-Schutz: Prüfung auf bereits zurückgesetzte Werte
- ✅ Felder: ALV, UVG, BVG YTD-Basen werden zurückgesetzt

**Bewertung:** ✅ Korrekt implementiert

### 2.9 Validierung (✅ KORREKT)

**Geprüft:**
- ✅ Monat: 1-12 validiert
- ✅ Jahr: 2000-2100 validiert
- ✅ Duplikate: Unique-Together Constraint
- ✅ Client-Typ: Nur FIRMA-Clients erlaubt
- ✅ Full Clean: Wird vor save() aufgerufen

**Bewertung:** ✅ Umfassende Validierung

---

## 3. FEHLENDE INFORMATIONEN AUF LOHNABRECHNUNG

### 3.1 Pflichtfelder (für Sozialversicherungsprüfer)

**Fehlt auf Druckansicht:**
1. ❌ AHV-Nummer des Mitarbeiters
2. ❌ Geburtsdatum
3. ❌ Eintrittsdatum
4. ❌ Arbeitskanton (für FAK-Berechnung)
5. ❌ BVG-Koordinationsabzug (explizit)
6. ❌ BVG-Korridore (Min/Max versicherter Lohn)
7. ❌ QST-Basis (explizit)
8. ❌ QST-Tarif (vollständig)

### 3.2 Empfohlene Ergänzungen

**Für HR-Profis:**
- ✅ Mitarbeiter-Nr. (bereits vorhanden, wenn gesetzt)
- ✅ Periode (bereits vorhanden)
- ✅ Datum (bereits vorhanden)
- ⚠️ Arbeitszeit (Stunden bei Stundenlohn)
- ⚠️ Ferienanspruch (bei Stundenlohn)

---

## 4. CODE-QUALITÄT

### 4.1 Duplikate

**Gefunden:**
1. **KRITISCH:** `recompute_bases_from_items()` - doppelte Zuweisung von `_manual_bvg_employee` und `_manual_bvg_employer`
   - Zeilen 690-691: Erste Zuweisung
   - Zeilen 695-703: Zweite Zuweisung (überschreibt erste)
   - **Fix:** Erste Zuweisung entfernen (Zeilen 690-691)

### 4.2 Konsistenz

**Geprüft:**
- ✅ Alle Calculator verwenden `round_to_5_rappen()`
- ✅ Alle Calculator verwenden `safe_decimal()` für Basis-Werte
- ✅ Alle Calculator verwenden `get_parameter_for_year()` für Parameter
- ✅ Konsistente Fehlerbehandlung mit Logging

---

## 5. EMPFEHLUNGEN

### 5.1 Sofort umzusetzen (HOCH)

1. **Code-Duplikat entfernen**
   - Datei: `adeacore/models.py`
   - Zeilen 690-691 entfernen (erste Zuweisung von `_manual_bvg_employee`)

2. **BVG-Basis korrigieren**
   - Datei: `adealohn/templates/adealohn/payroll/print.html`
   - Zeile 290: `bvg_basis` → `bvg_insured_month` (muss in View berechnet werden)

3. **Pflichtfelder hinzufügen**
   - AHV-Nummer, Geburtsdatum, Eintrittsdatum auf Lohnabrechnung

### 5.2 Kurzfristig (MITTEL)

4. **BVG-Details erweitern**
   - Koordinationsabzug explizit zeigen
   - BVG-Korridore zeigen (Min/Max)

5. **QST-Details erweitern**
   - QST-Basis explizit zeigen
   - QST-Tarif vollständig zeigen

### 5.3 Langfristig (NIEDRIG)

6. **Prüfsummen hinzufügen**
   - Automatische Prüfsummen für Prüfer
   - Summe aller Basen = Bruttolohn

7. **Arbeitszeit-Details**
   - Stunden bei Stundenlohn
   - Ferienanspruch

---

## 6. PRÜFUNG DURCH SOZIALVERSICHERUNGSPRÜFER

### 6.1 Was Prüfer prüfen würden:

1. ✅ **Rundungen:** Korrekt auf 5 Rappen
2. ✅ **Basen:** Korrekt berechnet aus lohnwirksamen Beträgen
3. ✅ **YTD-Logik:** Korrekte Kappung bei Max-Basen
4. ✅ **Rentnerfreibetrag:** Korrekt angewendet
5. ⚠️ **Dokumentation:** Unvollständig (fehlende Pflichtfelder)
6. ✅ **Berechnungen:** Mathematisch korrekt
7. ⚠️ **Nachvollziehbarkeit:** BVG-Basis nicht klar ersichtlich

### 6.2 Mögliche Beanstandungen:

1. **BVG-Basis:** Prüfer könnte falsche Basis beanstanden (zeigt `bvg_basis` statt `bvg_insured_month`)
2. **Fehlende Daten:** AHV-Nummer, Geburtsdatum fehlen
3. **BVG-Koordinationsabzug:** Nicht explizit dokumentiert

---

## 7. FAZIT

**Gesamtbewertung:** ✅ **GUT** (mit Verbesserungspotenzial)

**Stärken:**
- Berechnungen sind mathematisch korrekt
- Rundungen entsprechen Schweizer Standards
- YTD-Logik korrekt implementiert
- Validierung umfassend

**Schwächen:**
- Code-Duplikat muss behoben werden
- Dokumentation auf Lohnabrechnung unvollständig
- BVG-Basis in Druckansicht falsch

**Empfehlung:** 
- Sofort: Code-Duplikat entfernen, BVG-Basis korrigieren
- Kurzfristig: Pflichtfelder hinzufügen
- Langfristig: Prüfsummen und erweiterte Dokumentation

---

**Erstellt:** Automatisierte Code-Prüfung  
**Nächste Prüfung:** Nach Implementierung der Empfehlungen
