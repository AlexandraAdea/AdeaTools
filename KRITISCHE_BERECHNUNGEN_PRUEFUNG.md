# Kritische Berechnungen - Detaillierte Prüfung

## 1. NETTO-LOHN BERECHNUNG

**Datei:** `adeacore/models.py`, Zeile 930-945

```python
def _calculate_net_salary(self):
    self.net_salary = (
        safe_decimal(self.gross_salary)
        - safe_decimal(self.ahv_employee)
        - safe_decimal(self.alv_employee)
        - safe_decimal(self.nbu_employee)
        - safe_decimal(self.ktg_employee)
        - safe_decimal(self.bvg_employee)
        - safe_decimal(self.qst_amount)
    )
```

**✅ PRÜFUNG:**
- ✅ Alle AN-Abzüge werden korrekt abgezogen
- ✅ Reihenfolge korrekt (gross_salary - alle Abzüge)
- ⚠️ **PROBLEM:** Keine Rundung auf 2 Dezimalstellen
- ⚠️ **PROBLEM:** Negative Werte nicht verhindert (sollte `max(..., Decimal("0.00"))` sein)

**RISIKO:** Netto-Lohn könnte negativ werden oder zu viele Dezimalstellen haben

**EMPFEHLUNG:**
```python
def _calculate_net_salary(self):
    from decimal import Decimal, ROUND_HALF_UP
    netto = (
        safe_decimal(self.gross_salary)
        - safe_decimal(self.ahv_employee)
        - safe_decimal(self.alv_employee)
        - safe_decimal(self.nbu_employee)
        - safe_decimal(self.ktg_employee)
        - safe_decimal(self.bvg_employee)
        - safe_decimal(self.qst_amount)
    )
    # Sicherstellen dass Netto nicht negativ ist und auf 2 Dezimalstellen gerundet
    self.net_salary = max(netto, Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
```

---

## 2. QST-BASIS BERECHNUNG (KRITISCH!)

**Datei:** `adeacore/models.py`, Zeile 820-908

**Problem:** QST-Basis wird als `ALV-Basis - AN-Sozialabzüge auf ALV-Basis` berechnet.

**Aktuelle Logik:**
1. ALV-Basis für QST = `alv_basis` (ohne YTD-Kappung für QST-Berechnung)
2. AHV-AN wird auf ALV-Basis neu berechnet (ohne Rentnerfreibetrag)
3. ALV-AN wird auf ALV-Basis verwendet
4. NBU-AN wird auf ALV-Basis neu berechnet
5. KTG-AN wird auf ALV-Basis neu berechnet
6. BVG-AN wird direkt verwendet (nicht neu berechnet)
7. QST-Basis = ALV-Basis - Summe aller AN-Abzüge

**⚠️ KRITISCHES PROBLEM:**

**Problem 1: Inkonsistenz bei BVG**
- BVG wird NICHT auf ALV-Basis neu berechnet
- BVG verwendet `bvg_employee` (berechnet auf `bvg_basis`, nicht `alv_basis`)
- **Risiko:** QST-Basis könnte falsch sein, wenn BVG-Basis ≠ ALV-Basis

**Problem 2: NBU-Berechnung auf ALV-Basis**
- NBU wird auf ALV-Basis berechnet, aber sollte auf UV-Basis berechnet werden
- **Risiko:** Falsche NBU-Berechnung für QST-Basis

**Problem 3: KTG-Berechnung auf ALV-Basis**
- KTG wird auf ALV-Basis berechnet, aber sollte auf UV-Basis berechnet werden
- **Risiko:** Falsche KTG-Berechnung für QST-Basis

**Problem 4: YTD-Logik für QST-Basis**
- ALV-Basis für QST verwendet `alv_basis` ohne YTD-Kappung
- Aber NBU/KTG verwenden YTD-Logik in der Neuberechnung
- **Risiko:** Inkonsistenz zwischen Basis und Abzügen

**EMPFEHLUNG:**

Die QST-Basis sollte konsistent sein:
- Entweder: Alle Abzüge auf ALV-Basis neu berechnen (inkl. BVG)
- Oder: QST-Basis = Bruttolohn - alle tatsächlichen AN-Abzüge (vereinfacht)

**Aktueller Code:**
```python
# Zeile 851-853: AHV auf ALV-Basis
ahv_an_on_alv_basis = alv_basis_for_qst * ahv_rate_employee

# Zeile 857: ALV direkt verwendet
alv_an_on_alv_basis = safe_decimal(self.alv_employee)

# Zeile 860-874: NBU auf ALV-Basis (mit YTD!)
nbu_on_alv_basis = ... # Berechnet mit YTD-Logik

# Zeile 876-893: KTG auf ALV-Basis
ktg_on_alv_basis = ... # Berechnet auf ALV-Basis

# Zeile 896: BVG direkt verwendet (NICHT auf ALV-Basis!)
bvg_an = safe_decimal(self.bvg_employee)
```

**RISIKO:** QST-Basis könnte falsch sein, wenn:
- BVG-Basis ≠ ALV-Basis
- UV-Basis ≠ ALV-Basis (für NBU/KTG)

---

## 3. BVG-BERECHNUNG (YTD-LOGIK)

**Datei:** `adealohn/bvg_calculator.py`

**✅ PRÜFUNG:**

**YTD-Logik:**
```python
ytd_basis = get_ytd_basis(employee, "bvg_ytd_basis")
annual_salary = ytd_basis + basis
```

**✅ KORREKT:**
- Jahreslohn = YTD-Basis + aktuelle Basis
- Eintrittsschwelle geprüft
- Koordinationsabzug angewendet
- Korridore angewendet (Min/Max)

**⚠️ POTENZIELLES PROBLEM:**

**Versicherter Lohn des Monats:**
```python
ytd_insured = get_ytd_basis(employee, "bvg_ytd_insured_salary")
insured_month = insured_annual - ytd_insured
```

**RISIKO:** Wenn `insured_annual` sich ändert (z.B. durch Korridore), könnte `insured_month` negativ werden oder falsch sein.

**Beispiel:**
- Januar: Jahreslohn = 50'000, versichert = 30'000, Monat = 30'000
- Februar: Jahreslohn = 100'000, versichert = 80'000, YTD versichert = 30'000, Monat = 50'000 ✅
- März: Jahreslohn = 150'000, versichert = 120'000 (Max), YTD versichert = 80'000, Monat = 40'000 ✅

**ABER:** Wenn Jahreslohn sinkt oder Korridore sich ändern:
- Januar: Jahreslohn = 150'000, versichert = 120'000 (Max), Monat = 120'000
- Februar: Jahreslohn = 100'000, versichert = 80'000, YTD versichert = 120'000, Monat = -40'000 ❌

**✅ SCHUTZ:** Code prüft `if insured_month < 0: insured_month = Decimal("0.00")`

**BEWERTUNG:** ✅ Korrekt mit Schutz gegen negative Werte

---

## 4. YTD-UPDATE LOGIK

**Datei:** `adeacore/models.py`, Zeile 947-1000

**✅ PRÜFUNG:**

**Update nur bei Status "ABGERECHNET":**
```python
if self.status == "ABGERECHNET":
    # YTD-Updates
```

**✅ KORREKT:**
- YTD wird nur aktualisiert wenn Status = "ABGERECHNET"
- Verhindert doppelte Updates bei Entwürfen

**⚠️ POTENZIELLES PROBLEM:**

**Race Condition bei gleichzeitigen Updates:**
- Wenn zwei PayrollRecords gleichzeitig auf "ABGERECHNET" gesetzt werden
- Beide lesen gleiche YTD-Basis
- Beide addieren ihre Basis
- **Risiko:** YTD wird nur einmal aktualisiert

**EMPFEHLUNG:** `select_for_update()` verwenden (wie bei Januar-Reset)

**Aktueller Code:**
```python
employee.alv_ytd_basis += self.alv_effective_basis
employee.save(update_fields=['alv_ytd_basis'])
```

**RISIKO:** Bei gleichzeitigen Updates könnte YTD falsch sein

---

## 5. RUNDUNGEN

**✅ PRÜFUNG:**

**Sozialversicherungsbeiträge:**
- ✅ AHV: `round_to_5_rappen()` ✅
- ✅ ALV: `round_to_5_rappen()` ✅
- ✅ UVG: `round_to_5_rappen()` ✅
- ✅ BVG: `round_to_5_rappen()` ✅
- ✅ KTG: `round_to_5_rappen()` ✅
- ✅ QST: `round_to_5_rappen()` ✅

**Basen:**
- ✅ Alle Basen: `round_to_2_decimals()` mit `ROUND_HALF_UP` ✅

**Netto-Lohn:**
- ⚠️ **PROBLEM:** Keine explizite Rundung auf 2 Dezimalstellen

**round_to_5_rappen Funktion:**
```python
def round_to_5_rappen(amount: Decimal) -> Decimal:
    return (amount / FIVE_RAPPEN).quantize(Decimal("1"), rounding=ROUND_HALF_UP) * FIVE_RAPPEN
```

**✅ KORREKT:** Verwendet `ROUND_HALF_UP` (Schweizer Standard)

---

## 6. RENTNERFREIBETRAG

**Datei:** `adealohn/ahv_calculator.py`, Zeile 44-48

```python
if employee.is_rentner and employee.ahv_freibetrag_aktiv:
    effective_basis = max(basis - rentner_freibetrag, Decimal("0"))
else:
    effective_basis = basis
```

**✅ PRÜFUNG:**
- ✅ Rentnerfreibetrag: 1'400 CHF/Monat
- ✅ `max(..., Decimal("0"))` verhindert negative Basis
- ✅ Nur wenn `is_rentner` UND `ahv_freibetrag_aktiv`

**BEWERTUNG:** ✅ Korrekt

---

## 7. ALV YTD-KAPPUNG

**Datei:** `adealohn/alv_calculator.py`, Zeile 46-58

```python
ytd_basis = get_ytd_basis(employee, "alv_ytd_basis")

if ytd_basis >= max_year:
    capped_current = Decimal("0.00")
else:
    remaining = max_year - ytd_basis
    capped_current = min(basis, remaining)
```

**✅ PRÜFUNG:**
- ✅ YTD-Basis wird korrekt gelesen
- ✅ Kappung bei 148'200 CHF/Jahr
- ✅ `min(basis, remaining)` verhindert Überschreitung
- ✅ Rentner: Keine ALV

**BEWERTUNG:** ✅ Korrekt

---

## 8. UVG YTD-KAPPUNG

**Datei:** `adealohn/uvg_calculator.py`, Zeile 31-44

```python
ytd_basis = get_ytd_basis(employee, "uvg_ytd_basis")
max_year = params.max_annual_insured_salary

if ytd_basis >= max_year:
    capped_current = Decimal("0.00")
else:
    remaining = max_year - ytd_basis
    capped_current = min(basis, remaining)
```

**✅ PRÜFUNG:**
- ✅ Gleiche Logik wie ALV
- ✅ Kappung bei 148'200 CHF/Jahr
- ✅ BU: Nur Arbeitgeber
- ✅ NBU: Nur Arbeitnehmer (bei >8h/Woche)

**BEWERTUNG:** ✅ Korrekt

---

## 9. MANUELLE BVG-BEITRÄGE

**Datei:** `adeacore/models.py`, Zeile 825-834

```python
manual_bvg_employee = getattr(self, '_manual_bvg_employee', Decimal("0.00"))
manual_bvg_employer = getattr(self, '_manual_bvg_employer', Decimal("0.00"))

self.bvg_employee = round_to_2_decimals(bvg_result["bvg_employee"] + manual_bvg_employee)
self.bvg_employer = round_to_2_decimals(bvg_result["bvg_employer"] + manual_bvg_employer)
```

**✅ PRÜFUNG:**
- ✅ Manuelle Beiträge werden zu berechneten Beiträgen addiert
- ✅ Rundung auf 2 Dezimalstellen
- ⚠️ **PROBLEM:** Manuelle Beiträge sollten auch auf 5 Rappen gerundet werden (wie berechnete)

**RISIKO:** Inkonsistenz bei Rundung

**EMPFEHLUNG:**
```python
# Manuelle Beiträge auf 5 Rappen runden (wie berechnete)
manual_bvg_employee_rounded = round_to_5_rappen(manual_bvg_employee)
manual_bvg_employer_rounded = round_to_5_rappen(manual_bvg_employer)

# Dann addieren und auf 2 Dezimalstellen runden
self.bvg_employee = round_to_2_decimals(bvg_result["bvg_employee"] + manual_bvg_employee_rounded)
```

---

## 10. ZUSAMMENFASSUNG KRITISCHER PROBLEME

### 🔴 KRITISCH (MUSS behoben werden):

1. **QST-Basis Berechnung: Inkonsistenz bei BVG**
   - BVG wird nicht auf ALV-Basis neu berechnet
   - Verwendet `bvg_employee` (auf `bvg_basis` berechnet)
   - **Risiko:** Falsche QST-Basis wenn BVG-Basis ≠ ALV-Basis

2. **Netto-Lohn: Keine Rundung**
   - Netto-Lohn wird nicht auf 2 Dezimalstellen gerundet
   - Negative Werte nicht verhindert
   - **Risiko:** Ungenauigkeiten, negative Netto-Löhne

3. **YTD-Updates: Race Condition**
   - Kein `select_for_update()` bei YTD-Updates
   - **Risiko:** Falsche YTD-Werte bei gleichzeitigen Updates

### 🟡 WICHTIG (sollte behoben werden):

4. **Manuelle BVG-Beiträge: Rundung**
   - Manuelle Beiträge sollten auf 5 Rappen gerundet werden
   - **Risiko:** Inkonsistenz bei Rundung

5. **QST-Basis: NBU/KTG auf falscher Basis**
   - NBU/KTG werden auf ALV-Basis berechnet, sollten auf UV-Basis sein
   - **Risiko:** Falsche QST-Basis wenn UV-Basis ≠ ALV-Basis

---

## 11. EMPFEHLUNGEN

### Sofort umzusetzen:

1. **Netto-Lohn Rundung hinzufügen**
2. **QST-Basis: BVG konsistent berechnen** (auf ALV-Basis oder direkt verwenden)
3. **YTD-Updates: `select_for_update()` verwenden**

### Kurzfristig:

4. **Manuelle BVG-Beiträge: Auf 5 Rappen runden**
5. **QST-Basis: NBU/KTG auf UV-Basis berechnen**

---

**Erstellt:** Automatisierte Code-Prüfung  
**Datum:** {{ aktuelles_datum }}
