# Excel-Vorlage Struktur - Hierarchie

**Datum:** 2. Februar 2026  
**Basis:** Excel-Vorlage "Lohnbuchhaltung einfach. By Run my Accounts AG"

---

## 📋 STRUKTUR-HIERARCHIE (wie in Excel)

### 1️⃣ ARBEITGEBER-EBENE (für gesamten Arbeitgeber gültig)

#### A) Firmendaten (Client)
- **Name, Adresse, Kontakt**
- **MWST-Nummer / UID**
- **Arbeitskanton** (`work_canton`) - für FAK und kantonale Beiträge
- **Lohnmodul aktiviert** (`lohn_aktiv`)

#### B) Arbeitgeber-Parameter (global, jahresabhängig)
Diese Parameter gelten für **alle Mitarbeiter** des Arbeitgebers:

1. **BVGParameter** (pro Jahr)
   - Eintrittsschwelle
   - Koordinationsabzug
   - Min/Max versicherter Lohn
   - AN/AG-Sätze

2. **KTGParameter** (pro Jahr)
   - AN/AG-Sätze
   - Max-Basis (optional)

3. **UVGParameter** (pro Jahr)
   - BU-Satz AG
   - NBU-Satz AN
   - Max-Basis (148'200 CHF)

4. **FAKParameter** (pro Jahr, kantonabhängig)
   - FAK-Satz AG (kantonabhängig, z.B. 1.025% Standard, 1.450% Aargau)

5. **QSTParameter** (pro Jahr, tarifabhängig)
   - QST-Tarife (A0N, A0Y, B1N, B1Y, etc.)
   - Prozentsätze oder Fixbeträge pro Tarif

6. **FamilyAllowanceParameter** (pro Jahr)
   - Kinderzulage (pro Kind)
   - Ausbildungszulage (pro Kind in Ausbildung)

---

### 2️⃣ MITARBEITER-EBENE (persönliche/allgemeine Daten)

#### A) Grunddaten (Employee)
- **Name** (`first_name`, `last_name`)
- **Rolle** (`role`)
- **Mandant** (`client`) - Verknüpfung zum Arbeitgeber

#### B) Arbeitszeit & Versicherungen (Employee)
- **Stundensatz** (`hourly_rate`) - für Stundenlöhne
- **Wöchentliche Stunden** (`weekly_hours`)
- **Ferienwochen** (`vacation_weeks`) - 4/5/6 Wochen
- **Rentner** (`is_rentner`)
- **AHV-Freibetrag aktiv** (`ahv_freibetrag_aktiv`) - nur bei Rentnern
- **NBU-pflichtig** (`nbu_pflichtig`) - automatisch ab 8h/Woche

#### C) Quellensteuer (QST) - persönliche Daten (Employee)
- **QST-pflichtig** (`qst_pflichtig`)
- **QST-Tarif** (`qst_tarif`) - A/B (Familienstand) oder vollständig (A0N, B1Y)
- **QST-Kinder** (`qst_kinder`)
- **QST-Kirchensteuer** (`qst_kirchensteuer`)
- **QST-Fixbetrag** (`qst_fixbetrag`) - hat Vorrang vor Prozentsatz

**Hinweis:** `qst_prozent` wurde von Employee nach PayrollRecord verschoben (monatlich variabel bei Stundenlöhnen)

---

### 3️⃣ LOHNLAUF-SPEZIFISCH (persönliche Ansätze/Daten pro Monat)

#### A) PayrollRecord (monatliche Lohnabrechnung)
- **Mitarbeiter** (`employee`)
- **Monat/Jahr** (`month`, `year`)
- **Status** (`status`) - Entwurf, Geprüft, Abgerechnet, Gesperrt
- **QST-Prozentsatz** (`qst_prozent`) - **monatlich variabel** (bei Stundenlöhnen)

#### B) PayrollItems (Lohnkomponenten pro Monat)

Diese werden **pro Monat** erfasst:

1. **BVG-Beiträge**
   - WageType: `BVG_AN`, `BVG_AG`
   - Manuell eingegeben (pro Monat)
   - Oder automatisch berechnet (falls konfiguriert)

2. **Familienzulagen**
   - WageType: `KINDERZULAGE`, `AUSBILDUNGSZULAGE`
   - Beträge aus FamilyAllowanceParameter
   - Nachzahlungen möglich (separat erfasst)

3. **Privatanteil Auto**
   - WageType: `PRIVATANTEIL_AUTO`
   - 0.9% vom Kaufpreis (exkl. MWST)
   - Mitarbeiterbeitrag wird abgezogen
   - Nur Netto wird zur Basis addiert

4. **Spesen**
   - WageType: `SPESEN_*` (verschiedene Spesenarten)
   - Steuer- und sozialversicherungsfrei
   - Werden zum Netto addiert

5. **Überstunden**
   - WageType: `UEBERSTUNDEN_*`
   - Mit Zuschlägen (25% normal, 50% Nacht/Sonntag)
   - Sozialversicherungspflichtig

6. **Bonus/Gratifikationen**
   - WageType: `BONUS`
   - Sozialversicherungspflichtig

7. **Grundlohn**
   - WageType: `GRUNDLOHN_MONAT` (Monatslohn)
   - WageType: `GRUNDLOHN_STUNDEN` (Stundenlohn)
   - Ferienentschädigung wird automatisch hinzugefügt (bei Stundenlohn)

---

## 📊 ZUSAMMENFASSUNG

### Hierarchie:
```
1. ARBEITGEBER (Client)
   ├── Firmendaten (Name, Adresse, Kanton)
   └── Parameter (BVG, KTG, UVG, FAK, QST, Familienzulagen)
       └── Gilt für ALLE Mitarbeiter

2. MITARBEITER (Employee)
   ├── Grunddaten (Name, Rolle)
   ├── Arbeitszeit (Stunden, Stundensatz, Ferienwochen)
   ├── Versicherungen (Rentner, NBU, AHV-Freibetrag)
   └── QST-Daten (Tarif, Kinder, Kirchensteuer, Fixbetrag)
       └── Gilt für ALLE Lohnläufe des Mitarbeiters

3. LOHNLAUF (PayrollRecord + PayrollItems)
   ├── Monat/Jahr
   ├── QST-Prozentsatz (monatlich variabel)
   └── PayrollItems (BVG, Familienzulagen, Auto, Spesen, Überstunden, Bonus)
       └── Pro Monat individuell
```

---

## ✅ IMPLEMENTIERUNG IN ADEALOHN

### Arbeitgeber-Ebene:
- ✅ `Client` Model (Firmendaten, `work_canton`)
- ✅ `BVGParameter`, `KTGParameter`, `UVGParameter`, `FAKParameter`, `QSTParameter`, `FamilyAllowanceParameter`

### Mitarbeiter-Ebene:
- ✅ `Employee` Model (Grunddaten, Arbeitszeit, Versicherungen, QST-Daten)

### Lohnlauf-Ebene:
- ✅ `PayrollRecord` Model (Monat/Jahr, Status, `qst_prozent`)
- ✅ `PayrollItem` Model (Lohnkomponenten pro Monat)
- ✅ `WageType` Model (Kategorisierung der Lohnkomponenten)

---

## 🎯 WICHTIGE UNTERSCHIEDE ZU EXCEL

### Excel:
- Alle Daten in einer Tabelle
- Arbeitgeber-Parameter oben
- Mitarbeiter-Daten in der Mitte
- Lohnlauf-Daten unten

### AdeaLohn (Django):
- **Normalisierte Datenbankstruktur**
- Arbeitgeber-Parameter: Separate Models (pro Jahr)
- Mitarbeiter-Daten: `Employee` Model
- Lohnlauf-Daten: `PayrollRecord` + `PayrollItems`

**Vorteil:** Flexibler, keine Duplikate, bessere Datenintegrität

---

## 📝 HINWEIS

Die Struktur in AdeaLohn entspricht der Excel-Vorlage, ist aber in einer normalisierten Datenbankstruktur organisiert. Die Hierarchie bleibt erhalten:

1. **Arbeitgeber-Parameter** → gelten für alle
2. **Mitarbeiter-Daten** → gelten für alle Lohnläufe
3. **Lohnlauf-Daten** → gelten nur für diesen Monat
