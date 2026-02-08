# Code-Audit: AdeaLohn-Modul

**Datum:** 2025-01-XX  
**Auditor:** Lead Senior Engineer  
**Modul:** `adealohn`  
**Scope:** Vollständiges Code-Audit gemäss DRY, KISS, YAGNI, Performance, Security, Maintainability

---

## 1. DRY-AUDIT (Don't Repeat Yourself)

### 1.1 Top 15 Duplikat-Gruppen

#### 1.1.1 Parameter-Abfrage Pattern (15 Vorkommen)
**Problem:** Wiederholtes Pattern `.filter(year=payroll.year).first()` mit Fallback-Logik.

**Vorkommen:**
- `views.py:101, 112, 125, 127, 136, 143, 154, 785`
- `ahv_calculator.py:29`
- `alv_calculator.py:22`
- `ktg_calculator.py:16`
- `vk_calculator.py:29`
- `uvg_calculator.py:18`
- `bvg_calculator.py:16`

**Lösung:** Zentraler Helper `get_parameter_for_year(model_class, year, **filters)` mit Fallback.

**Impact:** Hoch (15 Call-Sites, zentrale Business-Logik)

---

#### 1.1.2 Prozent/Dezimal-Konvertierung (14 Vorkommen)
**Problem:** Wiederholte Konvertierung zwischen Prozent (5.3) und Dezimal (0.053).

**Vorkommen:**
- `views.py:103-104, 114-115, 130, 138, 145-146, 156-157, 182-183, 192-193, 204, 212, 220-221, 230-231, 828-829`
- `qst_calculator.py:35, 48`

**Lösung:** Helper `percent_to_decimal(value)` und `decimal_to_percent(value)`.

**Impact:** Mittel (14 Call-Sites, aber einfache Konvertierung)

---

#### 1.1.3 WageType.get_or_create Pattern (11 Vorkommen)
**Problem:** Wiederholtes `WageType.objects.get_or_create(code=..., defaults={...})` mit identischen Defaults.

**Vorkommen:**
- `views.py:443, 532, 556, 585, 664, 694, 730`
- `migrations/0001_initial.py:20`
- `migrations/0006_add_family_allowance_wage_types.py:49`
- `migrations/0007_add_spesen_wage_types.py:60`
- `migrations/0008_add_privatanteil_wage_types.py:43`

**Lösung:** Helper `ensure_wage_type(code, name, **overrides)` (bereits vorhanden, aber nur 1x verwendet).

**Impact:** Hoch (11 Call-Sites, zentrale Datenstruktur)

---

#### 1.1.4 Client-Filter Pattern (11 Vorkommen)
**Problem:** Wiederholtes `Client.objects.filter(client_type="FIRMA", lohn_aktiv=True)`.

**Vorkommen:**
- `views.py:57, 270, 292, 300, 340, 344, 484, 629`
- `mixins.py:91, 94`
- `tests.py:19, 175, 242, 243, 247, 481, 483`

**Lösung:** Manager-Methode `Client.firma_with_lohn_aktiv()` oder Helper `get_firma_clients()`.

**Impact:** Mittel (11 Call-Sites, aber einfache Filter)

---

#### 1.1.5 YTD-Basis-Abfrage Pattern (9 Vorkommen)
**Problem:** Wiederholtes `getattr(employee, "ytd_basis", Decimal("0.00")) or Decimal("0.00")`.

**Vorkommen:**
- `alv_calculator.py:47`
- `uvg_calculator.py:32`
- `bvg_calculator.py:29, 49`
- `models.py:806, 807`
- `views.py:787`

**Lösung:** Helper `get_ytd_basis(employee, field_name)` oder Property auf Employee.

**Impact:** Mittel (9 Call-Sites, aber einfache Abfrage)

---

#### 1.1.6 "or Decimal('0.00')" Fallback Pattern (18 Vorkommen)
**Problem:** Wiederholtes `value or Decimal("0.00")` für Null-Safety.

**Vorkommen:**
- `views.py:321, 440, 519, 652, 784, 787`
- `alv_calculator.py:34, 47`
- `ktg_calculator.py:25`
- `vk_calculator.py:38`
- `fak_calculator.py:35`
- `qst_calculator.py:25`
- `uvg_calculator.py:28, 32`
- `bvg_calculator.py:25, 29, 49`

**Lösung:** Helper `safe_decimal(value, default=Decimal("0.00"))`.

**Impact:** Niedrig (18 Call-Sites, aber sehr einfache Logik)

---

#### 1.1.7 WageType-Code-Filter Pattern (12 Vorkommen)
**Problem:** Wiederholtes Filtern nach `wage_type__code__in=[...]` oder `wage_type__code__startswith=...`.

**Vorkommen:**
- `views.py:792, 819`
- `forms.py:257, 286, 315, 353-354, 356, 358, 360`
- `admin.py:57`
- `migrations/0006_add_family_allowance_wage_types.py:70`

**Lösung:** Helper `filter_wage_types_by_code(queryset, excluded_codes, excluded_prefixes)`.

**Impact:** Mittel (12 Call-Sites, aber einfache Filter)

---

#### 1.1.8 Parameter-Update-or-Create Pattern (6 Vorkommen)
**Problem:** Wiederholtes `Parameter.objects.update_or_create(year=..., defaults={...})` mit Prozent-Konvertierung.

**Vorkommen:**
- `views.py:179, 189, 200, 209, 217, 227`

**Lösung:** Helper `save_parameter_for_year(model_class, year, form_data, **filters)`.

**Impact:** Mittel (6 Call-Sites, aber zentrale Logik)

---

#### 1.1.9 Grundlohn-WageType-Erstellung (4 Vorkommen)
**Problem:** Identische `WageType.objects.get_or_create(code="GRUNDLOHN_STUNDEN", defaults={...})` Logik.

**Vorkommen:**
- `views.py:532-544, 585-597, 664-676, 730-742`

**Lösung:** Helper `ensure_grundlohn_wage_type(code, employee_type)`.

**Impact:** Mittel (4 Call-Sites, aber identische Logik)

---

#### 1.1.10 Ferienentschädigung-WageType-Erstellung (2 Vorkommen)
**Problem:** Identische `WageType.objects.get_or_create(code="FERIENENTSCHAEDIGUNG", defaults={...})` Logik.

**Vorkommen:**
- `views.py:556-568, 694-706`

**Lösung:** Helper `ensure_ferien_wage_type()`.

**Impact:** Niedrig (2 Call-Sites, aber identische Logik)

---

#### 1.1.11 TimeRecord-Hours-Aggregation (3 Vorkommen)
**Problem:** Wiederholtes `TimeRecord.objects.filter(...).aggregate(total=Sum("hours"))["total"] or Decimal("0")`.

**Vorkommen:**
- `views.py:321, 439, 784`

**Lösung:** Helper `get_hours_total(employee, month, year)` (bereits vorhanden, aber nicht überall verwendet).

**Impact:** Niedrig (3 Call-Sites, aber bereits Helper vorhanden)

---

#### 1.1.12 Employee-Client-Filter (8 Vorkommen)
**Problem:** Wiederholtes `Employee.objects.filter(client=current_client)`.

**Vorkommen:**
- `views.py:407, 485, 506, 630`
- `mixins.py:91`
- `forms.py:293, 341`

**Lösung:** Manager-Methode `Employee.for_client(client)` oder Helper.

**Impact:** Niedrig (8 Call-Sites, aber einfache Filter)

---

#### 1.1.13 PayrollItem-Summen-Berechnung (2 Vorkommen)
**Problem:** Wiederholtes `sum(item.total for item in items)` in Python statt DB-Aggregation.

**Vorkommen:**
- `views.py:805, 822`

**Lösung:** `items.aggregate(total=Sum(F('quantity') * F('amount')))`.

**Impact:** Niedrig (2 Call-Sites, aber Performance-Optimierung möglich)

---

#### 1.1.14 getattr-Safety-Pattern (10 Vorkommen)
**Problem:** Wiederholtes `getattr(obj, "attr", default)` für Null-Safety.

**Vorkommen:**
- `alv_calculator.py:35-36`
- `fak_calculator.py:42`
- `qst_calculator.py:16, 19`
- `uvg_calculator.py:29, 32, 53`
- `mixins.py:42, 65, 90, 93, 115, 119`
- `bvg_calculator.py:26, 29, 49`

**Lösung:** Helper `safe_getattr(obj, attr, default)` oder Property-Methoden.

**Impact:** Niedrig (10 Call-Sites, aber einfache Logik)

---

#### 1.1.15 Fallback-Standardwerte für Parameter (7 Vorkommen)
**Problem:** Wiederholte Fallback-Logik für Parameter (z.B. `rate_employee = Decimal("0.053")`).

**Vorkommen:**
- `ahv_calculator.py:33-34`
- `alv_calculator.py:26-27`
- `ktg_calculator.py:18-19`
- `vk_calculator.py:32-33`
- `fak_calculator.py:15, 50`
- `qst_calculator.py:24`
- `vacation_calculator.py:30`

**Lösung:** Zentraler Helper `get_parameter_with_fallback(model_class, year, defaults, **filters)`.

**Impact:** Mittel (7 Call-Sites, aber zentrale Business-Logik)

---

### 1.2 Zusammenfassung DRY-Audit

**Gesamt-Duplikate:** 15 Gruppen mit 145+ Vorkommen  
**Priorität Hoch:** 3 Gruppen (Parameter-Abfrage, WageType-Erstellung, Prozent-Konvertierung)  
**Priorität Mittel:** 7 Gruppen  
**Priorität Niedrig:** 5 Gruppen

**Empfehlung:** Fokus auf Top 3 (Parameter-Abfrage, WageType-Erstellung, Prozent-Konvertierung) für maximalen ROI.

---

## 2. KISS-AUDIT (Keep It Simple, Stupid)

### 2.1 Komplexitäts-Hotspots

#### 2.1.1 PayrollRecord.save() - Sehr Komplex (200+ Zeilen)
**Datei:** `adeacore/models.py:667-890`

**Probleme:**
- 200+ Zeilen in einer Methode
- 8 Calculator-Aufrufe in sequenzieller Reihenfolge
- Komplexe QST-Basis-Berechnung inline (50+ Zeilen)
- YTD-Reset-Logik inline
- YTD-Update-Logik inline
- Verschachtelte try/except-Blöcke

**Komplexitäts-Metriken:**
- Cyclomatic Complexity: ~25
- Zeilen: 223
- Verschachtelungstiefe: 4

**Lösung:**
1. Extrahiere Calculator-Aufrufe in `_calculate_all_contributions()`
2. Extrahiere QST-Basis-Berechnung in `_calculate_qst_basis()`
3. Extrahiere YTD-Logik in `_handle_ytd_updates()`
4. Verwende `@transaction.atomic` nur für kritische Abschnitte

**Impact:** Hoch (zentrale Business-Logik, schwer testbar)

---

#### 2.1.2 PayrollRecordCreateView.form_valid() - Komplex (100+ Zeilen)
**Datei:** `adealohn/views.py:512-615`

**Probleme:**
- 100+ Zeilen in einer Methode
- Verschachtelte if/else für Stundenlohn vs. Monatslohn
- WageType-Erstellung inline
- Ferienentschädigung-Berechnung inline
- Viele verschachtelte Bedingungen

**Komplexitäts-Metriken:**
- Cyclomatic Complexity: ~12
- Zeilen: 103
- Verschachtelungstiefe: 3

**Lösung:**
1. Extrahiere Stundenlohn-Logik in `_create_hourly_payroll_items()`
2. Extrahiere Monatslohn-Logik in `_create_monthly_payroll_items()`
3. Extrahiere Ferienentschädigung in `_create_vacation_allowance_item()`

**Impact:** Mittel (häufig aufgerufen, aber nicht kritisch)

---

#### 2.1.3 PayrollRecordUpdateView.form_valid() - Komplex (120+ Zeilen)
**Datei:** `adealohn/views.py:645-765`

**Probleme:**
- 120+ Zeilen in einer Methode
- Duplizierte Logik aus CreateView
- Komplexe Update-Logik für bestehende Items
- Verschachtelte Bedingungen

**Komplexitäts-Metriken:**
- Cyclomatic Complexity: ~15
- Zeilen: 120
- Verschachtelungstiefe: 3

**Lösung:**
1. Nutze gemeinsame Helper aus CreateView
2. Extrahiere Update-Logik in `_update_or_create_payroll_items()`

**Impact:** Mittel (häufig aufgerufen, aber nicht kritisch)

---

#### 2.1.4 PayrollItemGeneralForm.__init__() - Komplex (30+ Zeilen)
**Datei:** `adealohn/forms.py:349-365`

**Probleme:**
- Komplexe WageType-Filter-Logik inline
- Mehrfache `.exclude()`-Aufrufe
- Hardcoded Code-Listen

**Komplexitäts-Metriken:**
- Cyclomatic Complexity: ~5
- Zeilen: 16
- Verschachtelungstiefe: 2

**Lösung:**
1. Extrahiere Filter-Logik in `get_available_wage_types()`
2. Verwende Konstante für excluded_codes

**Impact:** Niedrig (einfache Logik, aber könnte klarer sein)

---

#### 2.1.5 InsuranceRatesView.get_initial() - Komplex (60+ Zeilen)
**Datei:** `adealohn/views.py:93-165`

**Probleme:**
- 60+ Zeilen für Initial-Werte
- Wiederholte Parameter-Abfrage mit Fallback
- Prozent-Konvertierung inline

**Komplexitäts-Metriken:**
- Cyclomatic Complexity: ~8
- Zeilen: 72
- Verschachtelungstiefe: 2

**Lösung:**
1. Nutze zentralen Parameter-Helper
2. Nutze Prozent-Konvertierungs-Helper

**Impact:** Niedrig (einfache Logik, aber viele Duplikate)

---

#### 2.1.6 QST-Basis-Berechnung inline - Sehr Komplex (60+ Zeilen)
**Datei:** `adeacore/models.py:776-844`

**Probleme:**
- 60+ Zeilen inline in `save()`
- Komplexe Berechnung mit vielen Zwischenschritten
- Verschachtelte Bedingungen
- Hardcoded Logik

**Komplexitäts-Metriken:**
- Cyclomatic Complexity: ~10
- Zeilen: 68
- Verschachtelungstiefe: 3

**Lösung:**
1. Extrahiere in `_calculate_qst_basis()`
2. Verwende Calculator-Pattern (wie bei anderen Beiträgen)

**Impact:** Hoch (zentrale Business-Logik, schwer testbar)

---

### 2.2 Zusammenfassung KISS-Audit

**Komplexitäts-Hotspots:** 6 Methoden  
**Sehr Komplex (>100 Zeilen):** 3 Methoden  
**Mittel Komplex (50-100 Zeilen):** 2 Methoden  
**Niedrig Komplex (<50 Zeilen):** 1 Methode

**Empfehlung:** Fokus auf `PayrollRecord.save()` und QST-Basis-Berechnung für maximalen ROI.

---

## 3. YAGNI-AUDIT (You Ain't Gonna Need It)

### 3.1 Toter/Unbenutzter Code

#### 3.1.1 permissions.py - Fast Leer
**Datei:** `adealohn/permissions.py`

**Problem:**
- Nur eine Funktion `can_access_adelohn(user)`, die nur `is_staff` prüft
- Keine granularen Berechtigungen
- Kommentar sagt "Kann später erweitert werden" (YAGNI-Violation)

**Lösung:**
- Entweder entfernen (wenn nicht verwendet) oder erweitern (wenn benötigt)
- Aktuell: Nur `LoginRequiredMixin` wird verwendet, keine custom permissions

**Impact:** Niedrig (kleine Datei, aber zeigt YAGNI-Violation)

---

#### 3.1.2 ensure_wage_type() - Nur 1x Verwendet
**Datei:** `adealohn/views.py:442-457`

**Problem:**
- Helper-Methode wird nur 1x verwendet (in `PayrollRecordMixin`)
- Könnte inline sein

**Lösung:**
- Entweder entfernen und inline verwenden, oder mehrfach verwenden (DRY)

**Impact:** Niedrig (kleine Methode, aber zeigt YAGNI-Violation)

---

#### 3.1.3 get_hours_total() - Nicht Überall Verwendet
**Datei:** `adealohn/views.py:432-440`

**Problem:**
- Helper-Methode existiert, aber wird nicht überall verwendet
- 3 Vorkommen von `TimeRecord.objects.filter(...).aggregate(total=Sum("hours"))` direkt

**Lösung:**
- Konsistent verwenden oder entfernen

**Impact:** Niedrig (kleine Methode, aber zeigt DRY-Violation)

---

#### 3.1.4 WageTypeCategory - Nicht Vollständig Genutzt
**Datei:** `adealohn/models.py:8-12`

**Problem:**
- Enum definiert, aber nicht überall verwendet
- Hardcoded Strings in einigen Stellen

**Lösung:**
- Konsistent verwenden oder entfernen

**Impact:** Niedrig (kleine Enum, aber zeigt Inkonsistenz)

---

### 3.2 Zusammenfassung YAGNI-Audit

**Toter Code:** 4 Stellen  
**Unbenutzter Code:** 2 Stellen  
**Inkonsistenter Code:** 2 Stellen

**Empfehlung:** Fokus auf `permissions.py` und `ensure_wage_type()` für Klarheit.

---

## 4. PERFORMANCE-AUDIT

### 4.1 N+1 Query-Probleme

#### 4.1.1 PayrollRecordDetailView - Items Mehrfach Geladen
**Datei:** `adealohn/views.py:773-834`

**Probleme:**
- `self.object.items.filter(...)` wird 2x aufgerufen (Zeilen 791, 818)
- Keine `prefetch_related` für `wage_type`
- `sum(item.total for item in items)` in Python statt DB-Aggregation

**Lösung:**
```python
def get_queryset(self):
    return super().get_queryset().prefetch_related(
        'items__wage_type',
        'employee__client'
    )
```

**Impact:** Mittel (DetailView wird häufig aufgerufen)

---

#### 4.1.2 PayrollRecordListView - Keine Optimierung
**Datei:** `adealohn/views.py:361-426`

**Probleme:**
- `select_related("employee", "employee__client")` vorhanden, aber keine `prefetch_related` für Items
- `years` Query könnte gecacht werden

**Lösung:**
- `prefetch_related('items__wage_type')` hinzufügen (falls Items in Template angezeigt werden)
- Caching für `years` Query

**Impact:** Niedrig (ListView wird seltener aufgerufen)

---

#### 4.1.3 Parameter-Abfragen - Keine Caching
**Datei:** Verschiedene Calculator-Dateien

**Probleme:**
- `.filter(year=...).first()` wird bei jedem PayrollRecord-Save aufgerufen (8x pro Save)
- Keine Caching-Mechanismus

**Lösung:**
- `@lru_cache` für Parameter-Abfragen (mit Jahr als Key)
- Oder `select_related` wenn möglich

**Impact:** Hoch (wird sehr häufig aufgerufen)

---

### 4.2 Ineffiziente Queries

#### 4.2.1 Python-Summen statt DB-Aggregation
**Datei:** `adealohn/views.py:805, 822`

**Probleme:**
- `sum(item.total for item in items)` lädt alle Items in Python
- Sollte `items.aggregate(total=Sum(F('quantity') * F('amount')))` verwenden

**Lösung:**
- DB-Aggregation verwenden

**Impact:** Niedrig (kleine Datenmengen, aber schlechte Praxis)

---

#### 4.2.2 .first() ohne Index
**Datei:** Verschiedene Calculator-Dateien

**Probleme:**
- `.filter(year=...).first()` ohne Index auf `year`
- Könnte langsam sein bei vielen Parametern

**Lösung:**
- Index auf `year` Feld hinzufügen (Migration)

**Impact:** Mittel (wird sehr häufig aufgerufen)

---

### 4.3 Zusammenfassung Performance-Audit

**N+1 Probleme:** 2 Stellen  
**Ineffiziente Queries:** 2 Stellen  
**Fehlende Indizes:** 1 Stelle  
**Fehlendes Caching:** 1 Stelle

**Empfehlung:** Fokus auf Parameter-Caching und N+1-Fixes für maximalen ROI.

---

## 5. SECURITY-AUDIT

### 5.1 Berechtigungen

#### 5.1.1 permissions.py - Zu Einfach
**Datei:** `adealohn/permissions.py`

**Probleme:**
- Nur `is_staff`-Prüfung
- Keine granularen Berechtigungen
- Keine Tenant-Isolation auf Permission-Ebene

**Lösung:**
- Django Permissions verwenden
- Tenant-Isolation sicherstellen

**Impact:** Mittel (aktuell ausreichend, aber nicht skalierbar)

---

#### 5.1.2 TenantMixin - Korrekt Implementiert
**Datei:** `adealohn/mixins.py:51-118`

**Status:** ✅ Korrekt
- Tenant-Isolation über `get_current_client()`
- Queryset-Filterung
- Object-Level-Checks

---

### 5.2 Datenvalidierung

#### 5.2.1 PayrollRecord.save() - Try/Except zu Breit
**Datei:** `adeacore/models.py:667-890`

**Probleme:**
- Große try/except-Blöcke
- `ValidationError` wird geworfen, aber Details könnten sensibel sein

**Lösung:**
- Spezifischere Exceptions
- Keine sensiblen Daten in Error-Messages

**Impact:** Niedrig (aktuell ausreichend)

---

### 5.3 Zusammenfassung Security-Audit

**Berechtigungen:** 1 Verbesserungspotenzial  
**Datenvalidierung:** 1 Verbesserungspotenzial  
**Tenant-Isolation:** ✅ Korrekt

**Empfehlung:** Fokus auf granulare Berechtigungen für Skalierbarkeit.

---

## 6. MAINTAINABILITY-AUDIT

### 6.1 Code-Organisation

#### 6.1.1 Calculator-Klassen - Inkonsistent
**Datei:** Verschiedene Calculator-Dateien

**Probleme:**
- `AHVCalculator` verwendet `@classmethod`
- `ALVCalculator` verwendet Instanz-Methode
- Inkonsistente Patterns

**Lösung:**
- Einheitliches Pattern (empfohlen: `@classmethod`)

**Impact:** Niedrig (funktioniert, aber inkonsistent)

---

#### 6.1.2 Imports - Teilweise Chaotisch
**Datei:** Verschiedene Dateien

**Probleme:**
- Teilweise Imports in Methoden (z.B. `PayrollRecord.save()`)
- Teilweise Imports am Anfang

**Lösung:**
- Konsistente Import-Organisation
- Alle Imports am Anfang (außer bei Circular Imports)

**Impact:** Niedrig (funktioniert, aber inkonsistent)

---

### 6.2 Dokumentation

#### 6.2.1 Docstrings - Teilweise Fehlend
**Datei:** Verschiedene Dateien

**Probleme:**
- Viele Methoden ohne Docstrings
- Teilweise unklare Methodennamen

**Lösung:**
- Docstrings für alle öffentlichen Methoden
- Klarere Methodennamen

**Impact:** Niedrig (funktioniert, aber schwerer wartbar)

---

### 6.3 Zusammenfassung Maintainability-Audit

**Code-Organisation:** 2 Verbesserungspotenziale  
**Dokumentation:** 1 Verbesserungspotenzial

**Empfehlung:** Fokus auf einheitliche Calculator-Patterns für Konsistenz.

---

## 7. PRIORISIERTE EMPFEHLUNGEN

### 7.1 Hoch-Priorität (Sofort)

1. **Parameter-Abfrage zentralisieren** (DRY, Performance)
   - Helper `get_parameter_for_year()` mit Caching
   - Impact: 15 Call-Sites, sehr häufig aufgerufen

2. **PayrollRecord.save() refactoren** (KISS, Maintainability)
   - Extrahiere Calculator-Aufrufe, QST-Basis, YTD-Logik
   - Impact: Zentrale Business-Logik, schwer testbar

3. **Prozent/Dezimal-Konvertierung zentralisieren** (DRY)
   - Helper `percent_to_decimal()` und `decimal_to_percent()`
   - Impact: 14 Call-Sites, einfache Konvertierung

---

### 7.2 Mittel-Priorität (Bald)

4. **WageType-Erstellung zentralisieren** (DRY)
   - Helper `ensure_wage_type()` konsistent verwenden
   - Impact: 11 Call-Sites, zentrale Datenstruktur

5. **N+1 Query-Fixes** (Performance)
   - `prefetch_related` in DetailView
   - Impact: Häufig aufgerufene Views

6. **QST-Basis-Berechnung extrahieren** (KISS)
   - Eigene Methode `_calculate_qst_basis()`
   - Impact: Zentrale Business-Logik

---

### 7.3 Niedrig-Priorität (Später)

7. **Client-Filter zentralisieren** (DRY)
   - Manager-Methode `Client.firma_with_lohn_aktiv()`
   - Impact: 11 Call-Sites, aber einfache Filter

8. **YTD-Basis-Abfrage zentralisieren** (DRY)
   - Helper `get_ytd_basis()`
   - Impact: 9 Call-Sites, aber einfache Abfrage

9. **Python-Summen durch DB-Aggregation ersetzen** (Performance)
   - `aggregate(Sum(...))` statt `sum(...)`
   - Impact: Kleine Datenmengen, aber bessere Praxis

---

## 8. ZUSAMMENFASSUNG

**Gesamt-Probleme:** 45+  
**Hoch-Priorität:** 3  
**Mittel-Priorität:** 3  
**Niedrig-Priorität:** 3

**Geschätzter Aufwand:**
- Hoch-Priorität: 2-3 Tage
- Mittel-Priorität: 2-3 Tage
- Niedrig-Priorität: 1-2 Tage

**Gesamt:** 5-8 Tage

**ROI:** Hoch (zentrale Business-Logik, viele Call-Sites, Performance-Verbesserungen)

---

## 9. NÄCHSTE SCHRITTE

1. **Sofort:** Parameter-Abfrage zentralisieren + Caching
2. **Diese Woche:** PayrollRecord.save() refactoren
3. **Nächste Woche:** Prozent/Dezimal-Konvertierung zentralisieren
4. **Später:** Restliche Mittel/Niedrig-Priorität

---

**Ende des Audits**
