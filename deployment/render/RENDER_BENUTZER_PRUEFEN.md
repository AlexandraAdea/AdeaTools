# 🔍 Render Benutzer & Rollen prüfen

## Prüfe ob alles korrekt ist:

### In Render Shell:

**1. Prüfe alle Benutzer:**
```bash
python manage.py shell
```

Dann in Python Shell:
```python
from django.contrib.auth.models import User, Group

# Zeige alle Benutzer
for user in User.objects.all():
    print(f"User: {user.username}, Groups: {[g.name for g in user.groups.all()]}, Superuser: {user.is_superuser}")

# Zeige alle Gruppen
for group in Group.objects.all():
    print(f"Group: {group.name}, Users: {[u.username for u in group.user_set.all()]}")
```

**2. Prüfe ob Aivanova Admin-Rolle hat:**
```python
aivanova = User.objects.get(username="Aivanova")
admin_group = Group.objects.get(name="AdeaZeit Admin")
print(f"Aivanova in Admin-Group: {admin_group in aivanova.groups.all()}")
```

**3. Falls nicht, weise zu:**
```python
aivanova.groups.add(admin_group)
aivanova.save()
print("Aivanova wurde Admin-Rolle zugewiesen")
```

**4. Prüfe Mitarbeitende:**
```python
from adeazeit.models import EmployeeInternal, UserProfile

# Zeige alle Mitarbeitenden
for emp in EmployeeInternal.objects.all():
    print(f"Employee: {emp.name} ({emp.code})")

# Zeige UserProfile-Verknüpfungen
for profile in UserProfile.objects.all():
    print(f"User: {profile.user.username} -> Employee: {profile.employee.name if profile.employee else 'Keine'}")
```

**5. Exit Shell:**
```python
exit()
```

---

## ✅ Was sollte sein:

- **Aivanova** → `AdeaZeit Admin` Group
- **ai** → `AdeaZeit Mitarbeiter` Group + UserProfile mit EmployeeInternal
- **ei** → `AdeaZeit Mitarbeiter` Group + UserProfile mit EmployeeInternal

---

## 🔧 Falls etwas fehlt:

**Admin-Rolle zuweisen:**
```python
from django.contrib.auth.models import User, Group
user = User.objects.get(username="Aivanova")
group = Group.objects.get(name="AdeaZeit Admin")
user.groups.add(group)
```

**Mitarbeiter-Rolle zuweisen:**
```python
user = User.objects.get(username="ai")
group = Group.objects.get(name="AdeaZeit Mitarbeiter")
user.groups.add(group)
```

**UserProfile verknüpfen:**
```python
from adeazeit.models import EmployeeInternal, UserProfile
user = User.objects.get(username="ai")
employee = EmployeeInternal.objects.get(code="AI")  # oder name="...")
profile, created = UserProfile.objects.get_or_create(user=user)
profile.employee = employee
profile.save()
```

