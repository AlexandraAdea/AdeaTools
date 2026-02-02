# Test-Anleitung für AdeaLohn

**Datum:** 2. Februar 2026

---

## ✅ VORBEREITUNG

### 1. Migrationen ausführen
```bash
cd C:\AdeaTools\AdeaCore
python manage.py migrate
```

### 2. Server starten
```bash
python manage.py runserver
```

---

## 📋 TEST-ABLAUF

### Schritt 1: Arbeitgeber-Parameter konfigurieren (Arbeitgeber-Ebene)

Im Django Admin (`/admin/`) oder über die Views:

1. **AHVParameter für 2025/2026 erstellen:**
   - Jahr: 2025 (oder 2026)
   - Rate Arbeitnehmer: 0.0530 (5.3%)
   - Rate Arbeitgeber: 0.0530 (5.3%)
   - Rentnerfreibetrag: 1400.00 CHF

2. **ALVParameter für 2025/2026 erstellen:**
   - Jahr: 2025 (oder 2026)
   - Rate Arbeitnehmer: 0.0110 (1.1%)
   - Rate Arbeitgeber: 0.0110 (1.1%)
   - Max. Jahreslohn: 148200.00 CHF

3. **VKParameter für 2025/2026 erstellen:**
   - Jahr: 2025 (oder 2026)
   - Rate Arbeitgeber: 0.03 (3.0%)

4. **KTGParameter für 2025/2026 erstellen:**
   - Jahr: 2025 (oder 2026)
   - Rate Arbeitnehmer: 0.0050 (0.5%)
   - Rate Arbeitgeber: 0.0050 (0.5%)
   - Max. Basis: 300000.00 CHF (optional)

5. **UVGParameter für 2025/2026 erstellen:**
   - Jahr: 2025 (oder 2026)
   - BU Rate AG: 0.00644 (0.644%)
   - NBU Rate AN: 0.0230 (2.3%)
   - Max. Jahreslohn: 148200.00 CHF

6. **FAKParameter für 2025/2026 erstellen:**
   - Jahr: 2025 (oder 2026)
   - Kanton: DEFAULT (oder z.B. 'AG', 'ZH')
   - Rate Arbeitgeber: 0.01 (1.0%)

7. **BVGParameter für 2025/2026 erstellen:**
   - Jahr: 2025 (oder 2026)
   - Eintrittsschwelle: 22050.00 CHF
   - Koordinationsabzug: 25725.00 CHF
   - Min. versicherter Lohn: (aus Police)
   - Max. versicherter Lohn: (aus Police)
   - Rate AN/AG: (aus Police)

---

### Schritt 2: Mitarbeiter anlegen (Mitarbeiter-Ebene)

1. **Mandant auswählen/erstellen:**
   - `/lohn/` → Mandant auswählen
   - Oder neuen Mandant erstellen (Typ: FIRMA, Lohn aktiviert)

2. **Mitarbeiter anlegen:**
   - `/lohn/employees/` → "Neuer Mitarbeiter"
   - Grunddaten: Name, Rolle, Stundensatz
   - Arbeitszeit: Wöchentliche Stunden, Ferienwochen
   - Versicherungen: Rentner, NBU-pflichtig, AHV-Freibetrag
   - QST: QST-pflichtig, Tarif, Kinder, Kirchensteuer, Fixbetrag

---

### Schritt 3: Payroll-Eintrag erstellen (Lohnlauf-Ebene)

1. **Payroll-Eintrag erstellen:**
   - `/lohn/payroll/` → "Neuer Payroll-Eintrag"
   - Mitarbeiter auswählen
   - Monat/Jahr wählen
   - Bei Stundenlohn: Stunden manuell eingeben (falls keine Zeiteinträge)
   - QST-Prozentsatz eingeben (monatlich variabel)

2. **PayrollItems hinzufügen:**
   - BVG-Beiträge (manuell)
   - Familienzulagen (Kinderzulage/Ausbildungszulage)
   - Privatanteil Auto
   - Spesen
   - Überstunden
   - Bonus

3. **Berechnung prüfen:**
   - Payroll-Detail-Seite öffnen
   - Alle Berechnungen prüfen:
     - AHV (5.3% AN/AG)
     - FAK (1.0% AG)
     - VK (3.0% AG vom Total AHV)
     - ALV (1.1% AN/AG, bis 148'200)
     - UVG/BU (0.644% AG)
     - UVG/NBU (2.3% AN, nur ab 8h/Woche)
     - KTG (0.5% AN/AG)
     - BVG (konfigurierbar)
     - QST (auf QST-Basis)

---

## 🔍 WICHTIGE PRÜFPUNKTE

### 1. Parameter werden korrekt geladen
- ✅ Alle Calculator verwenden Parameter für das richtige Jahr
- ✅ Fallback auf Standardwerte wenn Parameter fehlen

### 2. QST-Basis-Berechnung
- ✅ QST-Basis = ALV-Basis - AN-Sozialabzüge auf ALV-Basis
- ✅ AN-Sozialabzüge werden direkt auf ALV-Basis berechnet (nicht proportional)

### 3. Rundung
- ✅ Alle Beträge auf 5 Rappen gerundet

### 4. YTD-Logik
- ✅ ALV: Kappung bei 148'200 CHF/Jahr
- ✅ UVG: Kappung bei 148'200 CHF/Jahr
- ✅ BVG: Jahresakkumulation für versicherten Lohn

---

## 🐛 BEKANNTE PROBLEME

Falls Fehler auftreten:

1. **Parameter fehlen:**
   - Calculator verwenden Fallback-Werte
   - Parameter im Admin erstellen

2. **Migration-Fehler:**
   - Alte KTGParameter-Daten müssen migriert werden
   - Prüfen ob `year` Feld vorhanden ist

3. **QST-Basis = 0:**
   - Prüfen ob ALV-Basis korrekt berechnet wird
   - Prüfen ob AN-Sozialabzüge korrekt sind

---

## 📝 NÄCHSTE SCHRITTE

Nach erfolgreichem Test:
1. Parameter für alle Jahre konfigurieren (2025, 2026, etc.)
2. Testdaten mit Excel-Vorlage vergleichen
3. Bei Abweichungen: Parameter anpassen
