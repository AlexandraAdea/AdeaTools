# AdeaLohn - Geschäftslogik Dokumentation

**Erstellt:** 2026-02-03  
**Status:** Verbindlich für alle Entwickler

---

## 📋 Inhaltsverzeichnis

1. [Bruttolohn-Berechnung](#bruttolohn-berechnung)
2. [Familienzulagen](#familienzulagen)
3. [Privatanteile](#privatanteile)
4. [BVG-Beiträge](#bvg-beiträge)
5. [Sozialversicherungs-Basis](#sozialversicherungs-basis)
6. [Auszahlungsberechnung](#auszahlungsberechnung)

---

## 💰 Bruttolohn-Berechnung

### Was gehört zum Bruttolohn?

**✅ ZUM BRUTTOLOHN:**
- Monatslohn (`GRUNDLOHN_MONAT`)
- Stundenlohn × Arbeitsstunden (`GRUNDLOHN_STUNDEN`)
- **Privatanteile** (Auto, Natel) - werden später wieder abgezogen
- Bonus/Prämien (falls `is_lohnwirksam=True`)
- Überstunden (falls `is_lohnwirksam=True`)

**❌ NICHT ZUM BRUTTOLOHN:**
- **Familienzulagen** (Durchlaufender Posten SVA)
- Spesen (effektiv oder pauschal)
- BVG-Beiträge (sind Abzüge, nicht Lohnbestandteil)

### Berechnung

```python
gross_salary = sum(item.total for item in payroll_items where item.wage_type.is_lohnwirksam == True)
```

**Wichtig:** Familienzulagen haben `is_lohnwirksam=False` und werden NICHT zum Bruttolohn addiert.

---

## 👨‍👩‍👧‍👦 Familienzulagen

### Definition

**Familienzulagen sind durchlaufende Posten SVA (Sozialversicherungsanstalt).**

### Geschäftslogik

**✅ IMMER DURCHLAUFENDER POSTEN:**
- Familienzulagen gehören **NICHT** zum Bruttolohn
- Familienzulagen sind **NICHT AHV-pflichtig**
- Familienzulagen sind **NICHT ALV-pflichtig**
- Familienzulagen sind **NICHT BVG-pflichtig**
- Familienzulagen sind **NICHT UVG-pflichtig**
- Familienzulagen sind **QST-pflichtig** (Quellensteuer)

### Buchhaltung

Der Arbeitgeber:
1. Zahlt die Familienzulagen aus
2. Erhält diese von der Familienausgleichskasse (FAK) zurück:
   - Direkte Gutschrift aufs Bankkonto, ODER
   - Verrechnung mit der AHV/IV/EO-Beitragsrechnung (häufigste Variante)

### Ausnahmen

**Freiwillige Familienzulagen über gesetzliche hinaus:**
- Wenn ein Arbeitgeber über die gesetzlichen Zulagen hinaus eigene Zulagen zahlt
- Diese sind **Teil des Lohns** und **AHV-pflichtig**
- Müssen als separate Lohnart erfasst werden (z.B. `ZULAGE_FREIWILLIG_FAMILIE`)

### WageTypes

- `KINDERZULAGE` - Gesetzliche Kinderzulage (durchlaufender Posten)
- `FAMILIENZULAGE` - Alte Bezeichnung (für Rückwärtskompatibilität)
- `AUSBILDUNGSZULAGE` - Ausbildungszulage (falls verwendet)

**Alle haben:**
- `is_lohnwirksam = False`
- `ahv_relevant = False`
- `alv_relevant = False`
- `bvg_relevant = False`
- `uv_relevant = False`
- `qst_relevant = True`

### Anzeige

Familienzulagen werden angezeigt als:
- **"Spesen und Zulagen"** in der Lohnabrechnung
- **Separater Posten** nach den Sozialversicherungs-Abzügen
- **Addition** zur Auszahlung (nicht Teil des Bruttolohns)

---

## 🚗 Privatanteile

### Definition

**Privatanteile sind Sachleistungen, die dem Mitarbeiter zur Verfügung gestellt werden.**

### Arten

**Nur zwei Arten werden unterstützt:**
1. **Privatanteil Auto** (`PRIVATANTEIL_AUTO`)
2. **Privatanteil Natel** (`PRIVATANTEIL_NATEL`)

**Beide werden manuell erfasst** (keine automatische Berechnung).

### Geschäftslogik

**✅ ZUM BRUTTOLOHN:**
- Privatanteile werden zum Bruttolohn addiert
- Sie erhöhen die **Sozialversicherungs-Basis** (AHV, ALV, NBU, BVG)

**✅ ABZUG VOM NETTOLOHN:**
- Privatanteile werden vom Nettolohn abgezogen
- Sie erscheinen als **"Privatanteile Abzüge"** in der Lohnabrechnung

### Berechnung

```
Bruttolohn = Monatslohn + Privatanteile
Sozialversicherungs-Basis = Bruttolohn (inkl. Privatanteile)
Nettolohn = Bruttolohn - Sozialversicherungs-Abzüge
Auszahlung = Nettolohn - Privatanteile
```

### Beispiel

```
Monatslohn:              7'200.00 CHF
+ Privatanteil Auto:    +150.00 CHF
= Bruttolohn für SV:    7'350.00 CHF

AHV/IV/EO (5.3%):       -389.55 CHF
ALV (1.1%):              -80.85 CHF
NBU (1.5%):             -110.25 CHF
BVG (5% von 4'995):     -249.75 CHF

= Nettolohn:            6'519.60 CHF
- Privatanteil Auto:    -150.00 CHF
= Auszahlung:           6'369.60 CHF
```

### WageTypes

- `PRIVATANTEIL_AUTO` - Privatanteil Auto
- `PRIVATANTEIL_NATEL` - Privatanteil Natel (Telefon)

**Beide haben:**
- `is_lohnwirksam = True` (gehören zum Bruttolohn)
- `ahv_relevant = True`
- `alv_relevant = True`
- `bvg_relevant = True` (falls BVG-Basis relevant)
- `uv_relevant = True`

---

## 💼 BVG-Beiträge

### Definition

**BVG (Berufliche Vorsorge, 2. Säule) Beiträge werden manuell erfasst.**

### Geschäftslogik

**✅ IMMER MANUELL:**
- BVG-Beiträge werden **NICHT automatisch berechnet**
- Sie werden direkt im PayrollRecord erfasst:
  - `manual_bvg_employee` - Arbeitnehmerbeitrag
  - `manual_bvg_employer` - Arbeitgeberbeitrag

**❌ NICHT ALS LOHNART:**
- BVG-Beiträge sind **KEINE Lohnarten**
- `BVG_AN` und `BVG_AG` WageTypes existieren nicht mehr
- BVG-Beiträge können **NICHT** als PayrollItem erfasst werden

### Optional: Automatische Berechnung

**Falls BVG-Parameter konfiguriert sind:**
- System kann automatisch berechnen
- Manuelle Beiträge werden zu berechneten Beiträgen **addiert**
- Formel: `bvg_employee = berechnet + manual_bvg_employee`

**Falls KEINE BVG-Parameter konfiguriert sind:**
- Nur manuelle Beiträge werden verwendet
- `bvg_employee = manual_bvg_employee`
- `bvg_employer = manual_bvg_employer`

### BVG-Basis

Die BVG-Basis wird aus lohnwirksamen WageTypes berechnet:
- `bvg_basis = sum(item.total for item in payroll_items where item.wage_type.bvg_relevant == True)`

**Wichtig:** Privatanteile sind BVG-relevant und erhöhen die BVG-Basis.

---

## 📊 Sozialversicherungs-Basis

### AHV/IV/EO-Basis

```
ahv_basis = sum(item.total for item in payroll_items where item.wage_type.ahv_relevant == True)
```

**✅ ZUR BASIS:**
- Monatslohn / Stundenlohn
- Privatanteile (Auto, Natel)
- Bonus/Prämien (falls `ahv_relevant=True`)
- Überstunden (falls `ahv_relevant=True`)

**❌ NICHT ZUR BASIS:**
- Familienzulagen (`ahv_relevant=False`)

### ALV-Basis

```
alv_basis = sum(item.total for item in payroll_items where item.wage_type.alv_relevant == True)
```

**✅ ZUR BASIS:**
- Monatslohn / Stundenlohn
- Privatanteile (Auto, Natel)
- Bonus/Prämien (falls `alv_relevant=True`)

**❌ NICHT ZUR BASIS:**
- Familienzulagen (`alv_relevant=False`)

### BVG-Basis

```
bvg_basis = sum(item.total for item in payroll_items where item.wage_type.bvg_relevant == True)
```

**✅ ZUR BASIS:**
- Monatslohn / Stundenlohn
- Privatanteile (Auto, Natel)
- Bonus/Prämien (falls `bvg_relevant=True`)

**❌ NICHT ZUR BASIS:**
- Familienzulagen (`bvg_relevant=False`)

### UVG-Basis

```
uv_basis = sum(item.total for item in payroll_items where item.wage_type.uv_relevant == True)
```

**✅ ZUR BASIS:**
- Monatslohn / Stundenlohn
- Privatanteile (Auto, Natel)
- Bonus/Prämien (falls `uv_relevant=True`)

**❌ NICHT ZUR BASIS:**
- Familienzulagen (`uv_relevant=False`)

---

## 💵 Auszahlungsberechnung

### Formel

```
Auszahlung = Bruttolohn
           - Abzüge Sozialversicherungen (AHV, ALV, NBU, BVG)
           - Privatanteile Abzüge
           - QST Abzug
           + Spesen und Zulagen (Familienzulagen)
           + Rundung (auf 5 Rappen)
```

### Beispiel-Berechnung

```
Monatslohn:                   7'200.00 CHF
+ Privatanteil Auto:         +150.00 CHF
= Bruttolohn:                7'350.00 CHF

Abzüge Sozialversicherungen:
  AHV (5.3% von 7'350):      -389.55 CHF
  ALV (1.1% von 7'350):       -80.85 CHF
  NBU (1.5% von 7'350):     -110.25 CHF
  BVG (manuell):             -249.75 CHF
= Total Abzüge:            -1'510.62 CHF

- Privatanteile Abzüge:      -150.00 CHF
- QST Abzug:                   0.00 CHF (falls nicht QST-pflichtig)
+ Spesen und Zulagen:        +215.00 CHF (Familienzulage)
+ Rundung:                    +0.02 CHF

= Auszahlung:                6'369.60 CHF
```

### Rundung

Die Auszahlung wird auf **5 Rappen gerundet** (0.05 CHF).

---

## ✅ Validierungsregeln

### PayrollRecord

1. **Bruttolohn:** Muss >= 0 sein
2. **Familienzulagen:** Dürfen NICHT zum Bruttolohn gehören
3. **BVG-Beiträge:** Dürfen NICHT als PayrollItem erfasst werden
4. **Privatanteile:** Nur Auto und Natel erlaubt

### PayrollItem

1. **BVG_AN/BVG_AG:** Dürfen NICHT als WageType verwendet werden
2. **Familienzulagen:** Müssen `is_lohnwirksam=False` haben
3. **Privatanteile:** Müssen `is_lohnwirksam=True` haben

---

## 📝 Änderungshistorie

- **2026-02-03:** Dokumentation erstellt basierend auf HR-Profi Feedback
- **2026-02-03:** Familienzulagen als durchlaufender Posten bestätigt
- **2026-02-03:** Privatanteile (nur Auto/Natel) dokumentiert
- **2026-02-03:** BVG-Beiträge als manuelle Eingabe bestätigt
