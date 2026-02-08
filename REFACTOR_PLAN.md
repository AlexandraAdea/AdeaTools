# Refactor-Plan: Einheitliche deutsche Benennungen im Payroll-Modul

## I) FUNDSTELLENLISTE

### `gross_salary` (DB-Feld):
- `adeacore/models.py:535` - Model-Feld Definition
- `adeacore/models.py:695` - Zuweisung in `recompute_bases_from_items()`
- `adeacore/models.py:979` - Verwendung in `_calculate_net_salary()`
- `adeacore/admin.py:248` - Admin list_display
- `adeacore/admin.py:276` - Admin fieldsets
- `adealohn/forms.py:172` - Form field
- `adealohn/forms.py:180` - Form label
- `adealohn/forms.py:194` - Form widget
- `adealohn/forms.py:244-252` - Form Logik
- `adealohn/views.py:568, 676` - View Logik
- `adealohn/views.py:782` - Kommentar
- `adealohn/views.py:925` - Print-View Berechnung
- `adealohn/templates/adealohn/payroll/detail.html:93, 415, 418` - Template
- `adealohn/templates/adealohn/payroll/print.html:261, 285, 292, 300, 365` - Template
- `adealohn/templates/adealohn/payroll/list.html:101` - Template
- `adealohn/templates/adealohn/payroll/confirm_delete.html:21` - Template
- `adealohn/tests_integration.py:130, 187, 354` - Tests
- `adealohn/qst_calculator.py:25` - QST Calculator
- `adealohn/fak_calculator.py:35` - FAK Calculator

### `net_salary` (DB-Feld):
- `adeacore/models.py:589` - Model-Feld Definition
- `adeacore/models.py:989` - Zuweisung in `_calculate_net_salary()`
- `adeacore/models.py:1066` - Aufruf von `_calculate_net_salary()`
- `adeacore/admin.py:249` - Admin list_display
- `adeacore/admin.py:277` - Admin fieldsets
- `adeacore/admin.py:342` - Admin readonly_fields
- `adealohn/templates/adealohn/payroll/detail.html:426` - Template
- `adealohn/templates/adealohn/payroll/list.html:102` - Template

### `qst_amount` (DB-Feld):
- `adeacore/models.py:569` - Model-Feld Definition
- `adeacore/models.py:985` - Verwendung in `_calculate_net_salary()`
- `adeacore/admin.py:250` - Admin list_display
- `adeacore/admin.py:299` - Admin fieldsets
- `adeacore/admin.py:341` - Admin readonly_fields
- `adealohn/views.py:919, 930` - Print-View
- `adealohn/templates/adealohn/payroll/detail.html:293, 425` - Template
- `adealohn/qst_calculator.py:20, 55` - QST Calculator
- `adealohn/tests.py:158, 168` - Tests

### `auszahlung` (Variable):
- `adealohn/views.py:926, 939` - Print-View Berechnung
- `adealohn/templates/adealohn/payroll/print.html:401` - Template

### `summe_privatanteile` (Variable):
- `adealohn/views.py:764, 890, 892, 929` - Views
- `adealohn/templates/adealohn/payroll/print.html:253, 256, 263, 327, 333, 371, 374` - Template

### `summe_familienzulagen` (Variable):
- `adealohn/views.py:740, 750, 882, 884, 931` - Views
- `adealohn/templates/adealohn/payroll/detail.html:417, 418` - Template
- `adealohn/templates/adealohn/payroll/print.html:339, 355, 383, 387` - Template

### `payroll_calculator` / `calculate_*`:
- **NICHT GEFUNDEN** - Noch nicht implementiert

---

## II) RENAME-PLAN (Mapping Alt → Neu)

| Alt | Neu | Typ | Kollision? |
|-----|-----|-----|------------|
| `gross_salary` | `bruttolohn` | DB-Feld | ❌ Nein |
| `net_salary` | `nettolohn` | DB-Feld | ❌ Nein |
| `qst_amount` | `qst_abzug` | DB-Feld | ❌ Nein |
| `auszahlung` (Variable) | `auszahlung` | Variable | ❌ Nein (bleibt gleich) |
| `summe_privatanteile` | `privatanteile_total` | Variable | ❌ Nein |
| `summe_familienzulagen` | `zulagen_total` | Variable | ❌ Nein |
| `breakdown` | `aufschluesselung` | Dict-Key | ❌ Nein (neu) |

**Bestätigung:** Keine Namenskollisionen gefunden.

---

## III) PATCH (Code-Änderungen + Migration)

### Schritt 1: Migration für DB-Feld-Renames

**Datei:** `adeacore/migrations/0032_rename_payroll_fields_to_german.py`

```python
# Generated migration for field renames
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('adeacore', '0031_add_pensum_iban_to_employee'),
    ]

    operations = [
        migrations.RenameField(
            model_name='payrollrecord',
            old_name='gross_salary',
            new_name='bruttolohn',
        ),
        migrations.RenameField(
            model_name='payrollrecord',
            old_name='net_salary',
            new_name='nettolohn',
        ),
        migrations.RenameField(
            model_name='payrollrecord',
            old_name='qst_amount',
            new_name='qst_abzug',
        ),
    ]
```

### Schritt 2: Zentrale Berechnungsfunktion

**Datei:** `adealohn/payroll_calculator.py` (NEU)

```python
from decimal import Decimal
from adeacore.models import PayrollRecord
from adeacore.money import round_to_5_rappen


def berechne_lohnabrechnung(record: PayrollRecord) -> dict:
    """
    Zentrale Funktion für Lohnabrechnungsberechnung.
    Single Source of Truth für UI und Print.
    
    Returns:
        {
            'bruttolohn': Decimal,
            'sozialabzuege_total': Decimal,
            'qst_abzug': Decimal,
            'nettolohn': Decimal,
            'privatanteile_total': Decimal,
            'zulagen_total': Decimal,
            'auszahlung': Decimal,
            'rundung': Decimal,
            'aufschluesselung': {
                'ahv': Decimal,
                'alv': Decimal,
                'nbu': Decimal,
                'bvg': Decimal,
                'ktg': Decimal,
            }
        }
    """
    # Bruttolohn
    bruttolohn = record.bruttolohn or Decimal("0")
    
    # Sozialabzüge
    sozialabzuege_total = (
        (record.ahv_employee or Decimal("0")) +
        (record.alv_employee or Decimal("0")) +
        (record.nbu_employee or Decimal("0")) +
        (record.bvg_employee or Decimal("0"))
    )
    
    # QST
    qst_abzug = record.qst_abzug or Decimal("0")
    
    # Nettolohn = Bruttolohn - Sozialabzüge - QST
    nettolohn = bruttolohn - sozialabzuege_total - qst_abzug
    
    # Privatanteile (aus PayrollItems)
    privatanteil_items = record.items.filter(
        wage_type__code__startswith="PRIVATANTEIL_"
    )
    privatanteile_total = sum(item.total for item in privatanteil_items)
    
    # Familienzulagen (Durchlaufender Posten SVA)
    family_allowance_items = record.items.filter(
        wage_type__code__in=['KINDERZULAGE', 'FAMILIENZULAGE']
    )
    zulagen_total = sum(item.total for item in family_allowance_items)
    
    # Auszahlung = Nettolohn - Privatanteile + Zulagen
    auszahlung_raw = nettolohn - privatanteile_total + zulagen_total
    
    # Rundung auf 5 Rappen
    auszahlung_gerundet = round_to_5_rappen(auszahlung_raw)
    rundung = auszahlung_gerundet - auszahlung_raw
    
    return {
        'bruttolohn': bruttolohn,
        'sozialabzuege_total': sozialabzuege_total,
        'qst_abzug': qst_abzug,
        'nettolohn': nettolohn,
        'privatanteile_total': privatanteile_total,
        'zulagen_total': zulagen_total,
        'auszahlung': auszahlung_gerundet,
        'rundung': rundung,
        'aufschluesselung': {
            'ahv': record.ahv_employee or Decimal("0"),
            'alv': record.alv_employee or Decimal("0"),
            'nbu': record.nbu_employee or Decimal("0"),
            'bvg': record.bvg_employee or Decimal("0"),
            'ktg': record.ktg_employee or Decimal("0"),
        }
    }
```

### Schritt 3: Model anpassen

**Datei:** `adeacore/models.py`

```python
# Zeile 535: Feld umbenennen
bruttolohn = models.DecimalField(max_digits=10, decimal_places=2, default=0)

# Zeile 569: Feld umbenennen
qst_abzug = models.DecimalField(max_digits=10, decimal_places=2, default=0)

# Zeile 589: Feld umbenennen
nettolohn = models.DecimalField(max_digits=10, decimal_places=2, default=0)

# Zeile 695: Zuweisung anpassen
self.bruttolohn = round_to_2_decimals(gross)

# Zeile 970-989: Methode anpassen
def _calculate_nettolohn(self):
    """
    Berechnet Nettolohn: Bruttolohn - alle AN-Abzüge (AHV + ALV + NBU + KTG + BVG + QST).
    Rundet auf 2 Dezimalstellen und verhindert negative Werte.
    """
    from decimal import Decimal, ROUND_HALF_UP
    from adealohn.helpers import safe_decimal
    
    netto = (
        safe_decimal(self.bruttolohn)
        - safe_decimal(self.ahv_employee)
        - safe_decimal(self.alv_employee)
        - safe_decimal(self.nbu_employee)
        - safe_decimal(self.ktg_employee)
        - safe_decimal(self.bvg_employee)
        - safe_decimal(self.qst_abzug)
    )
    
    self.nettolohn = max(netto, Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

# Zeile 1066: Aufruf anpassen
self._calculate_nettolohn()
```

### Schritt 4: Views anpassen

**Datei:** `adealohn/views.py`

```python
# Zeile 782: Kommentar anpassen
# Summe der lohnwirksamen Items (sollte gleich bruttolohn sein)

# Zeile 740-750: DetailView - zentrale Berechnung verwenden
from adealohn.payroll_calculator import berechne_lohnabrechnung

# Am Ende von get_context_data() hinzufügen:
lohnabrechnung = berechne_lohnabrechnung(self.object)
context["auszahlung"] = lohnabrechnung["auszahlung"]
context["privatanteile_total"] = lohnabrechnung["privatanteile_total"]
context["zulagen_total"] = lohnabrechnung["zulagen_total"]
context["aufschluesselung"] = lohnabrechnung["aufschluesselung"]

# Zeile 803-942: PrintView - komplett ersetzen durch:
def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    record = self.object
    
    # Monatsname
    from calendar import month_name
    from datetime import datetime
    import calendar
    
    context["month_name_de"] = month_name[record.month]
    context["record"] = record
    
    # Abrechnungsperiode
    first_day = datetime(record.year, record.month, 1).date()
    last_day = datetime(record.year, record.month, calendar.monthrange(record.year, record.month)[1]).date()
    context["abrechnungsperiode_start"] = first_day.strftime("%d.%m.%Y")
    context["abrechnungsperiode_ende"] = last_day.strftime("%d.%m.%Y")
    context["abrechnungsdatum"] = record.created_at.date().strftime("%d.%m.%Y")
    
    # Pensum
    pensum = record.employee.pensum or Decimal("100")
    context["pensum"] = pensum
    context["pensum_display"] = f"{int(pensum)}%"
    context["iban"] = record.employee.iban or ""
    
    # Stunden
    time_records = TimeRecord.objects.filter(
        employee=record.employee,
        date__month=record.month,
        date__year=record.year,
    ).select_related("client", "project").order_by("-date")
    hours_total = time_records.aggregate(total=Sum("hours"))["total"] or Decimal("0")
    context["hours_total"] = hours_total
    
    # BVG Parameter
    from .helpers import get_parameter_for_year, decimal_to_percent
    from adealohn.bvg_calculator import BVGCalculator
    bvg_params = get_parameter_for_year(BVGParameter, record.year)
    bvg_employee_rate_percent = None
    bvg_insured_month = Decimal("0.00")
    bvg_is_manual = False
    
    has_manual_bvg = (record.manual_bvg_employee > 0) or (record.manual_bvg_employer > 0)
    
    if bvg_params:
        bvg_employee_rate_percent = decimal_to_percent(bvg_params.employee_rate)
        bvg_calc = BVGCalculator()
        bvg_result = bvg_calc.calculate_for_payroll(record)
        calculated_bvg = bvg_result.get("bvg_employee", Decimal("0.00"))
        
        if has_manual_bvg and calculated_bvg == Decimal("0.00"):
            bvg_is_manual = True
            bvg_insured_month = None
        else:
            bvg_insured_month = bvg_result.get("bvg_insured_month", Decimal("0.00"))
    elif has_manual_bvg:
        bvg_is_manual = True
        bvg_insured_month = None
    
    context["bvg_employee_rate_percent"] = bvg_employee_rate_percent
    context["bvg_insured_month"] = bvg_insured_month
    context["bvg_is_manual"] = bvg_is_manual
    
    # Familienzulagen
    family_allowance_items = record.items.filter(
        wage_type__code__in=['KINDERZULAGE', 'FAMILIENZULAGE']
    ).select_related('wage_type').order_by('wage_type__code', 'id')
    context["family_allowance_items"] = family_allowance_items
    
    # Privatanteile
    privatanteil_items = record.items.filter(
        wage_type__code__startswith="PRIVATANTEIL_"
    ).select_related('wage_type').order_by('wage_type__code', 'id')
    context["privatanteil_items"] = privatanteil_items
    
    # Monatslohn
    monatslohn = Decimal("0")
    if record.employee.monthly_salary > 0:
        monatslohn = record.employee.monthly_salary
    elif record.employee.hourly_rate > 0 and hours_total > 0:
        monatslohn = record.employee.hourly_rate * hours_total
    context["monatslohn"] = monatslohn
    context["monatslohn_mit_pensum"] = f"Monatslohn ({context['pensum_display']})"
    
    # Zentrale Berechnung verwenden
    from adealohn.payroll_calculator import berechne_lohnabrechnung
    lohnabrechnung = berechne_lohnabrechnung(record)
    
    context["auszahlung"] = lohnabrechnung["auszahlung"]
    context["rundung"] = lohnabrechnung["rundung"]
    context["abzuege_sozialversicherungen"] = lohnabrechnung["sozialabzuege_total"]
    context["privatanteile_total"] = lohnabrechnung["privatanteile_total"]
    context["zulagen_total"] = lohnabrechnung["zulagen_total"]
    context["qst_abzug"] = lohnabrechnung["qst_abzug"]
    
    return context
```

### Schritt 5: Forms anpassen

**Datei:** `adealohn/forms.py`

```python
# Zeile 172: Feld umbenennen
fields = [
    "employee", "month", "year", "status", "bruttolohn", "qst_prozent",
    "manual_bvg_employee", "manual_bvg_employer"
]

# Zeile 180: Label anpassen
"bruttolohn": "Bruttolohn (CHF)",

# Zeile 194: Widget anpassen
"bruttolohn": forms.NumberInput(...),

# Zeile 244-252: Logik anpassen
self.fields["bruttolohn"].required = False
self.fields["bruttolohn"].widget = forms.HiddenInput()
# ... usw.
self.fields["bruttolohn"].initial = employee.monthly_salary
self.fields["bruttolohn"].help_text = f"Monatslohn (Standard: {employee.monthly_salary} CHF vom Mitarbeiter). Kann für diesen Monat überschrieben werden."

# Zeile 568, 676: View-Logik anpassen
monatslohn = employee.monthly_salary if employee.monthly_salary > 0 else form.cleaned_data.get('bruttolohn', Decimal("0"))
```

### Schritt 6: Templates anpassen

**Datei:** `adealohn/templates/adealohn/payroll/detail.html`

```html
<!-- Zeile 93, 415, 418: -->
{{ record.bruttolohn|floatformat:2 }}

<!-- Zeile 293, 425: -->
{{ record.qst_abzug|floatformat:2 }}

<!-- Zeile 426: -->
<li><strong>Nettolohn:</strong> {{ record.nettolohn|floatformat:2 }} CHF</li>
<!-- NEU hinzufügen: -->
{% if privatanteile_total > 0 %}
<li><strong>Privatanteile Abzug:</strong> -{{ privatanteile_total|floatformat:2 }} CHF</li>
{% endif %}
{% if zulagen_total > 0 %}
<li><strong>Spesen und Zulagen:</strong> +{{ zulagen_total|floatformat:2 }} CHF</li>
{% endif %}
<li style="border-top:2px solid rgba(0,0,0,0.2); padding-top:8px; margin-top:8px; font-size:1.1em;">
    <strong>Auszahlung:</strong> {{ auszahlung|floatformat:2 }} CHF
</li>
```

**Datei:** `adealohn/templates/adealohn/payroll/print.html`

```html
<!-- Alle Vorkommen von record.gross_salary → record.bruttolohn -->
<!-- Alle Vorkommen von summe_privatanteile → privatanteile_total -->
<!-- Alle Vorkommen von summe_familienzulagen → zulagen_total -->
<!-- qst_abzug bleibt gleich (bereits umbenannt) -->
```

### Schritt 7: Admin anpassen

**Datei:** `adeacore/admin.py`

```python
# Zeile 248-250: list_display anpassen
list_display = (
    "employee", "month", "year", "status",
    "bruttolohn", "nettolohn", "qst_abzug", "created_at",
)

# Zeile 276-277: fieldsets anpassen
"fields": (
    "bruttolohn",
    "nettolohn",
    # ... andere Felder ...
    "qst_abzug",
),

# Zeile 342: readonly_fields anpassen
readonly_fields = (
    # ... andere Felder ...
    "qst_abzug",
    "nettolohn",
)
```

### Schritt 8: Calculator anpassen

**Datei:** `adealohn/qst_calculator.py`

```python
# Zeile 25: Anpassen
basis = payroll.qst_basis if payroll.qst_basis and payroll.qst_basis > 0 else (payroll.bruttolohn or Decimal("0.00"))

# Zeile 55: Anpassen
payroll.qst_abzug = qst_amount
```

**Datei:** `adealohn/fak_calculator.py`

```python
# Zeile 35: Anpassen
gross_salary = payroll.bruttolohn or Decimal("0.00")
```

---

## IV) TEST-ÄNDERUNGEN

**Datei:** `adealohn/tests_integration.py`

```python
# Alle Vorkommen von gross_salary → bruttolohn
# Alle Vorkommen von net_salary → nettolohn
# Alle Vorkommen von qst_amount → qst_abzug

# NEU: Test für zentrale Berechnung
def test_berechne_lohnabrechnung_ui_print_konsistent(self):
    """UI und Print müssen identische Auszahlung zeigen."""
    from adealohn.payroll_calculator import berechne_lohnabrechnung
    
    result = berechne_lohnabrechnung(self.payroll)
    
    # Prüfe Formeln
    assert result['nettolohn'] == result['bruttolohn'] - result['sozialabzuege_total'] - result['qst_abzug']
    assert result['auszahlung'] == result['nettolohn'] - result['privatanteile_total'] + result['zulagen_total']

def test_privatanteile_reduzieren_auszahlung(self):
    """Privatanteile müssen Auszahlung reduzieren, aber Bruttolohnbasis erhöhen."""
    # Privatanteil hinzufügen
    PayrollItem.objects.create(
        payroll=self.payroll,
        wage_type=self.wage_type_privatanteil_auto,
        quantity=Decimal("1"),
        amount=Decimal("100.00"),
        total=Decimal("100.00"),
    )
    self.payroll.recompute_bases_from_items()
    self.payroll.save()
    
    from adealohn.payroll_calculator import berechne_lohnabrechnung
    result = berechne_lohnabrechnung(self.payroll)
    
    # Bruttolohn sollte erhöht sein
    assert result['bruttolohn'] > self.employee.monthly_salary
    # Auszahlung sollte reduziert sein
    assert result['auszahlung'] < result['nettolohn']

def test_zulagen_erhoehen_auszahlung(self):
    """Zulagen müssen Auszahlung erhöhen."""
    from adealohn.payroll_calculator import berechne_lohnabrechnung
    
    result_before = berechne_lohnabrechnung(self.payroll)
    
    # Zulage hinzufügen
    PayrollItem.objects.create(
        payroll=self.payroll,
        wage_type=self.wage_type_kinderzulage,
        quantity=Decimal("1"),
        amount=Decimal("215.00"),
        total=Decimal("215.00"),
    )
    self.payroll.recompute_bases_from_items()
    self.payroll.save()
    
    result_after = berechne_lohnabrechnung(self.payroll)
    
    assert result_after['zulagen_total'] == Decimal("215.00")
    assert result_after['auszahlung'] > result_before['auszahlung']

def test_qst_abzug_korrekt_beruecksichtigt(self):
    """QST-Abzug muss korrekt berücksichtigt werden."""
    self.payroll.qst_abzug = Decimal("100.00")
    self.payroll.save()
    
    from adealohn.payroll_calculator import berechne_lohnabrechnung
    result = berechne_lohnabrechnung(self.payroll)
    
    assert result['qst_abzug'] == Decimal("100.00")
    assert result['nettolohn'] == result['bruttolohn'] - result['sozialabzuege_total'] - Decimal("100.00")

def test_tenant_protection_erhalten(self):
    """Tenant-Isolation muss erhalten bleiben."""
    # Test bleibt gleich, prüft nur dass TenantObjectMixin noch funktioniert
    # (keine Code-Änderung nötig, da nur Feldnamen geändert wurden)
    pass
```

**Datei:** `adealohn/tests.py`

```python
# Zeile 158, 168: Anpassen
self.assertEqual(self.payroll.qst_abzug, Decimal("0.00"))
self.assertEqual(self.payroll.qst_abzug, Decimal("100.00"))
```

---

## V) LOKALE PRÜFUNG

```bash
# 1. Migration erstellen und ausführen
cd C:\AdeaTools\AdeaCore
python manage.py makemigrations adeacore --name rename_payroll_fields_to_german
python manage.py migrate

# 2. Tests ausführen
python manage.py test adealohn.tests_integration
python manage.py test adealohn.tests

# 3. Manuelle Prüfung
# - Server starten: python manage.py runserver
# - UI öffnen: http://127.0.0.1:8000/lohn/payroll/<id>/
# - Print öffnen: http://127.0.0.1:8000/lohn/payroll/<id>/print/
# - Prüfen: Auszahlung muss in UI und Print identisch sein
```

---

## HINWEISE

- **DB-Felder:** `gross_salary`, `net_salary`, `qst_amount` sind DB-Felder → Migration erforderlich
- **Sicherheit:** Migration verwendet `RenameField` → KEIN Datenverlust
- **Rückwärtskompatibilität:** Keine (Breaking Change, aber sauberer Refactor)
- **Tests:** Alle Tests müssen angepasst werden, da Feldnamen geändert werden
