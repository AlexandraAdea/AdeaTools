# Rollen & Berechtigungen: AdeaZeit

## Übersicht

AdeaZeit verwendet ein **3-Rollen-System** basierend auf Django Groups:

1. **ADMIN** - Vollzugriff auf alles
2. **MANAGER** - Kann alles sehen und bearbeiten, aber nicht löschen
3. **MITARBEITER** - Kann nur eigene Zeiteinträge sehen und bearbeiten

---

## Rollen-Definitionen

### 1. AdeaZeit Admin
- **Vollzugriff** auf alle Funktionen
- Kann **löschen**
- Kann **Mitarbeitende verwalten**
- Kann **Service-Typen verwalten**
- Kann **alle Zeiteinträge sehen**
- Kann **Feiertage verwalten** (über Django Admin)

### 2. AdeaZeit Manager
- Kann **alles sehen** (alle Zeiteinträge, Mitarbeitende, etc.)
- Kann **alles bearbeiten** (eigene und fremde Einträge)
- **Kann NICHT löschen**
- Kann **Mitarbeitende verwalten**
- Kann **Service-Typen verwalten**
- Kann **Abwesenheiten verwalten**

### 3. AdeaZeit Mitarbeiter
- Kann **nur eigene Zeiteinträge** sehen
- Kann **nur eigene Zeiteinträge** bearbeiten
- Kann **nur eigene Abwesenheiten** sehen/bearbeiten
- **Kann NICHT löschen**
- **Kann NICHT** Mitarbeitende verwalten
- **Kann NICHT** Service-Typen verwalten

---

## Installation

### 1. Rollen initialisieren

```bash
python manage.py init_roles
```

Dies erstellt die drei Rollen-Groups:
- `AdeaZeit Admin`
- `AdeaZeit Manager`
- `AdeaZeit Mitarbeiter`

### 2. Benutzern Rollen zuweisen

#### Option A: Django Admin
1. Gehen Sie zu Django Admin → Users
2. Wählen Sie einen Benutzer
3. Fügen Sie die entsprechende Group hinzu

#### Option B: Python Shell
```python
from django.contrib.auth.models import User, Group

# Hole User und Group
user = User.objects.get(username="max.mustermann")
group = Group.objects.get(name="AdeaZeit Admin")

# Weise Rolle zu
user.groups.add(group)
```

---

## Technische Details

### Permission-System

Das System verwendet:
- **Django Groups** für Rollen
- **Custom Permission-Funktionen** in `adeazeit/permissions.py`
- **Permission-Mixins** in `adeazeit/mixins.py`
- **Context Processor** für Template-Zugriff

### Views mit Rollenprüfung

- **AdminRequiredMixin**: Nur für Admins
- **ManagerOrAdminRequiredMixin**: Für Manager und Admins
- **TimeEntryFilterMixin**: Filtert Zeiteinträge nach Rolle
- **EmployeeFilterMixin**: Filtert Mitarbeitende nach Rolle
- **AbsenceFilterMixin**: Filtert Abwesenheiten nach Rolle
- **CanEditMixin**: Prüft Bearbeitungsrechte
- **CanDeleteMixin**: Prüft Löschrechte

### Template-Variablen

Folgende Variablen sind in Templates verfügbar:
- `adeazeit_is_admin`: Ist User Admin?
- `adeazeit_is_manager`: Ist User Manager oder Admin?
- `adeazeit_can_manage_employees`: Kann User Mitarbeitende verwalten?
- `adeazeit_can_manage_service_types`: Kann User Service-Typen verwalten?
- `adeazeit_can_manage_absences`: Kann User Abwesenheiten verwalten?
- `adeazeit_can_delete`: Kann User löschen?

---

## Verwendung in Templates

```django
{% if adeazeit_can_manage_employees %}
<a href="{% url 'adeazeit:employee-create' %}">+ Neue Mitarbeiterin</a>
{% endif %}

{% if adeazeit_can_delete %}
<a href="{% url 'adeazeit:timeentry-delete' entry.pk %}">Löschen</a>
{% endif %}
```

---

## Mitarbeiter-Zuordnung

**✅ Implementiert:** Das System verwendet jetzt das `UserProfile`-Model, das `User` mit `EmployeeInternal` verknüpft.

### UserProfile-Model

```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee = models.ForeignKey(EmployeeInternal, on_delete=models.SET_NULL, null=True, blank=True)
```

### Verwendung

1. **Im Django Admin:**
   - Gehen Sie zu Users → Wählen Sie einen User
   - Im "AdeaZeit Profil" Abschnitt können Sie einen `EmployeeInternal` zuordnen

2. **Per Python Shell:**
```python
from django.contrib.auth.models import User
from adeazeit.models import UserProfile, EmployeeInternal

user = User.objects.get(username="max.mustermann")
employee = EmployeeInternal.objects.get(code="MM")
profile, created = UserProfile.objects.get_or_create(user=user)
profile.employee = employee
profile.save()
```

**Fallback:** Falls kein `UserProfile` existiert, versucht das System weiterhin, Mitarbeitende über `username` oder `name` zu finden (für Migration).

---

## Sicherheit

- Alle Views sind mit `LoginRequiredMixin` geschützt
- Rollenprüfung erfolgt in `dispatch()`-Methoden
- Filterung erfolgt in `get_queryset()`-Methoden
- Templates zeigen nur relevante Links/Buttons

---

## Migration von bestehenden Usern

Bestehende Superuser werden automatisch als **Admin** behandelt.

Um bestehenden Usern Rollen zuzuweisen:

```python
from django.contrib.auth.models import User, Group

# Alle Superuser = Admin
admin_group = Group.objects.get(name="AdeaZeit Admin")
for user in User.objects.filter(is_superuser=True):
    user.groups.add(admin_group)

# Alle anderen = Mitarbeiter (Standard)
mitarbeiter_group = Group.objects.get(name="AdeaZeit Mitarbeiter")
for user in User.objects.filter(is_superuser=False):
    if not user.groups.exists():
        user.groups.add(mitarbeiter_group)
```

---

## Troubleshooting

### Problem: User sieht keine Zeiteinträge
**Lösung:** Prüfen Sie, ob der User eine Rolle zugewiesen hat und ob `EmployeeInternal` mit dem User verknüpft ist.

### Problem: User kann nicht bearbeiten
**Lösung:** Prüfen Sie die Rolle (Mitarbeiter können nur eigene Einträge bearbeiten).

### Problem: Buttons werden nicht angezeigt
**Lösung:** Prüfen Sie, ob `adeazeit_permissions` Context Processor in `settings.py` eingetragen ist.

---

**Erstellt:** 21. November 2025  
**Status:** Implementiert und getestet

