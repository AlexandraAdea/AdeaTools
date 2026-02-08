# Payroll-Bug Analyse: UI vs Print - Unterschiedliche Auszahlungsbeträge

**Datum:** 2026-02-03  
**Analyst:** Lead Senior Engineer + Payroll/HR-Reviewer + Security-Auditor

---

## I) FUNDSTELLEN (Liste)

### Views/Controller:
1. **`adealohn/views.py`**:
   - `PayrollRecordDetailView.get_context_data()` (Zeile 704-792)
   - `PayrollRecordPrintView.get_context_data()` (Zeile 803-942)

### Templates:
2. **`adealohn/templates/adealohn/payroll/detail.html`**:
   - Zeile 426: `{{ record.net_salary|floatformat:2 }} CHF`

3. **`adealohn/templates/adealohn/payroll/print.html`**:
   - Zeile 371-374: Privatanteile Abzüge
   - Zeile 400-401: `{{ auszahlung|floatformat:2 }} CHF`

### Models/Berechnung:
4. **`adeacore/models.py`**:
   - `PayrollRecord._calculate_net_salary()` (Zeile 970-989)
   - `PayrollRecord.save()` ruft `_calculate_net_salary()` auf (Zeile 1066)

### Services/Helpers:
5. **Kein zentraler Calc-Service gefunden** - Berechnungen sind in Views und Models verteilt

---

## II) URSACHE DER ABWEICHUNG (2–5 Bulletpoints)

### **KRITISCH: Unterschiedliche Berechnungslogik**

1. **UI (DetailView) verwendet `record.net_salary` aus Model:**
   ```python
   # adeacore/models.py, Zeile 978-986
   netto = (
       safe_decimal(self.gross_salary)
       - safe_decimal(self.ahv_employee)
       - safe_decimal(self.alv_employee)
       - safe_decimal(self.nbu_employee)
       - safe_decimal(self.ktg_employee)
       - safe_decimal(self.bvg_employee)
       - safe_decimal(self.qst_amount)
   )
   ```
   **Problem:** Privatanteile werden NICHT abgezogen!

2. **Print (PrintView) berechnet `auszahlung` im View:**
   ```python
   # adealohn/views.py, Zeile 926-932
   auszahlung = (
       bruttolohn
       - abzuege_sozialversicherungen
       - summe_privatanteile  # ← Privatanteile werden abgezogen!
       - (record.qst_amount or Decimal("0"))
       + summe_familienzulagen
   )
   ```
   **Problem:** Andere Berechnung als Model!

3. **Keine Single Source of Truth:**
   - Model berechnet `net_salary` ohne Privatanteile
   - Print berechnet `auszahlung` mit Privatanteile-Abzug
   - UI zeigt `net_salary` (falsch für Auszahlung)

4. **Privatanteile-Logik inkonsistent:**
   - Privatanteile sind `is_lohnwirksam=True` → werden zum Bruttolohn addiert
   - Aber: Sie müssen auch als Abzug erscheinen (Sage-Standard)
   - Model berücksichtigt das nicht, Print schon

---

## III) PATCH-PLAN (Schritte, priorisiert P0/P1)

### **P0 (KRITISCH - Sofort fixen):**
1. Erstelle zentrale Berechnungsfunktion `calculate_payroll_payout()`
2. Fixe `_calculate_net_salary()` im Model (Privatanteile abziehen)
3. Print-View verwendet zentrale Funktion
4. UI zeigt korrekte Auszahlung (nicht `net_salary`)

### **P1 (Wichtig - Nächster Sprint):**
5. Refactoring: Alle Berechnungen in Service-Klasse
6. Integrationstests für Berechnungen
7. Dokumentation der Berechnungslogik

---

## IV) KONKRETE CODEÄNDERUNGEN

### **1. Neue Datei: `adealohn/payroll_calculator.py`**

```python
from decimal import Decimal
from adeacore.models import PayrollRecord
from adeacore.money import round_to_5_rappen


def calculate_payroll_payout(payroll_record: PayrollRecord) -> dict:
    """
    Zentrale Funktion für Payroll-Auszahlungsberechnung.
    Single Source of Truth für UI und Print.
    
    Returns:
        {
            'brutto': Decimal,
            'sozialabzuege_total': Decimal,
            'privatanteile_total': Decimal,
            'zulagen_total': Decimal,
            'qst_abzug': Decimal,
            'auszahlung': Decimal,
            'rundung': Decimal,
            'breakdown': {
                'ahv': Decimal,
                'alv': Decimal,
                'nbu': Decimal,
                'bvg': Decimal,
                'ktg': Decimal,
            }
        }
    """
    # Bruttolohn
    brutto = payroll_record.gross_salary or Decimal("0")
    
    # Sozialabzüge
    abzuege_sozialversicherungen = (
        (payroll_record.ahv_employee or Decimal("0")) +
        (payroll_record.alv_employee or Decimal("0")) +
        (payroll_record.nbu_employee or Decimal("0")) +
        (payroll_record.bvg_employee or Decimal("0"))
    )
    
    # Privatanteile (aus PayrollItems)
    privatanteil_items = payroll_record.items.filter(
        wage_type__code__startswith="PRIVATANTEIL_"
    )
    summe_privatanteile = sum(item.total for item in privatanteil_items)
    
    # Familienzulagen (Durchlaufender Posten SVA)
    family_allowance_items = payroll_record.items.filter(
        wage_type__code__in=['KINDERZULAGE', 'FAMILIENZULAGE']
    )
    summe_familienzulagen = sum(item.total for item in family_allowance_items)
    
    # QST
    qst_abzug = payroll_record.qst_amount or Decimal("0")
    
    # Auszahlung berechnen
    auszahlung_raw = (
        brutto
        - abzuege_sozialversicherungen
        - summe_privatanteile  # Privatanteile abziehen
        - qst_abzug
        + summe_familienzulagen  # Zulagen addieren
    )
    
    # Rundung auf 5 Rappen
    auszahlung_gerundet = round_to_5_rappen(auszahlung_raw)
    rundung = auszahlung_gerundet - auszahlung_raw
    
    return {
        'brutto': brutto,
        'sozialabzuege_total': abzuege_sozialversicherungen,
        'privatanteile_total': summe_privatanteile,
        'zulagen_total': summe_familienzulagen,
        'qst_abzug': qst_abzug,
        'auszahlung': auszahlung_gerundet,
        'rundung': rundung,
        'breakdown': {
            'ahv': payroll_record.ahv_employee or Decimal("0"),
            'alv': payroll_record.alv_employee or Decimal("0"),
            'nbu': payroll_record.nbu_employee or Decimal("0"),
            'bvg': payroll_record.bvg_employee or Decimal("0"),
            'ktg': payroll_record.ktg_employee or Decimal("0"),
        }
    }
```

### **2. Fix `adeacore/models.py` - `_calculate_net_salary()`:**

```python
def _calculate_net_salary(self):
    """
    Berechnet Netto-Lohn: Bruttolohn - alle AN-Abzüge - Privatanteile.
    Rundet auf 2 Dezimalstellen und verhindert negative Werte.
    """
    from decimal import Decimal, ROUND_HALF_UP
    from adealohn.helpers import safe_decimal
    
    # Privatanteile berechnen
    privatanteil_items = self.items.filter(
        wage_type__code__startswith="PRIVATANTEIL_"
    )
    summe_privatanteile = sum(item.total for item in privatanteil_items)
    
    netto = (
        safe_decimal(self.gross_salary)
        - safe_decimal(self.ahv_employee)
        - safe_decimal(self.alv_employee)
        - safe_decimal(self.nbu_employee)
        - safe_decimal(self.ktg_employee)
        - safe_decimal(self.bvg_employee)
        - safe_decimal(self.qst_amount)
        - summe_privatanteile  # ← NEU: Privatanteile abziehen
    )
    
    # Sicherstellen dass Netto nicht negativ ist und auf 2 Dezimalstellen gerundet
    self.net_salary = max(netto, Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
```

### **3. Fix `adealohn/views.py` - `PayrollRecordPrintView.get_context_data()`:**

```python
# Zeile 920-940 ersetzen durch:
from adealohn.payroll_calculator import calculate_payroll_payout

# Berechnung der Auszahlung
payout_result = calculate_payroll_payout(record)
context["auszahlung"] = payout_result["auszahlung"]
context["rundung"] = payout_result["rundung"]
context["abzuege_sozialversicherungen"] = payout_result["sozialabzuege_total"]
context["summe_privatanteile"] = payout_result["privatanteile_total"]
context["summe_familienzulagen"] = payout_result["zulagen_total"]
context["qst_abzug"] = payout_result["qst_abzug"]
```

### **4. Fix `adealohn/views.py` - `PayrollRecordDetailView.get_context_data()`:**

```python
# Am Ende von get_context_data() hinzufügen (nach Zeile 790):
from adealohn.payroll_calculator import calculate_payroll_payout

# Berechnung der Auszahlung (für UI-Anzeige)
payout_result = calculate_payroll_payout(self.object)
context["auszahlung"] = payout_result["auszahlung"]
context["auszahlung_breakdown"] = payout_result["breakdown"]
```

### **5. Fix `adealohn/templates/adealohn/payroll/detail.html`:**

```html
<!-- Zeile 426 ersetzen: -->
<li style="border-top:1px solid rgba(0,0,0,0.1); padding-top:8px; margin-top:8px;">
    <strong>Netto-Lohn:</strong> {{ record.net_salary|floatformat:2 }} CHF
    <br><em style="color:#8e8e93; font-size:0.9em;">(Berechnet ohne Privatanteile)</em>
</li>
{% if summe_privatanteile > 0 %}
<li>
    <strong>Privatanteile Abzug:</strong> -{{ summe_privatanteile|floatformat:2 }} CHF
</li>
{% endif %}
{% if summe_familienzulagen > 0 %}
<li>
    <strong>Spesen und Zulagen:</strong> +{{ summe_familienzulagen|floatformat:2 }} CHF
</li>
{% endif %}
<li style="border-top:2px solid rgba(0,0,0,0.2); padding-top:8px; margin-top:8px; font-size:1.1em;">
    <strong>Auszahlung:</strong> {{ auszahlung|floatformat:2 }} CHF
</li>
```

---

## V) SICHERHEITSCHECK

### **Tenant-Sicherheit:**

✅ **GEFUNDEN:** `PayrollRecordDetailView` und `PayrollRecordPrintView` verwenden beide `TenantObjectMixin`

**Dateipfad:** `adealohn/mixins.py`, Zeile 164-180

```python
class TenantObjectMixin(TenantMixin):
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        current_client = self.get_current_client()
        
        if current_client and hasattr(obj, 'employee'):
            if obj.employee.client != current_client:
                from django.core.exceptions import PermissionDenied
                raise PermissionDenied("Kein Zugriff auf dieses Objekt.")
        
        return obj
```

**Status:** ✅ **SICHER** - Beide Views sind tenant-geschützt

### **Berechtigungen:**

✅ **GEFUNDEN:** Beide Views verwenden `LoginRequiredMixin`

**Dateipfad:** `adealohn/views.py`, Zeile 700, 795

**Status:** ✅ **SICHER** - Nur eingeloggte User haben Zugriff

---

## VI) 5 KURZE TESTS (verhindern zukünftige Probleme)

### **Test 1: Privatanteile werden korrekt abgezogen**
```python
def test_privatanteile_abzug_in_auszahlung():
    """Privatanteile müssen in Auszahlung abgezogen werden."""
    payroll = create_payroll_with_privatanteil(amount=100)
    result = calculate_payroll_payout(payroll)
    assert result['auszahlung'] == result['brutto'] - result['sozialabzuege_total'] - 100 - result['qst_abzug'] + result['zulagen_total']
```

### **Test 2: UI und Print zeigen gleiche Auszahlung**
```python
def test_ui_print_consistency():
    """UI und Print müssen identische Auszahlung zeigen."""
    payroll = create_test_payroll()
    detail_view = PayrollRecordDetailView()
    print_view = PayrollRecordPrintView()
    
    detail_context = detail_view.get_context_data(object=payroll)
    print_context = print_view.get_context_data(object=payroll)
    
    assert detail_context['auszahlung'] == print_context['auszahlung']
```

### **Test 3: Familienzulagen werden addiert**
```python
def test_familienzulagen_addiert():
    """Familienzulagen müssen zur Auszahlung addiert werden."""
    payroll = create_payroll_with_family_allowance(amount=215)
    result = calculate_payroll_payout(payroll)
    assert result['zulagen_total'] == 215
    assert result['auszahlung'] > result['brutto'] - result['sozialabzuege_total'] - result['privatanteile_total']
```

### **Test 4: Rundung auf 5 Rappen**
```python
def test_rundung_5_rappen():
    """Auszahlung muss auf 5 Rappen gerundet sein."""
    payroll = create_payroll_with_odd_amount()
    result = calculate_payroll_payout(payroll)
    assert result['auszahlung'] % Decimal("0.05") == 0
```

### **Test 5: Tenant-Isolation**
```python
def test_tenant_isolation():
    """User kann nur PayrollRecords seines Tenants sehen."""
    client_a = create_client("Client A")
    client_b = create_client("Client B")
    payroll_a = create_payroll(client=client_a)
    payroll_b = create_payroll(client=client_b)
    
    view = PayrollRecordDetailView()
    view.request = MockRequest(client=client_a)
    
    # Sollte funktionieren
    view.get_object(pk=payroll_a.pk)
    
    # Sollte PermissionDenied werfen
    with pytest.raises(PermissionDenied):
        view.get_object(pk=payroll_b.pk)
```

---

## ZUSAMMENFASSUNG

**Problem:** UI zeigt `net_salary` (ohne Privatanteile-Abzug), Print zeigt `auszahlung` (mit Privatanteile-Abzug) → unterschiedliche Beträge

**Lösung:** Zentrale Funktion `calculate_payroll_payout()`, beide Views verwenden diese, Model `_calculate_net_salary()` wird gefixt

**Sicherheit:** ✅ Beide Views sind tenant-geschützt

**Priorität:** P0 (KRITISCH) - Finanzielle Diskrepanz zwischen UI und Print
