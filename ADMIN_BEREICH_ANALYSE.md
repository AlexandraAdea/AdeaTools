# Admin-Bereich Analyse - Doppelte Funktionen und Reorganisationsbedarf

**Datum:** 2025-01-XX  
**Status:** Analyse (keine Änderungen)

---

## 1. Übersicht: Admin-Zugriffspunkte

### 1.1 URLs und Routen

| URL | Funktion | Zugriff | Template |
|-----|----------|---------|----------|
| `/management-console-secure/` | Django Admin (Standard) | Staff | Django Admin UI |
| `/admin/` | Redirect zu `/management-console-secure/` | Alle | Redirect |
| `/management-dashboard/` | Custom Admin Dashboard | Staff | `admin/dashboard.html` |
| `/` (home) | Startseite mit Modul-Karten | Alle | `home.html` |

**Problem:** Zwei verschiedene Admin-Interfaces:
- Django Admin (`/management-console-secure/`)
- Custom Dashboard (`/management-dashboard/`)

---

## 2. Navigation-Strukturen

### 2.1 Template: `admin_base.html` (MIT Sidebar)

**Verwendung:** Wird aktuell NICHT verwendet (Dashboard verwendet `admin_base.html`)

**Navigation:**
- Dashboard
- Mandantenverwaltung → Mandanten
- Zeiterfassung → Zeiteinträge, Mitarbeitende, Abwesenheiten, Service-Typen, Feiertage
- Lohnabrechnung → Lohnabrechnungen, Mitarbeitende
- System → Django Admin

**Problem:** Sidebar-Navigation existiert, wird aber nicht genutzt.

### 2.2 Template: `admin_base_no_sidebar.html` (OHNE Sidebar)

**Verwendung:** Wird für die meisten Views verwendet (Zeiteinträge, Mitarbeitende, etc.)

**Top-Navigation:**
- Dashboard (nur für Staff)
- Zeiteinträge
- Kundenübersicht (nur Manager/Admin)
- Aufgaben
- Mitarbeitende (nur für Staff)
- Abwesenheiten (nur für Staff)
- Service-Typen (nur für Staff)

**Problem:** Doppelte Navigation:
- Top-Navigation in `admin_base_no_sidebar.html`
- Sidebar in `admin_base.html` (unbenutzt)

---

## 3. Doppelte Funktionen

### 3.1 Mitarbeitende-Verwaltung

**Problem:** ZWEI verschiedene Mitarbeitende-Modelle mit separaten Verwaltungen:

#### A) `EmployeeInternal` (AdeaZeit)
- **URL:** `/zeit/employees/`
- **View:** `EmployeeInternalListView`
- **Admin:** `EmployeeInternalAdmin` in `adeazeit/admin.py`
- **Zweck:** Interne Mitarbeitende für Zeiterfassung
- **Navigation:** Top-Nav in `admin_base_no_sidebar.html`

#### B) `Employee` (AdeaCore/AdeaLohn)
- **URL:** `/lohn/employees/`
- **View:** `EmployeeListView` (AdeaLohn)
- **Admin:** `EmployeeAdmin` in `adeacore/admin.py`
- **Zweck:** Mitarbeitende für Lohnabrechnung
- **Navigation:** Sidebar in `admin_base.html` (unbenutzt)

**Konflikt:** Zwei separate Verwaltungen für ähnliche Daten.

---

### 3.2 Dashboard vs. Django Admin

#### A) Custom Dashboard (`/management-dashboard/`)
- **Template:** `admin/dashboard.html`
- **Base:** `admin_base.html` (mit Sidebar)
- **Funktionen:**
  - Statistiken (Mandanten, Zeiterfassung, Mitarbeitende, Lohnabrechnung)
  - Letzte Zeiteinträge
  - Aktive Abwesenheiten
  - Links zu Modulen

#### B) Django Admin (`/management-console-secure/`)
- **Template:** Django Standard UI
- **Funktionen:**
  - CRUD für alle Models
  - Erweiterte Filter, Suche
  - Bulk-Actions
  - Alle Models registriert

**Problem:** Zwei verschiedene Admin-Interfaces mit unterschiedlichen Funktionen.

---

### 3.3 Feiertage-Verwaltung

**Problem:** Feiertage werden nur über Django Admin verwaltet:

- **Django Admin:** `/management-console-secure/adeazeit/holiday/`
- **Link in Sidebar:** `/admin/adeazeit/holiday/` (öffnet in neuem Tab)
- **Keine Custom View:** Keine benutzerfreundliche View wie bei anderen Modellen

**Konflikt:** Inkonsistente Verwaltung (nur Django Admin, keine Custom View).

---

### 3.4 Mandanten-Verwaltung

#### A) AdeaDesk (`/desk/clients/`)
- **View:** `ClientListView`
- **Template:** `adeadesk/index.html`
- **Funktionen:** CRM, Termine, Dokumente

#### B) Django Admin (`/management-console-secure/adeacore/client/`)
- **Admin:** `ClientAdmin` in `adeacore/admin.py`
- **Funktionen:** Standard CRUD

**Problem:** Zwei verschiedene Interfaces für Mandanten.

---

## 4. Template-Struktur

### 4.1 Base-Templates

| Template | Sidebar | Verwendung | Status |
|----------|---------|------------|--------|
| `admin_base.html` | ✅ Ja | Dashboard | ✅ Aktiv |
| `admin_base_no_sidebar.html` | ❌ Nein | Alle anderen Views | ✅ Aktiv |
| `base.html` | ❌ Nein | Home, Login | ✅ Aktiv |

**Problem:** Zwei verschiedene Admin-Base-Templates mit unterschiedlicher Navigation.

---

## 5. Admin-Registrierungen

### 5.1 Models in Django Admin

#### `adeacore/admin.py`:
- `Client`
- `Employee` (Lohn)
- `Project`
- `TimeRecord`
- `SVAEntscheid`
- `PayrollRecord`

#### `adeazeit/admin.py`:
- `UserProfile`
- `EmployeeInternal` (Zeit)
- `ServiceType`
- `ZeitProject`
- `TimeEntry`
- `Absence`
- `Holiday`
- `Task`

#### `adealohn/admin.py`:
- `WageType`
- `PayrollItem`
- `KTGParameter`
- `BVGParameter`
- `QSTParameter`
- `FamilyAllowanceParameter`

#### `adeadesk/admin.py`:
- Leer (keine Registrierungen)

**Problem:** Viele Models nur über Django Admin zugänglich, keine Custom Views.

---

## 6. Identifizierte Probleme

### 6.1 Doppelte Navigation
- **Top-Navigation** in `admin_base_no_sidebar.html`
- **Sidebar** in `admin_base.html` (nur für Dashboard verwendet)
- **Inkonsistenz:** Unterschiedliche Navigation je nach View

### 6.2 Doppelte Admin-Interfaces
- **Custom Dashboard** (`/management-dashboard/`)
- **Django Admin** (`/management-console-secure/`)
- **Problem:** Benutzer müssen zwischen beiden wechseln

### 6.3 Doppelte Mitarbeitende-Verwaltung
- **EmployeeInternal** (Zeit) → Custom View
- **Employee** (Lohn) → Django Admin + Custom View
- **Problem:** Zwei separate Verwaltungen

### 6.4 Inkonsistente Verwaltung
- **Feiertage:** Nur Django Admin
- **Service-Typen:** Custom View + Django Admin
- **Mitarbeitende:** Custom View + Django Admin
- **Problem:** Keine einheitliche Strategie

### 6.5 Unbenutzte Templates
- **`admin_base.html`:** Wird nur für Dashboard verwendet
- **Sidebar-Navigation:** Existiert, aber nicht konsistent genutzt

---

## 7. Empfehlungen zur Reorganisation

### 7.1 Option A: Django Admin als Haupt-Interface
**Vorteile:**
- Einheitliches Interface
- Alle Models verfügbar
- Weniger Code-Wartung

**Nachteile:**
- Weniger benutzerfreundlich
- Custom Dashboard müsste entfernt werden

### 7.2 Option B: Custom Views als Haupt-Interface
**Vorteile:**
- Benutzerfreundlicher
- Konsistentes Design
- Bessere UX

**Nachteile:**
- Mehr Entwicklungsaufwand
- Django Admin nur für technische Verwaltung

### 7.3 Option C: Hybrid (Empfohlen)
**Struktur:**
1. **Custom Dashboard** (`/management-dashboard/`) als Haupt-Interface
2. **Custom Views** für häufig genutzte Funktionen
3. **Django Admin** nur für technische Verwaltung (versteckt)

**Reorganisation:**
- Alle häufig genutzten Models → Custom Views
- Django Admin → Nur für technische Einstellungen
- Einheitliche Navigation (Top-Nav oder Sidebar, nicht beides)

---

## 8. Konkrete Reorganisations-Schritte

### Schritt 1: Navigation vereinheitlichen
- [ ] Entscheiden: Top-Nav ODER Sidebar (nicht beides)
- [ ] Alle Views auf ein Base-Template umstellen
- [ ] Konsistente Navigation-Struktur

### Schritt 2: Mitarbeitende konsolidieren
- [ ] Prüfen: Können `EmployeeInternal` und `Employee` zusammengeführt werden?
- [ ] Oder: Klare Trennung mit einheitlicher Verwaltung

### Schritt 3: Feiertage Custom View erstellen
- [ ] Custom View für Feiertage (wie Service-Typen)
- [ ] Aus Sidebar-Navigation entfernen (Django Admin Link)

### Schritt 4: Dashboard optimieren
- [ ] Dashboard als zentrale Übersicht
- [ ] Links zu allen wichtigen Funktionen
- [ ] Django Admin nur für technische Einstellungen

### Schritt 5: Unbenutzte Templates entfernen
- [ ] Prüfen: Welche Templates werden wirklich verwendet?
- [ ] Unbenutzte Templates archivieren/löschen

---

## 9. Zusammenfassung

**Hauptprobleme:**
1. ✅ **Doppelte Navigation** (Top-Nav + Sidebar)
2. ✅ **Doppelte Admin-Interfaces** (Custom + Django Admin)
3. ✅ **Doppelte Mitarbeitende-Verwaltung** (EmployeeInternal + Employee)
4. ✅ **Inkonsistente Verwaltung** (manche Models nur Django Admin)
5. ✅ **Unbenutzte Templates** (`admin_base.html` Sidebar)

**Empfehlung:**
- **Hybrid-Ansatz:** Custom Views für häufig genutzte Funktionen, Django Admin für technische Verwaltung
- **Einheitliche Navigation:** Top-Nav ODER Sidebar (nicht beides)
- **Konsolidierung:** Mitarbeitende-Verwaltung vereinheitlichen
- **Vervollständigung:** Feiertage Custom View erstellen

---

**Nächste Schritte:**
1. Entscheidung über Navigation-Struktur
2. Mitarbeitende-Konsolidierung planen
3. Feiertage Custom View implementieren
4. Unbenutzte Templates entfernen






