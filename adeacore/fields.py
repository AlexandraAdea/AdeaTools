"""
Verschlüsselte Django-Model-Felder.
"""

from django.db import models
from django.core.exceptions import ImproperlyConfigured
from adeacore.encryption import get_encryption_manager


class EncryptedCharField(models.CharField):
    """
    Verschlüsseltes CharField.

    Speichert Werte verschlüsselt in der Datenbank,
    gibt sie automatisch entschlüsselt zurück.
    """

    def __init__(self, *args, **kwargs):
        """Initialisiert das verschlüsselte Feld."""
        super().__init__(*args, **kwargs)
        self._encryption_manager = get_encryption_manager()

    def from_db_value(self, value, expression, connection):
        """Entschlüsselt Wert beim Laden aus der Datenbank."""
        if value is None or value == "":
            return value
        try:
            return self._encryption_manager.decrypt(value)
        except Exception:
            # Falls Entschlüsselung fehlschlägt, könnte es ein alter verschlüsselter Wert sein
            # Prüfe, ob es wie ein verschlüsselter String aussieht (base64, lang)
            if isinstance(value, str) and len(value) > 50 and value.startswith("Z0FBQUFBQnBK"):
                # Alte verschlüsselte Daten, die nicht mehr entschlüsselt werden können
                # Rücke leeren String zurück (nicht benutzerfreundlich, verschlüsselte Strings zu zeigen)
                return ""
            # Falls es kein verschlüsselter String ist, als Klartext zurückgeben
            return value

    def to_python(self, value):
        """Konvertiert Wert zu Python-Objekt."""
        if isinstance(value, str) or value is None:
            return value
        return str(value)

    def get_prep_value(self, value):
        """Verschlüsselt Wert vor dem Speichern in die Datenbank."""
        if value is None or value == "":
            return value
        return self._encryption_manager.encrypt(str(value))


class EncryptedEmailField(EncryptedCharField):
    """
    Verschlüsseltes EmailField.

    Erbt von EncryptedCharField, fügt Email-Validierung hinzu.
    """

    pass  # Email-Validierung wird in Forms gemacht


class EncryptedTextField(models.TextField):
    """
    Verschlüsseltes TextField.

    Speichert Werte verschlüsselt in der Datenbank,
    gibt sie automatisch entschlüsselt zurück.
    """

    def __init__(self, *args, **kwargs):
        """Initialisiert das verschlüsselte Feld."""
        super().__init__(*args, **kwargs)
        self._encryption_manager = get_encryption_manager()

    def from_db_value(self, value, expression, connection):
        """Entschlüsselt Wert beim Laden aus der Datenbank."""
        if value is None or value == "":
            return value
        try:
            return self._encryption_manager.decrypt(value)
        except Exception:
            # Falls Entschlüsselung fehlschlägt, könnte es ein alter verschlüsselter Wert sein
            # Prüfe, ob es wie ein verschlüsselter String aussieht (base64, lang)
            if isinstance(value, str) and len(value) > 50 and value.startswith("Z0FBQUFBQnBK"):
                # Alte verschlüsselte Daten, die nicht mehr entschlüsselt werden können
                # Rücke leeren String zurück (nicht benutzerfreundlich, verschlüsselte Strings zu zeigen)
                return ""
            # Falls es kein verschlüsselter String ist, als Klartext zurückgeben
            return value

    def to_python(self, value):
        """Konvertiert Wert zu Python-Objekt."""
        if isinstance(value, str) or value is None:
            return value
        return str(value)

    def get_prep_value(self, value):
        """Verschlüsselt Wert vor dem Speichern in die Datenbank."""
        if value is None or value == "":
            return value
        return self._encryption_manager.encrypt(str(value))


class EncryptedDateField(models.CharField):
    """
    Verschlüsseltes DateField.

    Speichert Datum als verschlüsselten String,
    gibt es als Date-Objekt zurück.
    """

    def __init__(self, *args, **kwargs):
        """Initialisiert das verschlüsselte Feld."""
        # Wir speichern verschlüsselte Daten als TEXT/CHAR in der DB, nicht als DATE.
        # Hintergrund: SQLite konvertiert Spalten vom Typ "date" automatisch via Converter.
        # Das funktioniert nicht für verschlüsselte Werte und führt beim Lesen zu None.
        kwargs.setdefault("max_length", 1000)
        super().__init__(*args, **kwargs)
        self._encryption_manager = get_encryption_manager()

    def from_db_value(self, value, expression, connection):
        """Entschlüsselt Wert beim Laden aus der Datenbank."""
        if value is None:
            return value

        # Wenn bereits ein Date-Objekt, direkt zurückgeben
        if isinstance(value, (str, bytes)):
            try:
                decrypted = self._encryption_manager.decrypt(value)
                from django.utils.dateparse import parse_date

                return parse_date(decrypted)
            except Exception:
                # Falls Entschlüsselung fehlschlägt, versuche direkt zu parsen
                from django.utils.dateparse import parse_date

                return parse_date(value)

        return value

    def to_python(self, value):
        """Konvertiert Wert zu Python-Objekt."""
        if value is None:
            return value
        if isinstance(value, str):
            try:
                decrypted = self._encryption_manager.decrypt(value)
                from django.utils.dateparse import parse_date

                return parse_date(decrypted)
            except Exception:
                from django.utils.dateparse import parse_date

                return parse_date(value)
        return super().to_python(value)

    def get_prep_value(self, value):
        """Verschlüsselt Wert vor dem Speichern in die Datenbank."""
        if value is None or value == "":
            return None

        # Normalisiere zu ISO-Date-String
        if isinstance(value, str):
            from django.utils.dateparse import parse_date

            parsed = parse_date(value)
            if parsed is None:
                # Sieht nicht wie ein Datum aus → vermutlich bereits verschlüsselt
                return value
            date_str = parsed.isoformat()
        else:
            if hasattr(value, "date"):
                value = value.date()
            date_str = value.isoformat() if hasattr(value, "isoformat") else str(value)

        return self._encryption_manager.encrypt(date_str)

    def formfield(self, **kwargs):
        """In Forms weiterhin als DateField behandeln."""
        from django import forms

        # Wichtig: CharField würde `max_length` u.ä. an das FormField weiterreichen,
        # aber forms.DateField akzeptiert das nicht.
        defaults = {"form_class": forms.DateField}
        defaults.update(kwargs)
        defaults.pop("max_length", None)
        return models.Field.formfield(self, **defaults)

