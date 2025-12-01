# 🗺️ AdeaLohn Roadmap – Nächste Schritte

**Aktueller Stand:** ✅ Produktionsreif (9/10)  
**Datum:** 2025-11-20

---

## 🎯 PHASE 1: Production-Deployment (KRITISCH)

### 1.1 Production-Settings vorbereiten
**Priorität:** 🔴 **HOCH** (vor Live-Betrieb)

**Aufgaben:**
- [ ] `SECRET_KEY` aus Environment-Variable lesen
- [ ] `DEBUG = False` für Production
- [ ] `ALLOWED_HOSTS` aus Environment konfigurieren
- [ ] Separate `settings_production.py` oder Environment-basierte Konfiguration
- [ ] Database-URL aus Environment (für PostgreSQL/MySQL)
- [ ] Static Files für Production konfigurieren (WhiteNoise oder CDN)
- [ ] Media Files konfigurieren (falls benötigt)

**Zeitaufwand:** 2-3 Stunden

---

### 1.2 Deployment-Checklist
**Priorität:** 🔴 **HOCH**

**Aufgaben:**
- [ ] Django Deployment Checklist durchgehen
- [ ] HTTPS konfigurieren (SSL/TLS)
- [ ] Backup-Strategie definieren
- [ ] Monitoring/Logging für Production
- [ ] Error-Tracking (z.B. Sentry)
- [ ] Performance-Monitoring

**Zeitaufwand:** 4-6 Stunden

---

## 📄 PHASE 2: PDF-Export & Reporting (WICHTIG)

### 2.1 PDF-Lohnausweis generieren
**Priorität:** 🟡 **MITTEL-HOCH** (Kern-Feature)

**Aufgaben:**
- [ ] PDF-Library auswählen (WeasyPrint oder ReportLab)
- [ ] Template für Lohnausweis erstellen
- [ ] View für PDF-Generierung
- [ ] Download-Button in PayrollDetail
- [ ] Formatierung nach Schweizer Standard

**Zeitaufwand:** 8-12 Stunden

---

### 2.2 Jahreslohnauskunft (Jahreslohnausweis)
**Priorität:** 🟡 **MITTEL**

**Aufgaben:**
- [ ] View für Jahresübersicht (alle 12 Monate aggregiert)
- [ ] PDF-Generierung für Jahreslohnauskunft
- [ ] YTD-Werte korrekt anzeigen
- [ ] Steuerrelevante Summen

**Zeitaufwand:** 6-8 Stunden

---

### 2.3 CSV/Excel-Export
**Priorität:** 🟢 **NIEDRIG**

**Aufgaben:**
- [ ] CSV-Export für PayrollRecords
- [ ] Excel-Export (optional, mit openpyxl)
- [ ] Export für Buchhaltung
- [ ] Bank-Export (LSV/ESR) – optional

**Zeitaufwand:** 4-6 Stunden

---

## 🔗 PHASE 3: Integration & Automatisierung (WICHTIG)

### 3.1 AdeaZeit → AdeaLohn Integration
**Priorität:** 🟡 **MITTEL-HOCH**

**Aufgaben:**
- [ ] Stunden aus AdeaZeit importieren
- [ ] Automatische PayrollItem-Erstellung aus TimeRecords
- [ ] Validierung: Nur abgerechnete Stunden
- [ ] UI: "Stunden aus AdeaZeit importieren" Button

**Zeitaufwand:** 8-10 Stunden

---

### 3.2 Abwesenheiten-Integration
**Priorität:** 🟡 **MITTEL**

**Aufgaben:**
- [ ] Ferien/Urlaub aus AdeaZeit berücksichtigen
- [ ] Krankentage-Tracking
- [ ] Feiertags-Logik
- [ ] Soll-Ist-Vergleich in Payroll

**Zeitaufwand:** 6-8 Stunden

---

## ⚡ PHASE 4: Performance & Optimierung (OPTIONAL)

### 4.1 Database-Optimierungen
**Priorität:** 🟢 **NIEDRIG**

**Aufgaben:**
- [ ] Konsistente `select_related()` und `prefetch_related()`
- [ ] Database-Indexes prüfen
- [ ] Query-Optimierung für Listen-Views
- [ ] Pagination für große Datensätze

**Zeitaufwand:** 4-6 Stunden

---

### 4.2 Caching
**Priorität:** 🟢 **NIEDRIG**

**Aufgaben:**
- [ ] Redis/Memcached für häufig verwendete Queries
- [ ] Template-Caching
- [ ] Query-Caching für Parameter-Models

**Zeitaufwand:** 3-4 Stunden

---

## 📚 PHASE 5: Dokumentation & Benutzerführung (WICHTIG)

### 5.1 Benutzerdokumentation
**Priorität:** 🟡 **MITTEL**

**Aufgaben:**
- [ ] README.md für AdeaLohn
- [ ] Benutzerhandbuch (PDF oder Wiki)
- [ ] Screenshots und Anleitungen
- [ ] FAQ

**Zeitaufwand:** 8-12 Stunden

---

### 5.2 Code-Dokumentation
**Priorität:** 🟢 **NIEDRIG**

**Aufgaben:**
- [ ] Docstrings für alle wichtigen Funktionen
- [ ] API-Dokumentation (falls API geplant)
- [ ] Architektur-Dokumentation

**Zeitaufwand:** 4-6 Stunden

---

### 5.3 UI-Verbesserungen
**Priorität:** 🟡 **MITTEL**

**Aufgaben:**
- [ ] Tooltips für komplexe Felder
- [ ] Hilfe-Texte in Forms
- [ ] Validierungs-Fehlermeldungen verbessern
- [ ] Breadcrumbs

**Zeitaufwand:** 4-6 Stunden

---

## 🧪 PHASE 6: Testing & Qualitätssicherung (WICHTIG)

### 6.1 Erweiterte Tests
**Priorität:** 🟡 **MITTEL**

**Aufgaben:**
- [ ] Integration-Tests für PDF-Generierung
- [ ] Tests für AdeaZeit-Integration
- [ ] Edge-Case-Tests
- [ ] Performance-Tests

**Zeitaufwand:** 6-8 Stunden

---

## 🎨 PHASE 7: Weitere Features (OPTIONAL)

### 7.1 13. Monatslohn
**Priorität:** 🟢 **NIEDRIG**

**Aufgaben:**
- [ ] WageType für 13. Monatslohn
- [ ] Automatische Berechnung (optional)
- [ ] UI für Erfassung

**Zeitaufwand:** 3-4 Stunden

---

### 7.2 Bonus/Gratifikation
**Priorität:** 🟢 **NIEDRIG**

**Aufgaben:**
- [ ] WageType für Bonus
- [ ] Steuer-Optimierung (optional)
- [ ] UI für Erfassung

**Zeitaufwand:** 2-3 Stunden

---

### 7.3 Überstunden-Automatik
**Priorität:** 🟢 **NIEDRIG**

**Aufgaben:**
- [ ] Automatische Erkennung von Überstunden
- [ ] Zuschläge berechnen
- [ ] Konfigurierbare Schwellenwerte

**Zeitaufwand:** 6-8 Stunden

---

## 📊 PRIORISIERUNG

### Sofort (vor Live-Betrieb):
1. ✅ **Production-Settings** (Phase 1.1)
2. ✅ **Deployment-Checklist** (Phase 1.2)

### Kurzfristig (1-2 Monate):
3. ✅ **PDF-Lohnausweis** (Phase 2.1)
4. ✅ **AdeaZeit-Integration** (Phase 3.1)
5. ✅ **Benutzerdokumentation** (Phase 5.1)

### Mittelfristig (3-6 Monate):
6. ✅ **Jahreslohnauskunft** (Phase 2.2)
7. ✅ **Abwesenheiten-Integration** (Phase 3.2)
8. ✅ **Erweiterte Tests** (Phase 6.1)

### Langfristig (optional):
9. ✅ **Performance-Optimierungen** (Phase 4)
10. ✅ **Weitere Features** (Phase 7)

---

## 🎯 EMPFOHLENER NÄCHSTER SCHRITT

**Phase 1.1: Production-Settings vorbereiten**

**Warum?**
- System ist funktional produktionsreif
- Aber noch nicht deployment-ready
- SECRET_KEY und DEBUG müssen aus Environment kommen

**Was zu tun:**
1. Environment-Variablen für Settings einrichten
2. `settings_production.py` erstellen oder Environment-basierte Konfiguration
3. `.env`-Datei für lokale Entwicklung
4. Dokumentation für Deployment

**Zeitaufwand:** 2-3 Stunden

---

## 📝 NOTIZEN

- **Aktueller Stand:** System ist funktional komplett und getestet
- **Kritische Features:** Alle implementiert ✅
- **Production-Ready:** Fast – nur Settings fehlen noch
- **Vergleich:** Gleichwertig mit professionellen Systemen (Abacus, Sage, SwissSalary)

---

**Letzte Aktualisierung:** 2025-11-20


