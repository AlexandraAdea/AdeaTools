from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q
from decimal import Decimal
from datetime import date
from django.contrib.auth.models import User

from adeacore.models import Client
from django.utils import timezone


class UserProfile(models.Model):
    """
    Verknüpft Django User mit EmployeeInternal für präzise Rollenprüfung.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="adeazeit_profile",
        verbose_name="Benutzer"
    )
    employee = models.ForeignKey(
        "EmployeeInternal",
        on_delete=models.SET_NULL,
        related_name="user_profiles",
        null=True,
        blank=True,
        verbose_name="Mitarbeiterin",
        help_text="Verknüpfung zum EmployeeInternal für Zeiterfassung"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Benutzerprofil"
        verbose_name_plural = "Benutzerprofile"
        ordering = ["user__username"]

    def __str__(self):
        if self.employee:
            return f"{self.user.username} → {self.employee.name}"
        return f"{self.user.username} (kein Mitarbeiter zugeordnet)"


class EmployeeInternal(models.Model):
    """
    Eigene Mitarbeitende von Adea Treuhand (NICHT Mandanten).
    Diese werden für Zeiterfassung verwendet.
    """
    # Stammdaten
    code = models.CharField(
        "Mitarbeiterkürzel",
        max_length=20,
        unique=True,
        help_text="Eindeutiger Kurzcode für den Mitarbeiter (z.B. MM, EMP001)"
    )
    name = models.CharField("Name", max_length=255)
    function_title = models.CharField("Funktion", max_length=255, default="")
    rolle = models.CharField("Rolle", max_length=255, blank=True)
    
    # Arbeitszeitmodell
    employment_percent = models.DecimalField(
        "Beschäftigungsgrad (%)",
        max_digits=5,
        decimal_places=2,
        default=Decimal('100.00'),
        help_text="Beispiel: 100.00, 60.00"
    )
    weekly_soll_hours = models.DecimalField(
        "Wöchentliche Sollstunden",
        max_digits=5,
        decimal_places=2,
        default=Decimal('42.00'),
        help_text="Gesamte wöchentliche Sollstunden (z.B. 42.00 oder 40.00)"
    )
    weekly_working_days = models.DecimalField(
        "Wöchentliche Arbeitstage",
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="z.B. 5.0 / 4.5 / 4.0"
    )
    
    # Ferien & Feiertage
    vacation_days_per_year = models.DecimalField(
        "Ferientage pro Jahr",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="z.B. 20.00 / 25.00"
    )
    work_canton = models.CharField(
        "Arbeitskanton",
        max_length=50,
        null=True,
        blank=True,
        help_text="Für zukünftige Feiertagsmodelle"
    )
    holiday_model = models.CharField(
        "Feiertagsmodell",
        max_length=255,
        null=True,
        blank=True,
        help_text="Freitext"
    )
    
    # Beschäftigung
    employment_start = models.DateField(
        "Beschäftigungsbeginn",
        null=True,
        blank=True
    )
    employment_end = models.DateField(
        "Beschäftigungsende",
        null=True,
        blank=True
    )
    eintrittsdatum = models.DateField("Eintrittsdatum", null=True, blank=True)  # Legacy, wird automatisch aus employment_start gesetzt
    austrittsdatum = models.DateField("Austrittsdatum", null=True, blank=True)  # Legacy
    
    # Finanzen
    stundensatz = models.DecimalField(
        "Koeffizient",
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Koeffizient für die Verrechnung von Services (z.B. 1.3 = 30% Aufschlag auf Standard-Stundensatz)"
    )
    
    # Legacy-Felder (für Rückwärtskompatibilität)
    sollstunden_woche = models.DecimalField(
        "Sollstunden/Woche (Legacy)",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Veraltet - verwende weekly_soll_hours"
    )
    ferien_pro_jahr = models.DecimalField(
        "Ferien pro Jahr (Legacy)",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Veraltet - verwende vacation_days_per_year"
    )
    
    # Status & Notizen
    aktiv = models.BooleanField("Aktiv", default=True)
    notes = models.TextField("Notizen", null=True, blank=True)
    
    # System
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Interne Mitarbeiterin"
        verbose_name_plural = "Interne Mitarbeitende"

    def __str__(self):
        return self.name

    @property
    def internal_full_name(self):
        """Gibt den vollständigen Namen mit Funktion zurück."""
        if self.function_title:
            return f"{self.name} – {self.function_title}"
        return self.name

    def clean(self):
        """Validiere Eintritts- und Austrittsdatum."""
        if self.employment_end and self.employment_start and self.employment_end < self.employment_start:
            raise ValidationError({
                'employment_end': 'Beschäftigungsende darf nicht vor Beschäftigungsbeginn liegen.'
            })
        if self.austrittsdatum and self.eintrittsdatum and self.austrittsdatum < self.eintrittsdatum:
            raise ValidationError({
                'austrittsdatum': 'Austrittsdatum darf nicht vor Eintrittsdatum liegen.'
            })
    
    def is_active(self):
        """Prüft, ob der Mitarbeiter aktuell aktiv ist."""
        if not self.aktiv:
            return False
        from datetime import date
        today = date.today()
        # Prüfe beide Datumsfelder (neu und Legacy)
        if self.employment_end:
            if self.employment_end < today:
                return False
        if self.austrittsdatum:
            if self.austrittsdatum < today:
                return False
        return True


class ServiceType(models.Model):
    """
    Service-Typen (Kategorien) für Zeiterfassung.
    Entspricht den Excel-Kategorien.
    """
    code = models.CharField("Code", max_length=20, unique=True)
    name = models.CharField("Name", max_length=255)
    standard_rate = models.DecimalField(
        "Standard-Stundensatz",
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    billable = models.BooleanField("Verrechenbar", default=True)
    description = models.TextField("Beschreibung", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code"]
        verbose_name = "Service-Typ"
        verbose_name_plural = "Service-Typen"

    def __str__(self):
        return f"{self.code} – {self.name}"


class Task(models.Model):
    """
    Aufgaben für Mitarbeiter mit Fälligkeitsdatum und Priorität.
    Wichtig für Treuhand: Steuerfristen, MwSt-Abgaben, etc.
    """
    STATUS_CHOICES = [
        ('OFFEN', 'Offen'),
        ('IN_ARBEIT', 'In Arbeit'),
        ('WARTET', 'Wartet auf Kunde'),
        ('ERLEDIGT', 'Erledigt'),
    ]
    
    PRIORITAET_CHOICES = [
        ('NIEDRIG', 'Niedrig'),
        ('MITTEL', 'Mittel'),
        ('HOCH', 'Hoch'),
    ]
    
    titel = models.CharField(
        "Titel",
        max_length=255,
        help_text="Kurze Beschreibung der Aufgabe (z.B. 'Steuererklärung Müller AG')"
    )
    beschreibung = models.TextField(
        "Beschreibung",
        blank=True,
        help_text="Detaillierte Beschreibung (optional)"
    )
    status = models.CharField(
        "Status",
        max_length=20,
        choices=STATUS_CHOICES,
        default='OFFEN'
    )
    prioritaet = models.CharField(
        "Priorität",
        max_length=20,
        choices=PRIORITAET_CHOICES,
        default='MITTEL'
    )
    eingangsdatum = models.DateField(
        "Unterlagen eingegangen",
        null=True,
        blank=True,
        help_text="Wann hat der Kunde seine Unterlagen vollständig eingereicht?",
    )
    fälligkeitsdatum = models.DateField(
        "Fälligkeitsdatum",
        null=True,
        blank=True,
        help_text="Wichtig für Treuhand: Steuerfristen, MwSt-Abgaben, etc."
    )
    notizen = models.TextField(
        "Notizen",
        blank=True,
        help_text="Notizen zum aktuellen Stand (z.B. 'Warte auf Belege vom Kunden')"
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name='tasks',
        null=True,
        blank=True,
        verbose_name="Mandant",
        help_text="Optional: Mandant zuordnen (z.B. 'Steuererklärung Müller AG')"
    )
    mitarbeiter = models.ForeignKey(
        EmployeeInternal,
        on_delete=models.PROTECT,
        related_name='tasks',
        verbose_name="Mitarbeiterin"
    )
    erstellt_am = models.DateTimeField("Erstellt am", auto_now_add=True)
    erledigt_am = models.DateTimeField("Erledigt am", null=True, blank=True)
    archiviert = models.BooleanField("Archiviert", default=False, help_text="Erledigte Aufgaben werden nach 7 Tagen automatisch archiviert")
    tagesplan = models.BooleanField(
        "Heute einplanen",
        default=False,
        help_text="Markiert die Aufgabe für den Tagesplan (Widget 'Heute zu erledigen').",
    )
    updated_at = models.DateTimeField("Aktualisiert am", auto_now=True)
    
    class Meta:
        verbose_name = "Aufgabe"
        verbose_name_plural = "Aufgaben"
        ordering = ['prioritaet', 'fälligkeitsdatum', '-erstellt_am']
        indexes = [
            models.Index(fields=['mitarbeiter', 'status'], name='adeazeit_ta_mitarbe_492268_idx'),
            models.Index(fields=['client', 'status'], name='adeazeit_ta_client__018f96_idx'),
            models.Index(fields=['fälligkeitsdatum'], name='adeazeit_ta_fälligk_0cb4c5_idx'),
        ]
    
    def __str__(self):
        return f"{self.titel} ({self.get_status_display()})"
    
    def is_overdue(self):
        """Prüft ob die Aufgabe überfällig ist."""
        if self.fälligkeitsdatum and self.status != 'ERLEDIGT':
            from django.utils import timezone
            return self.fälligkeitsdatum < timezone.now().date()
        return False


class ZeitProject(models.Model):
    """
    Projekte pro Mandant für Zeiterfassung (optional für Treuhandarbeit).
    """
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="zeit_projects",
        verbose_name="Mandant"
    )
    name = models.CharField("Projektname", max_length=255)
    aktiv = models.BooleanField("Aktiv", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["client", "name"]
        verbose_name = "Zeit-Projekt"
        verbose_name_plural = "Zeit-Projekte"
        unique_together = [["client", "name"]]

    def __str__(self):
        return f"{self.client.name} – {self.name}"


class TimeEntry(models.Model):
    """
    Zeiteinträge (Kerndatenmodell).
    """
    mitarbeiter = models.ForeignKey(
        EmployeeInternal,
        on_delete=models.PROTECT,
        related_name="time_entries",
        verbose_name="Mitarbeiterin"
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name="time_entries",
        verbose_name="Mandant",
        null=True,
        blank=True,
        help_text="Optional: Für interne Arbeiten leer lassen"
    )
    project = models.ForeignKey(
        "ZeitProject",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="time_entries",
        verbose_name="Projekt"
    )
    datum = models.DateField("Datum")
    start = models.TimeField("Startzeit", null=True, blank=True)
    ende = models.TimeField("Endzeit", null=True, blank=True)
    dauer = models.DecimalField(
        "Dauer (Stunden)",
        max_digits=5,
        decimal_places=2
    )
    service_type = models.ForeignKey(
        ServiceType,
        on_delete=models.PROTECT,
        related_name="time_entries",
        verbose_name="Service-Typ"
    )
    kommentar = models.TextField("Kommentar", blank=True)
    billable = models.BooleanField("Verrechenbar", default=True)
    verrechnet = models.BooleanField("Verrechnet", default=False, help_text="Zeit wurde bereits verrechnet/invoiced")
    rate = models.DecimalField(
        "Stundensatz",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Wird automatisch aus Service-Typ übernommen, falls nicht gesetzt"
    )
    betrag = models.DecimalField(
        "Betrag",
        max_digits=10,
        decimal_places=2
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-datum", "-start"]
        verbose_name = "Zeiteintrag"
        verbose_name_plural = "Zeiteinträge"
        indexes = [
            models.Index(fields=["datum", "mitarbeiter"]),
            models.Index(fields=["client", "datum"]),
            models.Index(
                fields=["mitarbeiter", "datum", "start", "ende"],
                name="adeazeit_te_overlap_idx"
            ),
        ]

    def __str__(self):
        return f"{self.datum} – {self.mitarbeiter.name}"

    @staticmethod
    def _calculate_duration_minutes(start, ende):
        """
        Berechnet Dauer in Minuten zwischen Start- und Endzeit.
        
        Args:
            start: time-Objekt (Startzeit)
            ende: time-Objekt (Endzeit)
            
        Returns:
            int: Dauer in Minuten (kann negativ sein bei ungültigen Eingaben)
        """
        # Konvertiere zu Minuten für Vergleich
        start_minutes = start.hour * 60 + start.minute
        end_minutes = ende.hour * 60 + ende.minute
        
        # Wenn Endzeit vor Startzeit (über Mitternacht), addiere 24 Stunden
        if end_minutes <= start_minutes:
            end_minutes += 24 * 60
        
        # Berechne Differenz
        return end_minutes - start_minutes

    def clean(self):
        """Validiere Zeiteintrag."""
        # Prüfe, ob Startzeit ohne Endzeit ausgefüllt ist
        if self.start and not self.ende:
            raise ValidationError({
                'ende': 'Bitte geben Sie die Endzeit ein, wenn Sie eine Startzeit angegeben haben.'
            })
        
        # Prüfe, ob Endzeit ohne Startzeit ausgefüllt ist
        if self.ende and not self.start:
            raise ValidationError({
                'start': 'Bitte geben Sie die Startzeit ein, wenn Sie eine Endzeit angegeben haben.'
            })
        
        if self.ende and self.start:
            # Verwende Helper-Methode für Dauer-Berechnung und validiere
            diff_minutes = self._calculate_duration_minutes(self.start, self.ende)
            # Mindestens 1 Minute Unterschied erforderlich
            if diff_minutes < 1:
                raise ValidationError({
                    'ende': 'Endzeit muss mindestens 1 Minute nach Startzeit liegen.'
                })
        
        # Prüfe Dauer nur, wenn sie gesetzt ist (kann bei neuen Einträgen noch fehlen)
        if hasattr(self, 'dauer') and self.dauer is not None and self.dauer <= 0:
            raise ValidationError({
                'dauer': 'Dauer muss größer als 0 sein.'
            })
        
        # Prüfe auf Zeitüberschneidungen für denselben Mitarbeiter
        if self.mitarbeiter and self.datum and self.start and self.ende:
            # Finde alle Zeiteinträge für denselben Mitarbeiter am selben Tag mit Start- und Endzeit
            overlapping = TimeEntry.objects.filter(
                mitarbeiter=self.mitarbeiter,
                datum=self.datum,
                start__isnull=False,
                ende__isnull=False
            ).exclude(
                pk=self.pk if self.pk else None
            ).filter(
                # Überschneidung: Start liegt vor dem Ende des neuen Zeitraums UND Ende liegt nach dem Start des neuen Zeitraums
                start__lt=self.ende,
                ende__gt=self.start
            )
            
            if overlapping.exists():
                overlapping_entry = overlapping.first()
                raise ValidationError({
                    'start': f'Zeitüberschneidung! Es existiert bereits ein Eintrag für {self.mitarbeiter.name} '
                            f'am {self.datum.strftime("%d.%m.%Y")} von {overlapping_entry.start.strftime("%H:%M")} bis {overlapping_entry.ende.strftime("%H:%M")}.',
                    'ende': 'Bitte wählen Sie eine andere Zeit oder bearbeiten Sie den bestehenden Eintrag.'
                })

    def save(self, *args, **kwargs):
        """Automatische Berechnung von Rate und Betrag."""
        from django.db import transaction
        from datetime import datetime, timedelta
        from .timeentry_calc import calculate_timeentry_rate, calculate_timeentry_amount
        
        with transaction.atomic():
            # Berechne Dauer automatisch aus Start- und Endzeit, falls beide vorhanden sind
            if self.start and self.ende:
                # Verwende Helper-Methode für Dauer-Berechnung
                diff_minutes = self._calculate_duration_minutes(self.start, self.ende)
                # Konvertiere Minuten zu Stunden
                self.dauer = Decimal(str(diff_minutes / 60)).quantize(Decimal('0.01'))
            
            # WICHTIG: Für korrekte Fakturierung muss IMMER der aktuelle Stundensatz aus ServiceType verwendet werden
            # UND der Koeffizient des Mitarbeiters angewendet werden
            if self.service_type:
                # Koeffizient des Mitarbeiters IMMER anwenden (z.B. 0.5 = 50% des Standard-Stundensatzes)
                # Auch wenn rate bereits gesetzt ist, muss sie neu berechnet werden, damit Koeffizient-Änderungen wirksam werden
                self.rate = calculate_timeentry_rate(service_type=self.service_type, employee=self.mitarbeiter)
            
            # billable aus ServiceType übernehmen, falls nicht explizit gesetzt
            if not hasattr(self, '_billable_set'):
                if self.service_type:
                    self.billable = self.service_type.billable
            
            # Betrag IMMER neu berechnen (für korrekte Fakturierung)
            # Verwendet den aktuellen rate und dauer
            self.betrag = calculate_timeentry_amount(rate=self.rate, dauer=self.dauer)
            
            # Validierung
            self.full_clean()
            
            super().save(*args, **kwargs)


class Absence(models.Model):
    """
    Abwesenheiten (Ferien, Krankheit, Feiertage, etc.).
    """
    TYPE_CHOICES = [
        ("FERIEN", "Ferien"),
        ("KRANK", "Krankheit"),
        ("UNFALL", "Unfall"),
        ("FEIERTAG", "Feiertag"),
        ("UNBEZAHLT", "Unbezahlter Urlaub"),
        ("WEITERBILDUNG", "Weiterbildung"),
        ("SONSTIGES", "Sonstiges"),
    ]

    employee = models.ForeignKey(
        EmployeeInternal,
        on_delete=models.CASCADE,
        related_name="absences",
        verbose_name="Mitarbeiterin"
    )
    absence_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name="Typ"
    )
    date_from = models.DateField(verbose_name="Von Datum")
    date_to = models.DateField(verbose_name="Bis Datum")
    full_day = models.BooleanField(
        default=True,
        verbose_name="Ganztägig",
        help_text="Wenn nicht ganztägig, Stunden angeben"
    )
    hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Stunden",
        help_text="Nur bei Teilzeit-Abwesenheit"
    )
    comment = models.TextField(blank=True, verbose_name="Kommentar")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")

    class Meta:
        verbose_name = "Abwesenheit"
        verbose_name_plural = "Abwesenheiten"
        ordering = ["-date_from", "employee"]
        indexes = [
            models.Index(fields=["employee", "date_from"]),
        ]

    def __str__(self):
        return f"{self.employee.name} – {self.get_absence_type_display()} {self.date_from}–{self.date_to}"

    def clean(self):
        """Validiere Abwesenheit."""
        if self.date_from > self.date_to:
            raise ValidationError({
                'date_to': 'Bis-Datum muss nach oder gleich Von-Datum sein.'
            })
        
        if self.full_day:
            if self.hours is not None:
                raise ValidationError({
                    'hours': 'Bei ganztägiger Abwesenheit dürfen keine Stunden angegeben werden.'
                })
        else:
            if self.hours is None or self.hours <= 0:
                raise ValidationError({
                    'hours': 'Bei Teilzeit-Abwesenheit müssen Stunden > 0 angegeben werden.'
                })

    @property
    def is_aktiv(self):
        """Prüft, ob die Abwesenheit aktuell aktiv ist."""
        today = date.today()
        return self.date_from <= today <= self.date_to
    
    def get_absence_type_display(self):
        """Gibt den Anzeigenamen des Typs zurück."""
        return dict(self.TYPE_CHOICES).get(self.absence_type, self.absence_type)


class Holiday(models.Model):
    """
    Feiertage als Daten (nicht hard-coded).
    """
    name = models.CharField("Name", max_length=255)
    date = models.DateField("Datum")
    canton = models.CharField(
        "Kanton",
        max_length=10,
        blank=True,
        help_text="z.B. 'AG', 'ZH'. Leer = CH-weit"
    )
    is_official = models.BooleanField(
        "Offizieller Feiertag",
        default=True
    )

    class Meta:
        verbose_name = "Feiertag"
        verbose_name_plural = "Feiertage"
        unique_together = ("date", "canton")
        ordering = ["date"]

    def __str__(self):
        label = self.canton or "CH"
        return f"{self.date} – {self.name} ({label})"


class RunningTimeEntry(models.Model):
    """
    Laufender Timer für Live-Zeiterfassung.
    """
    mitarbeiter = models.ForeignKey(
        EmployeeInternal,
        on_delete=models.CASCADE,
        related_name="running_timer",
        verbose_name="Mitarbeiterin"
    )
    client = models.ForeignKey(
        Client,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="running_timers",
        verbose_name="Mandant",
        help_text="Nur bei externen Leistungen. Bei internen Leistungen leer lassen."
    )
    service_type = models.ForeignKey(
        ServiceType,
        on_delete=models.PROTECT,
        related_name="running_timers",
        verbose_name="Service-Typ"
    )
    projekt = models.ForeignKey(
        "ZeitProject",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="running_timers",
        verbose_name="Projekt"
    )
    beschreibung = models.TextField("Beschreibung", blank=True)
    start_time = models.DateTimeField("Startzeit", auto_now_add=True)
    datum = models.DateField("Datum", auto_now_add=True)

    class Meta:
        verbose_name = "Laufender Zeiteintrag"
        verbose_name_plural = "Laufende Zeiteinträge"
        constraints = [
            models.UniqueConstraint(fields=['mitarbeiter'], name='one_timer_per_employee')
        ]

    def __str__(self):
        from django.utils import timezone
        return f"{self.mitarbeiter.name} – Timer läuft seit {timezone.localtime(self.start_time).strftime('%H:%M')}"

    def get_duration_seconds(self):
        from django.utils import timezone
        delta = timezone.now() - self.start_time
        return int(delta.total_seconds())

    def get_duration_hours(self):
        from decimal import Decimal
        seconds = self.get_duration_seconds()
        hours = Decimal(seconds) / Decimal(3600)
        # Runde auf 2 Dezimalstellen und stelle sicher, dass mindestens 0.01 Stunden (36 Sekunden)
        rounded = hours.quantize(Decimal('0.01'))
        # Mindestdauer: 0.01 Stunden (36 Sekunden) um Validierungsfehler zu vermeiden
        if rounded < Decimal('0.01'):
            return Decimal('0.01')
        return rounded
