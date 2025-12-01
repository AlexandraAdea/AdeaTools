# 📋 To-Do-Liste Feature - Planungsdokument

**Datum:** 25. November 2025  
**Status:** Planungsphase  
**Inspiration:** Asana-App

---

## 🎯 Ziel

Eine benutzerfreundliche To-Do-Liste für Mitarbeitende, damit sie:
- Aufgaben planen können
- Notieren können, wo sie geblieben sind
- Den Überblick über ihre Arbeit behalten
- Aufgaben mit Zeiterfassung verknüpfen können

---

## ❓ Offene Fragen (bitte klären)

### 1. Integration mit Zeiterfassung
- **Soll eine To-Do mit einem Zeiteintrag verknüpft werden können?**
  - Beispiel: "Steuererklärung Müller AG" → später als Zeiteintrag erfassen
  - Oder: To-Do und Zeiteintrag sind getrennt?

### 2. Struktur der To-Dos
- **Sollen To-Dos Projekten/Mandanten zugeordnet werden?**
  - Beispiel: "Steuererklärung Müller AG" → Mandant: Müller AG
  - Oder: Nur persönliche To-Dos ohne Mandanten-Zuordnung?

### 3. Status & Prioritäten
- **Welche Status soll es geben?**
  - Geplant / In Arbeit / Erledigt / Verschoben?
  - Prioritäten: Hoch / Mittel / Niedrig?

### 4. Zeitplanung
- **Sollen To-Dos ein Fälligkeitsdatum haben?**
  - Beispiel: "Bis 30.11.2025"
  - Oder: Nur freie Notizen ohne Datum?

### 5. Sichtbarkeit
- **Wer soll die To-Dos sehen?**
  - Nur der Mitarbeiter selbst?
  - Manager können alle sehen?
  - Admin kann alle sehen?

### 6. "Wo geblieben" Notizen
- **Wie soll das funktionieren?**
  - Ein Textfeld pro To-Do: "Notizen / Stand"?
  - Mehrere Notizen mit Datum (wie ein Log)?
  - Oder einfach ein Kommentar-Feld?

---

## 💡 Vorschlag: Minimal-Version (MVP)

### Phase 1: Einfache To-Do-Liste

**Model: `Task` (oder `Todo`)**
```python
- mitarbeiter (ForeignKey zu EmployeeInternal)
- titel (CharField) - z.B. "Steuererklärung Müller AG"
- beschreibung (TextField, optional) - Details
- status (ChoiceField) - OFFEN / IN_ARBEIT / ERLEDIGT
- prioritaet (ChoiceField) - NIEDRIG / MITTEL / HOCH
- fälligkeitsdatum (DateField, optional)
- notizen (TextField) - "Wo geblieben" Notizen
- client (ForeignKey zu Client, optional) - Verknüpfung mit Mandant
- project (ForeignKey zu ZeitProject, optional) - Verknüpfung mit Projekt
- erstellt_am (DateTimeField)
- erledigt_am (DateTimeField, optional)
```

**Features:**
- ✅ Liste aller eigenen To-Dos
- ✅ Neue To-Do erstellen
- ✅ To-Do bearbeiten (Status ändern, Notizen hinzufügen)
- ✅ To-Do als erledigt markieren
- ✅ Filter nach Status / Priorität / Fälligkeitsdatum
- ✅ Suche nach Titel/Beschreibung

**UI:**
- 📋 To-Do-Liste Seite (ähnlich wie Zeiteinträge)
- ➕ Button "Neue Aufgabe"
- ✅ Checkbox zum Erledigen
- 📝 Notizen-Feld für "Wo geblieben"

---

## 🎨 UI/UX Vorschlag

### Layout (wie Asana)
```
┌─────────────────────────────────────────┐
│  Meine Aufgaben                         │
│  [+ Neue Aufgabe]                       │
├─────────────────────────────────────────┤
│  🔴 HOCH                                │
│  ☐ Steuererklärung Müller AG            │
│     📅 Fällig: 30.11.2025               │
│     📝 Notizen: Warte auf Belege...     │
│     [Bearbeiten] [Erledigt]             │
│                                         │
│  🟡 MITTEL                              │
│  ☐ Jahresabschluss 2024                 │
│     📅 Fällig: 15.12.2025               │
│     [Bearbeiten] [Erledigt]             │
│                                         │
│  ✅ ERLEDIGT                            │
│  ☑️ Lohnabrechnung November              │
│     Erledigt: 20.11.2025                │
└─────────────────────────────────────────┘
```

### Navigation
- Neuer Menüpunkt: "Aufgaben" (zwischen "Zeiteinträge" und "Abwesenheiten")
- Mitarbeiter sehen nur eigene Aufgaben
- Manager/Admin sehen alle Aufgaben (optional)

---

## 🔗 Integration mit Zeiterfassung

### Option A: Verknüpfung (empfohlen)
- Beim Erstellen eines Zeiteintrags: "Verknüpft mit Aufgabe: [Dropdown]"
- Zeiteintrag kann optional mit To-Do verknüpft werden
- In To-Do-Ansicht: "Zeit erfasst: 2.5h" anzeigen

### Option B: Getrennt
- To-Dos und Zeiteinträge sind unabhängig
- Einfacher, aber weniger integriert

---

## 📊 Erweiterte Features (später)

### Phase 2 (optional):
- 📎 Datei-Anhänge zu To-Dos
- 👥 Aufgaben teilen (Team-Aufgaben)
- 📧 E-Mail-Benachrichtigungen bei Fälligkeit
- 📈 Statistiken: "Wie viele Aufgaben erledigt diese Woche?"

### Phase 3 (optional):
- 🔄 Wiederkehrende Aufgaben
- 📋 Unteraufgaben (Subtasks)
- 🏷️ Tags/Labels
- 📅 Kalender-Ansicht

---

## 🛠️ Technische Umsetzung

### Neue Dateien:
```
adeazeit/
├── models.py (Task-Model hinzufügen)
├── forms.py (TaskForm hinzufügen)
├── views.py (TaskListView, TaskCreateView, TaskUpdateView)
├── urls.py (neue Routes)
└── templates/adeazeit/
    ├── task_list.html
    └── task_form.html
```

### Migration:
- Neue Migration für `Task`-Model
- Foreign Keys zu `EmployeeInternal`, `Client`, `ZeitProject`

---

## ✅ Nächste Schritte

1. **Fragen klären** (siehe oben)
2. **MVP definieren** (welche Features in Phase 1?)
3. **UI-Mockup** erstellen (optional)
4. **Implementierung** starten

---

## 💭 Meine Empfehlung

**Für den Start (MVP):**
- ✅ Einfache To-Do-Liste mit Status (OFFEN / IN_ARBEIT / ERLEDIGT)
- ✅ Priorität (HOCH / MITTEL / NIEDRIG)
- ✅ Fälligkeitsdatum (optional)
- ✅ Notizen-Feld für "Wo geblieben"
- ✅ Optional: Verknüpfung mit Mandant/Projekt
- ✅ Optional: Verknüpfung mit Zeiteintrag (später)

**UI:**
- 📋 Übersichtliche Liste (wie Asana)
- 🎨 Farbcodierung nach Priorität
- ✅ Checkbox zum schnellen Erledigen
- 📝 Notizen direkt in der Liste bearbeitbar

**Berechtigungen:**
- Mitarbeiter: Nur eigene Aufgaben
- Manager/Admin: Alle Aufgaben sehen (optional)

---

**Was denkst du? Welche Features sind wichtig für dich?**




