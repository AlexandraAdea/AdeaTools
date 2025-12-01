# 📋 To-Do-Liste Feature - Finaler Plan

**Datum:** 25. November 2025  
**Status:** ✅ Finalisiert - Bereit für Implementierung  
**Anforderungen:** Erfahrene Treuhand-Mitarbeiterin

---

## ✅ Finale Anforderungen

### 1. **KEINE Verknüpfung mit Zeiteinträgen**
- To-Dos und Zeiteinträge bleiben getrennt
- Einfacher, klarer Fokus
- ✅ **Umgesetzt**

### 2. **Mandanten-Zuordnung**
- Jede Aufgabe kann einem Mandanten zugeordnet werden
- Wichtig für Treuhand: "Steuererklärung Müller AG"
- Optional (kann auch leer sein für interne Aufgaben)
- ✅ **Umgesetzt**

### 3. **Fälligkeitsdatum**
- **KRITISCH für Treuhand** (Steuerfristen, MwSt-Abgaben, etc.)
- Muss vorhanden sein
- Später: AI-Erinnerungen bei nahenden Fristen
- ✅ **Umgesetzt**

### 4. **3 Statusen**
- OFFEN (neu erstellt)
- IN_ARBEIT (wird bearbeitet)
- ERLEDIGT (abgeschlossen)
- ✅ **Umgesetzt**

### 5. **Notizen - einfache Variante**
- Ein Textfeld pro To-Do
- "Wo geblieben" Notizen
- Kann jederzeit aktualisiert werden
- ✅ **Umgesetzt**

---

## 📊 Datenmodell

### Model: `Task`

```python
class Task(models.Model):
    STATUS_CHOICES = [
        ('OFFEN', 'Offen'),
        ('IN_ARBEIT', 'In Arbeit'),
        ('ERLEDIGT', 'Erledigt'),
    ]
    
    PRIORITAET_CHOICES = [
        ('NIEDRIG', 'Niedrig'),
        ('MITTEL', 'Mittel'),
        ('HOCH', 'Hoch'),
    ]
    
    # Verknüpfungen
    mitarbeiter = ForeignKey(EmployeeInternal)  # Wer hat die Aufgabe
    client = ForeignKey(Client, null=True, blank=True)  # Optional: Mandant
    
    # Aufgaben-Daten
    titel = CharField(max_length=255)  # "Steuererklärung Müller AG"
    beschreibung = TextField(blank=True)  # Details (optional)
    
    # Status & Priorität
    status = CharField(choices=STATUS_CHOICES, default='OFFEN')
    prioritaet = CharField(choices=PRIORITAET_CHOICES, default='MITTEL')
    
    # Fristen (KRITISCH für Treuhand)
    fälligkeitsdatum = DateField(null=True, blank=True)  # Wichtig!
    
    # Notizen
    notizen = TextField(blank=True)  # "Wo geblieben" - einfache Variante
    
    # Metadaten
    erstellt_am = DateTimeField(auto_now_add=True)
    erledigt_am = DateTimeField(null=True, blank=True)
    updated_at = DateTimeField(auto_now=True)
```

---

## 🎨 UI/UX Design

### Übersichtsseite: "Meine Aufgaben"

```
┌─────────────────────────────────────────────────────┐
│  Meine Aufgaben                    [+ Neue Aufgabe] │
├─────────────────────────────────────────────────────┤
│  🔴 HOCH PRIORITÄT                                  │
│  ┌─────────────────────────────────────────────┐   │
│  │ ☐ Steuererklärung Müller AG                 │   │
│  │    📅 Fällig: 30.11.2025 ⚠️ (in 5 Tagen)    │   │
│  │    🏢 Mandant: Müller AG                     │   │
│  │    📝 Notizen: Warte auf Belege vom Kunden  │   │
│  │    [Bearbeiten] [→ In Arbeit]               │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  🟡 MITTEL PRIORITÄT                                │
│  ┌─────────────────────────────────────────────┐   │
│  │ ☐ Jahresabschluss 2024 - Müller AG          │   │
│  │    📅 Fällig: 15.12.2025                    │   │
│  │    🏢 Mandant: Müller AG                    │   │
│  │    [Bearbeiten] [→ In Arbeit]               │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ✅ ERLEDIGT (diese Woche)                         │
│  ┌─────────────────────────────────────────────┐   │
│  │ ☑️ MwSt-Abgabe Q3 2025                      │   │
│  │    Erledigt: 20.11.2025                     │   │
│  │    🏢 Mandant: Müller AG                    │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### Features:
- ✅ Farbcodierung nach Priorität (Rot/Gelb/Grün)
- ✅ Warnung bei nahenden Fristen (z.B. "in 5 Tagen")
- ✅ Filter: Status / Priorität / Mandant / Fälligkeitsdatum
- ✅ Suche nach Titel/Beschreibung
- ✅ Schnelle Status-Änderung (Buttons)
- ✅ Notizen direkt sichtbar

---

## 🔐 Berechtigungen

- **Mitarbeiter:** Nur eigene Aufgaben sehen/bearbeiten
- **Manager/Admin:** Alle Aufgaben sehen (optional, später)
- **Erstellen:** Jeder kann eigene Aufgaben erstellen

---

## 📋 Implementierungs-Schritte

### Phase 1: Basis (MVP)
1. ✅ Model `Task` erstellen
2. ✅ Migration erstellen
3. ✅ Form `TaskForm` erstellen
4. ✅ Views: Liste, Erstellen, Bearbeiten
5. ✅ Templates: Liste, Formular
6. ✅ URL-Routen
7. ✅ Navigation hinzufügen

### Phase 2: UI-Verbesserungen
1. ✅ Farbcodierung nach Priorität
2. ✅ Fälligkeitsdatum-Warnungen
3. ✅ Filter & Suche
4. ✅ Schnelle Status-Änderung

### Phase 3: Erweiterungen (später)
1. 📧 E-Mail-Erinnerungen bei nahenden Fristen
2. 🤖 AI-Erinnerungen (wie du vorgeschlagen hast)
3. 📊 Statistiken: "Wie viele Aufgaben offen?"

---

## 🎯 Warum das perfekt für Treuhand ist:

1. **Fristen-Management:** Steuerfristen, MwSt-Abgaben sind kritisch
2. **Mandanten-Zuordnung:** Klare Zuordnung zu Kunden
3. **Einfach:** Keine Überfrachtung, fokussiert auf das Wesentliche
4. **Notizen:** "Wo geblieben" hilft bei komplexen Fällen
5. **Status:** Klarer Überblick über offene Aufgaben

---

## ✅ Bereit für Implementierung!

**Soll ich jetzt starten?**




