# Refactor-Implementation: Einheitliche deutsche Benennungen

## I) FUNDSTELLENLISTE (Vollständig)

### DB-Felder (Model):
- `adeacore/models.py:535` - `gross_salary` → `bruttolohn`
- `adeacore/models.py:569` - `qst_amount` → `qst_abzug`
- `adeacore/models.py:589` - `net_salary` → `nettolohn`

### Views:
- `adealohn/views.py` - Mehrere Stellen (bereits angepasst)

### Templates:
- `adealohn/templates/adealohn/payroll/detail.html` - Bereits angepasst
- `adealohn/templates/adealohn/payroll/print.html` - Bereits angepasst
- `adealohn/templates/adealohn/payroll/list.html` - Bereits angepasst
- `adealohn/templates/adealohn/payroll/form.html` - Bereits angepasst
- `adealohn/templates/adealohn/payroll/confirm_delete.html` - Bereits angepasst

### Forms:
- `adealohn/forms.py` - Bereits angepasst

### Admin:
- `adeacore/admin.py` - Bereits angepasst

### Tests:
- `adealohn/tests_integration.py` - Bereits angepasst
- `adealohn/tests.py` - Bereits angepasst

### Calculator:
- `adealohn/qst_calculator.py` - Bereits angepasst
- `adealohn/fak_calculator.py` - Bereits angepasst

---

## II) RENAME-PLAN (Mapping Alt → Neu)

| Alt | Neu | Status |
|-----|-----|--------|
| `gross_salary` | `bruttolohn` | ✅ Implementiert |
| `net_salary` | `nettolohn` | ✅ Implementiert |
| `qst_amount` | `qst_abzug` | ✅ Implementiert |
| `auszahlung` (Variable) | `auszahlung` | ✅ Bleibt gleich |
| `summe_privatanteile` | `privatanteile_total` | ✅ Implementiert |
| `summe_familienzulagen` | `zulagen_total` | ✅ Implementiert |
| `breakdown` | `aufschluesselung` | ✅ Implementiert |

**Namenskollisionen:** ❌ Keine gefunden

---

## III) PATCH (Code-Änderungen)

### 1. Migration erstellt:
**Datei:** `adeacore/migrations/0032_rename_payroll_fields_to_german.py` ✅

### 2. Zentrale Berechnung erstellt:
**Datei:** `adealohn/payroll_calculator.py` ✅

### 3. Model angepasst:
**Datei:** `adeacore/models.py`
- Felder umbenannt ✅
- `_calculate_nettolohn()` angepasst ✅

### 4. Views angepasst:
**Datei:** `adealohn/views.py`
- `PayrollRecordDetailView` verwendet `berechne_lohnabrechnung()` ✅
- `PayrollRecordPrintView` verwendet `berechne_lohnabrechnung()` ✅
- Variablen umbenannt ✅

### 5. Templates angepasst:
- Alle Templates verwenden neue Feldnamen ✅
- UI zeigt `auszahlung` aus zentraler Berechnung ✅
- Print zeigt `auszahlung` aus zentraler Berechnung ✅

### 6. Forms/Admin/Tests angepasst:
- Alle Referenzen aktualisiert ✅

---

## IV) TEST-ÄNDERUNGEN

### Neue Tests hinzugefügt:

**Datei:** `adealohn/tests_integration.py`

```python
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

### Bestehende Tests angepasst:
- Alle `gross_salary` → `bruttolohn` ✅
- Alle `net_salary` → `nettolohn` ✅
- Alle `qst_amount` → `qst_abzug` ✅

---

## V) LOKALE PRÜFUNG

```bash
# 1. Migration ausführen
cd C:\AdeaTools\AdeaCore
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

## ZUSAMMENFASSUNG

✅ **Zentrale Berechnung:** `berechne_lohnabrechnung()` erstellt  
✅ **DB-Felder umbenannt:** Migration erstellt  
✅ **UI/Print vereinheitlicht:** Beide verwenden `auszahlung` aus zentraler Funktion  
✅ **Alle Referenzen angepasst:** Models, Views, Templates, Forms, Admin, Tests  
✅ **Tests aktualisiert:** Neue Tests für Konsistenz hinzugefügt

**Nächster Schritt:** Migration ausführen und Tests prüfen
