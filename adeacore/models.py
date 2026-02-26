from django.db import models
from django.db import transaction
from adeacore.fields import EncryptedCharField, EncryptedEmailField, EncryptedTextField, EncryptedDateField
from adeacore.audit import get_audit_logger


class Client(models.Model):
    CLIENT_TYPES = [
        ("FIRMA", "Firma"),
        ("PRIVAT", "Privatperson"),
    ]
    
    STATUS_CHOICES = [
        ("AKTIV", "Aktiv"),
        ("INAKTIV", "Inaktiv"),
        ("POTENZIELL", "Potenziell"),
        ("GESPERRT", "Gesperrt"),
    ]

    ZAHLUNGSVERHALTEN_CHOICES = [
        ("SCHNELL", "⭐⭐⭐⭐ Schnell zahlt"),
        ("NORMAL", "⭐⭐⭐ Normal / Neukunde"),
        ("LANGSAM", "⭐⭐ Langsam zahlt"),
        ("SCHLECHT", "⭐ Schlecht zahlt"),
    ]
    
    # Grunddaten
    name = models.CharField("Name", max_length=255)
    client_type = models.CharField(
        "Typ",
        max_length=10,
        choices=CLIENT_TYPES,
        default="FIRMA",
        help_text="Mandantentyp: Firma (für Lohnbuchhaltung) oder Privatperson (nur für Zeiterfassung)",
    )
    status = models.CharField(
        "Status",
        max_length=20,
        choices=STATUS_CHOICES,
        default="AKTIV",
        help_text="Status des Mandanten",
    )
    status_grund = models.TextField(
        "Grund für Status",
        blank=True,
        help_text="Grund für Inaktivität oder Sperrung (optional)",
    )
    status_geaendert_am = models.DateTimeField(
        "Status geändert am",
        null=True,
        blank=True,
        help_text="Datum der letzten Status-Änderung",
    )
    
    # Kontakt (verschlüsselt)
    email = EncryptedEmailField("E-Mail", max_length=1000, blank=True, null=True)
    phone = EncryptedCharField("Telefon", max_length=500, blank=True)
    kontaktperson_name = models.CharField(
        "Kontaktperson",
        max_length=255,
        blank=True,
        help_text="Name der Kontaktperson (für FIRMA)",
    )
    
    # Adresse (verschlüsselt)
    street = EncryptedCharField("Strasse", max_length=1000, blank=True)
    house_number = EncryptedCharField("Hausnummer", max_length=500, blank=True)
    zipcode = EncryptedCharField("PLZ", max_length=500, blank=True)
    city = EncryptedCharField("Ort", max_length=1000, blank=True)
    
    # MWST & Rechnungsdaten (nur FIRMA) - MWST-Nummer verschlüsselt
    mwst_pflichtig = models.BooleanField(
        "MWST-pflichtig",
        default=False,
        help_text="Ist der Mandant MWST-pflichtig? (nur FIRMA)",
    )
    mwst_nr = EncryptedCharField(
        "MWST-Nummer / UID",
        max_length=500,
        blank=True,
        help_text="MWST-Nummer / UID (in CH identisch, nur FIRMA)",
    )
    rechnungs_email = EncryptedEmailField(
        "Rechnungs-E-Mail",
        max_length=1000,
        blank=True,
        null=True,
        help_text="E-Mail-Adresse für Rechnungen (nur FIRMA)",
    )
    zahlungsziel_tage = models.PositiveIntegerField(
        "Zahlungsziel (Tage)",
        default=30,
        help_text="Zahlungsziel in Tagen (nur FIRMA)",
    )
    zahlungsverhalten = models.CharField(
        "Zahlungsverhalten",
        max_length=20,
        choices=ZAHLUNGSVERHALTEN_CHOICES,
        default="NORMAL",
        help_text="Einschätzung des Zahlungsverhaltens für Priorisierung in Aufgabenlisten.",
    )
    
    # Steuerdaten (nur PRIVAT) - verschlüsselt
    geburtsdatum = EncryptedDateField(
        "Geburtsdatum",
        blank=True,
        null=True,
        help_text="Geburtsdatum (nur PRIVAT)",
    )
    steuerkanton = EncryptedCharField(
        "Steuerkanton",
        max_length=500,
        blank=True,
        help_text="Steuerkanton (nur PRIVAT)",
    )
    
    # Weitere Daten
    # HINWEIS: uid wurde entfernt - verwende mwst_nr (in CH identisch)
    # uid ist jetzt ein Property, das mwst_nr zurückgibt
    interne_notizen = models.TextField(
        "Interne Notizen",
        blank=True,
        help_text="Interne Notizen und Bemerkungen",
    )
    
    # Arbeitgeberort (für kantonale Sozialversicherungsbeiträge)
    work_canton = models.CharField(
        "Arbeitskanton",
        max_length=50,
        blank=True,
        null=True,
        help_text="Kanton des Arbeitgebersitzes (für FAK und andere kantonale Beiträge). Z.B. 'AG', 'ZH', 'BE'",
    )
    
    # Module-Aktivierung
    lohn_aktiv = models.BooleanField(
        "AdeaLohn aktiviert",
        default=False,
        help_text="Aktiviert die Lohnbuchhaltung (AdeaLohn) für diesen Mandanten. Nur bei FIRMA-Mandanten relevant.",
    )
    
    # Sachbearbeiter für AdeaLohn
    sachbearbeiter = models.ForeignKey(
        "adeazeit.EmployeeInternal",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lohn_clients",
        verbose_name="Sachbearbeiter (AdeaLohn)",
        help_text="Sachbearbeiter, der für diesen Mandanten Zugriff auf AdeaLohn hat. Nur bei FIRMA-Mandanten mit aktiviertem Lohnmodul relevant.",
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
    
    def is_firma(self):
        """Prüft ob Client eine Firma ist."""
        return self.client_type == "FIRMA"
    
    def is_privat(self):
        """Prüft ob Client eine Privatperson ist."""
        return self.client_type == "PRIVAT"
    
    @property
    def uid(self):
        """
        UID Property - gibt MWST-Nummer zurück (in CH identisch).
        Für Rückwärtskompatibilität beibehalten.
        """
        return self.mwst_nr
    
    def save(self, *args, **kwargs):
        """Speichert mit Audit-Logging."""
        is_new = self.pk is None
        old_instance = None
        
        if not is_new:
            try:
                old_instance = Client.objects.get(pk=self.pk)
            except Client.DoesNotExist:
                pass
        
        # Aktualisiere status_geaendert_am wenn Status geändert wurde
        if old_instance and old_instance.status != self.status:
            from django.utils import timezone
            self.status_geaendert_am = timezone.now()
        
        super().save(*args, **kwargs)
        
        # Audit-Log
        audit_logger = get_audit_logger()
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Versuche aktuellen Benutzer zu finden (aus Thread-Local oder Request)
        user = getattr(self, '_current_user', None)
        
        changes = {}
        if old_instance:
            # Track Änderungen
            for field in ['name', 'email', 'phone', 'mwst_nr', 'rechnungs_email', 'geburtsdatum', 'status']:
                old_value = getattr(old_instance, field, None)
                new_value = getattr(self, field, None)
                if old_value != new_value:
                    changes[field] = {'old': str(old_value)[:50], 'new': str(new_value)[:50]}
        
        action = 'CREATE' if is_new else 'UPDATE'
        audit_logger.log_action(
            user=user,
            action=action,
            model_name='Client',
            object_id=self.pk,
            object_repr=str(self),
            changes=changes if changes else None
        )


class Employee(models.Model):
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="employees",
    )
    
    # Identifikation
    personalnummer = models.CharField(
        "Personal-Nr.",
        max_length=50,
        blank=True,
        help_text="Eindeutige Personalnummer des Mitarbeiters",
    )
    
    # Personendaten
    first_name = models.CharField("Vorname", max_length=100)
    last_name = models.CharField("Nachname", max_length=100)
    geburtsdatum = EncryptedDateField(
        "Geburtsdatum",
        blank=True,
        null=True,
        help_text="Geburtsdatum des Mitarbeiters",
    )
    ahv_nummer = EncryptedCharField(
        "AHV-Nummer",
        max_length=50,
        blank=True,
        help_text="AHV-Nummer im Format 756.XXXX.XXXX.XX",
    )
    
    # Adresse (verschlüsselt)
    street = EncryptedCharField("Strasse", max_length=1000, blank=True)
    zipcode = EncryptedCharField("PLZ", max_length=500, blank=True)
    city = EncryptedCharField("Ort", max_length=1000, blank=True)
    country = EncryptedCharField(
        "Land",
        max_length=500,
        blank=True,
        default="CH",
        help_text="ISO-Code (CH, DE, FR, AT) für Grenzgänger",
    )
    
    # Kontakt (verschlüsselt)
    email = EncryptedEmailField("E-Mail", max_length=1000, blank=True, null=True)
    phone = EncryptedCharField("Telefon", max_length=500, blank=True)
    mobile = EncryptedCharField("Mobiltelefon", max_length=500, blank=True)
    
    # Zivilstand
    ZIVILSTAND_CHOICES = [
        ("LEDIG", "Ledig"),
        ("VERHEIRATET", "Verheiratet"),
        ("GESCHIEDEN", "Geschieden"),
        ("VERWITWET", "Verwitwet"),
        ("KONKUBINAT", "Konkubinat"),
        ("UNBEKANNT", "Unbekannt"),
    ]
    zivilstand = models.CharField(
        "Zivilstand",
        max_length=20,
        choices=ZIVILSTAND_CHOICES,
        default="UNBEKANNT",
        help_text="Zivilstand des Mitarbeiters",
    )
    
    # Beschäftigung
    eintrittsdatum = models.DateField(
        "Eintrittsdatum",
        blank=True,
        null=True,
        help_text="Datum des Eintritts in die Firma",
    )
    austrittsdatum = models.DateField(
        "Austrittsdatum",
        blank=True,
        null=True,
        help_text="Datum des Austritts aus der Firma",
    )
    
    # Tätigkeit
    role = models.CharField("Rolle/Tätigkeit", max_length=255, blank=True)
    taetigkeit_branche = models.CharField(
        "Tätigkeit/Branche",
        max_length=255,
        blank=True,
        help_text="z.B. 'Coiffeur', 'Gastro'",
    )
    
    # Lohn
    hourly_rate = models.DecimalField(
        "Stundensatz (CHF)",
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text="Stundensatz für Stundenlöhne. Wenn 0, wird Monatslohn verwendet.",
    )
    monthly_salary = models.DecimalField(
        "Monatslohn (CHF)",
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Monatlicher Bruttolohn für Monatslöhne. Wenn 0, wird Stundenlohn verwendet.",
    )
    is_rentner = models.BooleanField(
        default=False,
        help_text="Ist der Mitarbeiter Rentner?",
    )
    ahv_freibetrag_aktiv = models.BooleanField(
        default=True,
        help_text="Rentnerfreibetrag 1400/Monat anwenden",
    )
    weekly_hours = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        default=0,
        help_text="Wöchentliche Arbeitsstunden",
    )
    pensum = models.DecimalField(
        "Arbeitspensum (%)",
        max_digits=5,
        decimal_places=1,
        default=100,
        help_text="Arbeitspensum in Prozent (z.B. 80 für 80%, 100 für 100%)",
    )
    iban = EncryptedCharField(
        "IBAN",
        max_length=100,
        blank=True,
        help_text="IBAN für Lohnauszahlung",
    )
    vacation_weeks = models.IntegerField(
        default=5,
        choices=[(4, "4 Wochen"), (5, "5 Wochen"), (6, "6 Wochen")],
        help_text="Anzahl Ferienwochen (für Ferienentschädigung bei Stundenlöhnen)",
    )
    nbu_pflichtig = models.BooleanField(
        default=False,
        help_text="NBU-Pflicht (AN). Automatisch bei >8h/Woche, aber manuell überschreibbar.",
    )
    qst_pflichtig = models.BooleanField(
        default=False,
        help_text="Quellensteuerpflichtig",
    )
    qst_tarif = models.CharField(
        max_length=5,
        blank=True,
        null=True,
        help_text="QST-Tarif: Familienstand (A=alleinstehend, B=verheiratet) oder vollständig (z.B. 'A0N', 'B1Y'). "
                  "Vollständiges Format: [Familienstand][Kinder][Kirchensteuer] mit N=ohne, Y=mit Kirche. "
                  "Wenn nur Familienstand angegeben, wird Tarif automatisch aus Kindern und Kirchensteuer ergänzt.",
    )
    qst_kinder = models.PositiveIntegerField(
        default=0,
        help_text="Anzahl Kinder für QST-Berechnung",
    )
    qst_kirchensteuer = models.BooleanField(
        default=False,
        help_text="Kirchensteuerpflichtig (wird in qst_effective_tarif kodiert, z.B. A0Y statt A0N)",
    )
    qst_prozent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="QST-Prozentsatz (z.B. 5.00 für 5%)",
    )
    qst_fixbetrag = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="QST-Fixbetrag (hat Vorrang vor Prozentsatz)",
    )
    alv_ytd_basis = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="ALV YTD-Basis (Year-to-Date) für Kappung bei 148'200 CHF/Jahr",
    )
    uvg_ytd_basis = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="UVG YTD-Basis (Year-to-Date) für Kappung bei 148'200 CHF/Jahr",
    )
    bvg_ytd_basis = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="BVG YTD-Basis (Year-to-Date) für Jahreslohnberechnung",
    )
    bvg_ytd_insured_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="BVG YTD versicherter Lohn (Year-to-Date) für monatliche Berechnung",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def clean(self):
        """Validiert dass Employee nur bei FIRMA-Clients mit aktiviertem Lohnmodul erstellt werden kann."""
        from django.core.exceptions import ValidationError
        
        if self.client:
            if self.client.client_type != "FIRMA":
                raise ValidationError({
                    'client': 'Nur Firmen-Mandanten können Mitarbeitende haben. '
                             f'Der ausgewählte Mandant "{self.client.name}" ist eine Privatperson.'
                })
            if not self.client.lohn_aktiv:
                raise ValidationError({
                    'client': 'Das Lohnmodul ist für diesen Mandanten nicht aktiviert. '
                             f'Bitte aktivieren Sie AdeaLohn für "{self.client.name}" in AdeaDesk.'
                })
    
    def save(self, *args, **kwargs):
        """Validiert vor dem Speichern und setzt automatische Felder."""
        from decimal import Decimal
        
        # Automatische NBU-Pflicht bei >8h/Woche (Schweizer Recht)
        NBU_THRESHOLD_HOURS = Decimal("8")
        if self.weekly_hours > NBU_THRESHOLD_HOURS:
            self.nbu_pflichtig = True
        
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def qst_effective_tarif(self):
        """
        Generiert den vollständigen QST-Tarif im Format [Familienstand][Kinder][Kirchensteuer].
        Beispiel: A0N (alleinstehend, 0 Kinder, ohne Kirche), B1Y (verheiratet, 1 Kind, mit Kirche).
        
        Wenn qst_tarif bereits im vollständigen Format ist (z.B. A0N), wird es direkt verwendet.
        Sonst wird es aus qst_tarif[0] (Familienstand), qst_kinder und qst_kirchensteuer generiert.
        """
        if not self.qst_tarif:
            return None
        
        # Wenn Tarif bereits im vollständigen Format (z.B. A0N, B1Y), direkt verwenden
        if len(self.qst_tarif) >= 3 and self.qst_tarif[-1] in ['N', 'Y']:
            return self.qst_tarif
        
        # Sonst aus Komponenten generieren
        familienstand = self.qst_tarif[0] if self.qst_tarif else 'A'
        kirchensteuer_code = 'Y' if self.qst_kirchensteuer else 'N'
        return f"{familienstand}{self.qst_kinder}{kirchensteuer_code}"


class Project(models.Model):
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class TimeRecord(models.Model):
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="time_records",
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        related_name="time_records",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="time_records",
    )
    date = models.DateField()
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        project_name = self.project.name if self.project else "Allgemein"
        return f"{self.employee} – {project_name} ({self.date})"


class PayrollRecord(models.Model):
    STATUS_CHOICES = [
        ("ENTWURF", "Entwurf"),
        ("GEPRUEFT", "Geprüft"),
        ("ABGERECHNET", "Abgerechnet"),
        ("GESPERRT", "Gesperrt"),
    ]
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="payroll_records",
    )
    month = models.IntegerField()
    year = models.IntegerField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="ENTWURF",
        help_text="Status des Lohnlaufs. Gesperrte Löhne können nicht mehr bearbeitet werden.",
    )
    bruttolohn = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ahv_basis = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    alv_basis = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bvg_basis = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    uv_basis = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    qst_basis = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ahv_effective_basis = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ahv_employee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ahv_employer = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    alv_effective_basis = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    alv_employee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    alv_employer = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    uvg_effective_basis = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bu_employer = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bu_employee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    nbu_employee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ktg_effective_basis = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ktg_employee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ktg_employer = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bvg_insured_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bvg_employee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bvg_employer = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    manual_bvg_employee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Manueller BVG-Arbeitnehmerbeitrag (falls nicht automatisch berechnet). Wird zu berechneten Beiträgen addiert."
    )
    manual_bvg_employer = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Manueller BVG-Arbeitgeberbeitrag (falls nicht automatisch berechnet). Wird zu berechneten Beiträgen addiert."
    )
    qst_abzug = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    qst_prozent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="QST-Prozentsatz für diesen Monat (z.B. 5.00 für 5%). Kann monatlich variieren bei Stundenlöhnen.",
    )
    fak_employer = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="FAK-Beitrag Arbeitgeber (1.0% vom Bruttolohn, gemäss Excel-Vorlage)",
    )
    vk_employer = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Verwaltungskosten Arbeitgeber (3.0% vom Total AHV-Beitrag, gemäss Excel-Vorlage)",
    )
    nettolohn = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-year", "-month", "employee__last_name"]
        verbose_name = "Payroll Record"
        verbose_name_plural = "Payroll Records"
        unique_together = ("employee", "month", "year")

    def __str__(self):
        return f"{self.employee} – {self.month:02d}/{self.year}"
    
    def is_locked(self) -> bool:
        """Prüft, ob dieser PayrollRecord gesperrt ist und nicht mehr bearbeitet werden kann."""
        return self.status in ("ABGERECHNET", "GESPERRT")
    
    def clean(self):
        """Validiert PayrollRecord-Daten vor dem Speichern."""
        from django.core.exceptions import ValidationError as DjangoValidationError
        ValidationError = DjangoValidationError  # Für Verwendung in save()
        
        # Prüfe Monat (1-12)
        if self.month < 1 or self.month > 12:
            raise ValidationError({"month": "Monat muss zwischen 1 und 12 liegen."})
        
        # Prüfe Jahr (2000-2100)
        if self.year < 2000 or self.year > 2100:
            raise ValidationError({"year": "Jahr muss zwischen 2000 und 2100 liegen."})
        
        # Prüfe auf Duplikate (zusätzlich zu unique_together für bessere Fehlermeldung)
        # Nur wenn employee gesetzt ist (kann bei Form-Validierung noch fehlen)
        if hasattr(self, 'employee_id') and self.employee_id:
            # Sicherheitsprüfung: Employee muss zu einem FIRMA-Client gehören
            try:
                employee = Employee.objects.select_related('client').get(pk=self.employee_id)
                if employee.client.client_type != "FIRMA":
                    raise ValidationError({
                        'employee': 'Payroll kann nur für Mitarbeitende von Firmen erstellt werden. '
                                   f'Der Mitarbeiter gehört zu "{employee.client.name}" (Privatperson).'
                    })
            except Employee.DoesNotExist:
                pass
            
            if self.pk:  # Nur bei Updates prüfen
                existing = PayrollRecord.objects.filter(
                    employee_id=self.employee_id,
                    month=self.month,
                    year=self.year
                ).exclude(pk=self.pk).first()
                if existing:
                    raise ValidationError(
                        f"Es existiert bereits eine Lohnabrechnung für diesen Mitarbeiter "
                        f"im Monat {self.month}/{self.year}."
                    )
            else:  # Bei neuen Records
                existing = PayrollRecord.objects.filter(
                    employee_id=self.employee_id,
                    month=self.month,
                    year=self.year
                ).first()
                if existing:
                    raise ValidationError(
                        f"Es existiert bereits eine Lohnabrechnung für diesen Mitarbeiter "
                        f"im Monat {self.month}/{self.year}."
                    )

    def recompute_bases_from_items(self):
        """
        Berechnet alle Basen aus PayrollItems und rundet auf 2 Dezimalstellen.
        
        WICHTIG: Alle Werte müssen auf 2 Dezimalstellen gerundet werden,
        da die DecimalField-Felder max. 2 Dezimalstellen erlauben.
        """
        from decimal import Decimal, ROUND_HALF_UP

        gross = Decimal("0.00")
        ahv = Decimal("0.00")
        alv = Decimal("0.00")
        bvg = Decimal("0.00")
        uv = Decimal("0.00")
        qst = Decimal("0.00")

        items_qs = getattr(self, "_items_qs", None)
        items = items_qs if items_qs is not None else self.items.select_related("wage_type")

        for item in items:
            total = item.total
            wt = item.wage_type
            if wt.is_lohnwirksam:
                gross += total
            if wt.ahv_relevant:
                ahv += total
            if wt.alv_relevant:
                alv += total
            if wt.bvg_relevant:
                bvg += total
            if wt.uv_relevant:
                uv += total
            if wt.qst_relevant:
                qst += total

        # Auf 2 Dezimalstellen runden (für DecimalField mit decimal_places=2)
        def round_to_2_decimals(value):
            """Rundet Decimal-Wert auf 2 Dezimalstellen."""
            return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        self.bruttolohn = round_to_2_decimals(gross)
        self.ahv_basis = round_to_2_decimals(ahv)
        self.alv_basis = round_to_2_decimals(alv)
        self.bvg_basis = round_to_2_decimals(bvg)
        self.uv_basis = round_to_2_decimals(uv)
        self.qst_basis = round_to_2_decimals(qst)
        
        # Manuelle BVG-Beiträge werden jetzt direkt im PayrollRecord gespeichert (manual_bvg_employee, manual_bvg_employer)
        # Keine Extraktion aus PayrollItems mehr nötig
    
    def _handle_january_ytd_reset(self):
        """
        Setzt YTD-Basen für Januar zurück (Jahresreset).
        
        Verwendet select_for_update() um Race Conditions zu vermeiden.
        """
        from decimal import Decimal
        import logging
        
        logger = logging.getLogger(__name__)
        
        if self.month != 1:
            return
        
        # Lock Employee für Update (verhindert Race Conditions)
        employee = Employee.objects.select_for_update().get(pk=self.employee.pk)
        
        # Prüfe ob bereits zurückgesetzt wurde (verhindert doppelte Resets)
        if employee.alv_ytd_basis != Decimal("0.00") or employee.uvg_ytd_basis != Decimal("0.00"):
            logger.info(f"YTD-Reset für {employee} im Monat {self.month}/{self.year}")
            employee.alv_ytd_basis = Decimal("0.00")
            employee.uvg_ytd_basis = Decimal("0.00")
            employee.bvg_ytd_basis = Decimal("0.00")
            employee.bvg_ytd_insured_salary = Decimal("0.00")
            employee.save(update_fields=[
                'alv_ytd_basis', 'uvg_ytd_basis', 'bvg_ytd_basis', 'bvg_ytd_insured_salary'
            ])
    
    def _calculate_social_insurances(self):
        """
        Berechnet alle Sozialversicherungen (AHV, ALV, UVG, KTG, BVG, FAK, VK).
        
        Returns:
            dict: Enthält 'bvg_result' für spätere YTD-Updates
        
        Raises:
            ValidationError: Falls eine Berechnung fehlschlägt
        """
        from decimal import Decimal
        import logging
        from django.core.exceptions import ValidationError
        
        logger = logging.getLogger(__name__)
        bvg_result = {}
        
        # AHV-Berechnung durchführen
        try:
            from adealohn.ahv_calculator import AHVCalculator
            ahv_result = AHVCalculator.calculate_for_payroll(self)
            self.ahv_effective_basis = ahv_result["ahv_effective_basis"]
            self.ahv_employee = ahv_result["ahv_employee"]
            self.ahv_employer = ahv_result["ahv_employer"]
        except Exception as e:
            logger.error(f"AHV-Berechnung fehlgeschlagen für PayrollRecord {self.pk}: {e}", exc_info=True)
            raise ValidationError(f"AHV-Berechnung fehlgeschlagen: {e}")

        # FAK-Berechnung durchführen (nach AHV, da auf Bruttolohn basiert)
        try:
            from adealohn.fak_calculator import FAKCalculator
            fak_result = FAKCalculator.calculate_for_payroll(self)
            self.fak_employer = fak_result["fak_employer"]
        except Exception as e:
            logger.error(f"FAK-Berechnung fehlgeschlagen für PayrollRecord {self.pk}: {e}", exc_info=True)
            raise ValidationError(f"FAK-Berechnung fehlgeschlagen: {e}")

        # VK-Berechnung durchführen (nach AHV, da auf Total AHV-Beitrag basiert)
        try:
            from adealohn.vk_calculator import VKCalculator
            vk_result = VKCalculator.calculate_for_payroll(self)
            self.vk_employer = vk_result["vk_employer"]
        except Exception as e:
            logger.error(f"VK-Berechnung fehlgeschlagen für PayrollRecord {self.pk}: {e}", exc_info=True)
            raise ValidationError(f"VK-Berechnung fehlgeschlagen: {e}")

        # ALV-Berechnung durchführen
        try:
            from adealohn.alv_calculator import ALVCalculator
            alv_calc = ALVCalculator()
            alv_result = alv_calc.calculate_for_payroll(self)
            self.alv_effective_basis = alv_result["alv_effective_basis"]
            self.alv_employee = alv_result["alv_employee"]
            self.alv_employer = alv_result["alv_employer"]
        except Exception as e:
            logger.error(f"ALV-Berechnung fehlgeschlagen für PayrollRecord {self.pk}: {e}", exc_info=True)
            raise ValidationError(f"ALV-Berechnung fehlgeschlagen: {e}")

        # UVG-Berechnung durchführen
        try:
            from adealohn.uvg_calculator import UVGCalculator
            uvg_calc = UVGCalculator()
            uvg_result = uvg_calc.calculate_for_payroll(self)
            self.uvg_effective_basis = uvg_result["uvg_effective_basis"]
            self.bu_employer = uvg_result["bu_employer"]
            self.bu_employee = uvg_result["bu_employee"]
            self.nbu_employee = uvg_result["nbu_employee"]
        except Exception as e:
            logger.error(f"UVG-Berechnung fehlgeschlagen für PayrollRecord {self.pk}: {e}", exc_info=True)
            raise ValidationError(f"UVG-Berechnung fehlgeschlagen: {e}")

        # KTG-Berechnung durchführen
        try:
            from adealohn.ktg_calculator import KTGCalculator
            ktg_calc = KTGCalculator()
            ktg_result = ktg_calc.calculate_for_payroll(self)
            self.ktg_effective_basis = ktg_result["ktg_effective_basis"]
            self.ktg_employee = ktg_result["ktg_employee"]
            self.ktg_employer = ktg_result["ktg_employer"]
        except Exception as e:
            logger.error(f"KTG-Berechnung fehlgeschlagen für PayrollRecord {self.pk}: {e}", exc_info=True)
            raise ValidationError(f"KTG-Berechnung fehlgeschlagen: {e}")

        # BVG-Berechnung durchführen (optional - nur wenn Parameter vorhanden)
        from adealohn.helpers import safe_decimal
        from decimal import Decimal, ROUND_HALF_UP
        from adeacore.money import round_to_5_rappen
        
        def round_to_2_decimals(value):
            """Rundet Decimal-Wert auf 2 Dezimalstellen."""
            return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
        # Manuelle BVG-Beiträge aus PayrollRecord-Feldern lesen
        manual_bvg_employee = safe_decimal(self.manual_bvg_employee)
        manual_bvg_employer = safe_decimal(self.manual_bvg_employer)
        
        # Prüfe ob BVG-Parameter vorhanden sind
        from adealohn.models import BVGParameter
        from adealohn.helpers import get_parameter_for_year
        bvg_params = get_parameter_for_year(BVGParameter, self.year)
        
        if bvg_params:
            # Automatische Berechnung vorhanden - verwende Calculator
            try:
                from adealohn.bvg_calculator import BVGCalculator
                bvg_calc = BVGCalculator()
                bvg_result = bvg_calc.calculate_for_payroll(self)
                self.bvg_insured_salary = bvg_result["bvg_insured_salary"]
                
                # Manuelle Beiträge auf 5 Rappen runden und zu berechneten Beiträgen addieren
                manual_bvg_employee_rounded = round_to_5_rappen(manual_bvg_employee)
                manual_bvg_employer_rounded = round_to_5_rappen(manual_bvg_employer)
                
                self.bvg_employee = round_to_2_decimals(bvg_result["bvg_employee"] + manual_bvg_employee_rounded)
                self.bvg_employer = round_to_2_decimals(bvg_result["bvg_employer"] + manual_bvg_employer_rounded)
                
                return bvg_result
            except Exception as e:
                logger.error(f"BVG-Berechnung fehlgeschlagen für PayrollRecord {self.pk}: {e}", exc_info=True)
                raise ValidationError(f"BVG-Berechnung fehlgeschlagen: {e}")
        else:
            # Keine BVG-Parameter - nur manuelle Beiträge verwenden
            self.bvg_insured_salary = Decimal("0.00")
            manual_bvg_employee_rounded = round_to_5_rappen(manual_bvg_employee)
            manual_bvg_employer_rounded = round_to_5_rappen(manual_bvg_employer)
            
            self.bvg_employee = round_to_2_decimals(manual_bvg_employee_rounded)
            self.bvg_employer = round_to_2_decimals(manual_bvg_employer_rounded)
            
            return {
                "bvg_insured_salary": Decimal("0.00"),
                "bvg_insured_month": Decimal("0.00"),
                "bvg_employee": manual_bvg_employee_rounded,
                "bvg_employer": manual_bvg_employer_rounded,
            }
    
    def _calculate_qst_basis(self):
        """
        Berechnet QST-Basis gemäss Excel-Logik: ALV-Basis - AN-Sozialabzüge auf ALV-Basis.
        
        WICHTIG: Diese Berechnung muss NACH allen anderen Berechnungen erfolgen!
        AN-Sozialabzüge auf ALV-Basis müssen direkt auf ALV-Basis berechnet werden (nicht proportional!).
        """
        from decimal import Decimal
        from adealohn.ktg_calculator import KTGCalculator
        from adealohn.uvg_calculator import UVGCalculator
        from adealohn.models import KTGParameter, UVGParameter, AHVParameter
        from adeacore.money import round_to_5_rappen
        from adealohn.helpers import get_parameter_for_year, get_ytd_basis, safe_decimal
        
        alv_basis_for_qst = safe_decimal(self.alv_basis)
        employee = getattr(self, "employee", None)
        
        # AHV-Parameter für Jahr holen
        defaults_ahv = {"rate_employee": Decimal("0.053")}
        ahv_params = get_parameter_for_year(AHVParameter, self.year, defaults=defaults_ahv)
        ahv_rate_employee = ahv_params.rate_employee if ahv_params else defaults_ahv["rate_employee"]
        
        # AHV-AN auf ALV-Basis: Berechne AHV direkt mit ALV-Basis (ohne Rentnerfreibetrag für QST)
        # Für QST-Basis wird Rentnerfreibetrag nicht berücksichtigt (wie im alten System)
        ahv_an_on_alv_basis = alv_basis_for_qst * ahv_rate_employee
        ahv_an_on_alv_basis = round_to_5_rappen(ahv_an_on_alv_basis)
        
        # ALV-AN ist bereits auf ALV-Basis (bereits korrekt berechnet)
        alv_an_on_alv_basis = safe_decimal(self.alv_employee)
        
        # NBU-AN auf ALV-Basis: Berechne NBU direkt mit ALV-Basis
        nbu_on_alv_basis = Decimal("0.00")
        if employee and getattr(employee, "nbu_pflichtig", False):
            defaults_uvg = {"max_annual_insured_salary": Decimal("148200.00"), "nbu_rate_employee": Decimal("0.023")}
            uvg_params = get_parameter_for_year(UVGParameter, self.year, defaults=defaults_uvg)
            if uvg_params:
                # YTD-Logik für NBU (gleiche wie für BU)
                ytd_basis = get_ytd_basis(employee, "uvg_ytd_basis")
                max_year = uvg_params.max_annual_insured_salary if uvg_params else defaults_uvg["max_annual_insured_salary"]
                
                if ytd_basis < max_year:
                    remaining = max_year - ytd_basis
                    capped_alv_basis = min(alv_basis_for_qst, remaining)
                    nbu_rate = uvg_params.nbu_rate_employee if uvg_params else defaults_uvg["nbu_rate_employee"]
                    nbu_raw = capped_alv_basis * nbu_rate
                    nbu_on_alv_basis = round_to_5_rappen(nbu_raw)
        
        # KTG-AN auf ALV-Basis: Berechne KTG direkt mit ALV-Basis
        ktg_on_alv_basis = Decimal("0.00")
        ktg_params = get_parameter_for_year(KTGParameter, self.year)
        if ktg_params and ktg_params.ktg_rate_employee > 0:
            # Optional: Kappung anwenden
            if ktg_params.ktg_max_basis:
                effective_alv_basis = min(alv_basis_for_qst, ktg_params.ktg_max_basis)
            else:
                effective_alv_basis = alv_basis_for_qst
            
            total_rate = ktg_params.ktg_rate_employee + ktg_params.ktg_rate_employer
            ktg_total_on_alv = effective_alv_basis * total_rate
            # AN-Anteil (50/50 Split, falls nicht anders konfiguriert)
            if total_rate > 0:
                ktg_on_alv_basis = ktg_total_on_alv * (ktg_params.ktg_rate_employee / total_rate)
            else:
                ktg_on_alv_basis = Decimal("0.00")
            ktg_on_alv_basis = round_to_5_rappen(ktg_on_alv_basis)
        
        # BVG ist unabhängig von Basis (wird direkt verwendet)
        bvg_an = safe_decimal(self.bvg_employee)
        
        # AN-Sozialabzüge auf ALV-Basis
        sozialabzuege_auf_alv_basis = (
            ahv_an_on_alv_basis +
            alv_an_on_alv_basis +
            nbu_on_alv_basis +
            ktg_on_alv_basis +
            bvg_an
        )
        
        # QST-Basis = ALV-Basis - AN-Sozialabzüge auf ALV-Basis
        self.qst_basis = max(alv_basis_for_qst - sozialabzuege_auf_alv_basis, Decimal("0.00"))
    
    def _calculate_qst(self):
        """
        Berechnet QST (Quellensteuer) basierend auf qst_basis.
        
        Raises:
            ValidationError: Falls QST-Berechnung fehlschlägt
        """
        import logging
        from django.core.exceptions import ValidationError
        
        logger = logging.getLogger(__name__)
        
        try:
            from adealohn.qst_calculator import QSTCalculator
            qst_calc = QSTCalculator()
            qst_calc.calculate_for_payroll(self)
        except Exception as e:
            logger.error(f"QST-Berechnung fehlgeschlagen für PayrollRecord {self.pk}: {e}", exc_info=True)
            raise ValidationError(f"QST-Berechnung fehlgeschlagen: {e}")
    
    def _calculate_nettolohn(self):
        """
        Berechnet Nettolohn: Bruttolohn - alle AN-Abzüge (AHV + ALV + NBU + KTG + BVG + QST).
        Rundet auf 2 Dezimalstellen und verhindert negative Werte.
        """
        from decimal import Decimal, ROUND_HALF_UP
        from adealohn.helpers import safe_decimal
        
        netto = (
            safe_decimal(self.bruttolohn)
            - safe_decimal(self.ahv_employee)
            - safe_decimal(self.alv_employee)
            - safe_decimal(self.nbu_employee)
            - safe_decimal(self.ktg_employee)
            - safe_decimal(self.bvg_employee)
            - safe_decimal(self.qst_abzug)
        )
        
        # Sicherstellen dass Netto nicht negativ ist und auf 2 Dezimalstellen gerundet
        self.nettolohn = max(netto, Decimal("0.00")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    def _update_ytd_if_abgerechnet(self, bvg_result):
        """
        Aktualisiert YTD-Basen nur wenn Status = "ABGERECHNET".
        
        Verwendet select_for_update() um Race Conditions zu vermeiden.
        
        Args:
            bvg_result: Ergebnis der BVG-Berechnung (enthält bvg_insured_month)
        """
        from decimal import Decimal
        import logging
        
        logger = logging.getLogger(__name__)
        
        if self.status != "ABGERECHNET":
            return
        
        # Lock Employee für Update (verhindert Race Conditions bei gleichzeitigen Updates)
        employee = Employee.objects.select_for_update().get(pk=self.employee.pk)
        
        # Prüfe ob bereits aktualisiert wurde (verhindert doppelte Updates bei Status-Änderungen)
        # Speichere alten Status in _old_status (wird in __init__ gesetzt)
        old_status = getattr(self, '_old_status', None)
        if old_status != "ABGERECHNET":
            logger.info(f"YTD-Update für {employee} - PayrollRecord {self.pk} ({self.month}/{self.year})")
            # WICHTIG: Verwende effective_basis (nach YTD-Kappung) für YTD-Updates
            employee.alv_ytd_basis += self.alv_effective_basis
            employee.uvg_ytd_basis += self.uvg_effective_basis
            employee.bvg_ytd_basis += self.bvg_basis
            # bvg_ytd_insured_salary aktualisieren (monatlicher versicherter Lohn)
            bvg_insured_month = bvg_result.get("bvg_insured_month", Decimal("0.00")) if bvg_result else Decimal("0.00")
            employee.bvg_ytd_insured_salary += bvg_insured_month
            employee.save(update_fields=[
                'alv_ytd_basis', 'uvg_ytd_basis', 'bvg_ytd_basis', 'bvg_ytd_insured_salary'
            ])

    @transaction.atomic
    def save(self, *args, **kwargs):
        """
        Speichert PayrollRecord und führt alle Berechnungen durch.
        
        Ablauf:
        1. Validierung
        2. YTD-Reset für Januar
        3. Basis-Berechnung aus Items
        4. Sozialversicherungen berechnen
        5. QST-Basis berechnen
        6. QST berechnen
        7. Netto-Lohn berechnen
        8. Speichern
        9. YTD aktualisieren (wenn Status = ABGERECHNET)
        """
        # Validierung durchführen
        self.full_clean()
        
        # Jahresreset für Januar: YTD-Basen zurücksetzen
        self._handle_january_ytd_reset()
        
        # Basis-Berechnung aus Items (falls vorhanden)
        items_qs = None
        if self.pk and self.items.exists():
            items_qs = list(self.items.select_related("wage_type"))
            self._items_qs = items_qs
            self.recompute_bases_from_items()

        # Alle Sozialversicherungen berechnen
        bvg_result = self._calculate_social_insurances()
        
        # QST-Basis berechnen (muss nach allen anderen Berechnungen erfolgen)
        self._calculate_qst_basis()
        
        # QST-Berechnung durchführen
        self._calculate_qst()

        # Netto-Lohn berechnen
        self._calculate_nettolohn()

        # Speichern
        super().save(*args, **kwargs)
        
        # YTD aktualisieren nur wenn Status = "ABGERECHNET"
        self._update_ytd_if_abgerechnet(bvg_result)
        
        # Cleanup
        if items_qs is not None:
            self._items_qs = None


class SVAEntscheid(models.Model):
    """
    SVA-Entscheid für Familienzulagen (Kinderzulage/Ausbildungszulage).
    
    Dokumentiert den Entscheid der Familienausgleichskasse (FAK/SVA) über
    die Gewährung von Familienzulagen für einen Mitarbeiter.
    """
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="sva_entscheide",
        help_text="Mitarbeiter, für den dieser SVA-Entscheid gilt",
    )
    entscheid = models.CharField(
        max_length=255,
        help_text="Entscheid-Nummer oder Beschreibung (z.B. 'FAK-2025-12345')",
    )
    von_datum = models.DateField(
        help_text="Gültigkeitsbeginn des Entscheids",
    )
    bis_datum = models.DateField(
        null=True,
        blank=True,
        help_text="Gültigkeitsende des Entscheids (optional, leer = unbefristet)",
    )
    betrag_monatlich = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Monatlicher Betrag der Familienzulage in CHF",
    )
    beschreibung = models.TextField(
        blank=True,
        help_text="Zusätzliche Informationen zum Entscheid (optional)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-von_datum", "employee__last_name"]
        verbose_name = "SVA-Entscheid"
        verbose_name_plural = "SVA-Entscheide"

    def __str__(self):
        return f"{self.employee} – {self.entscheid} ({self.von_datum})"

    def is_aktiv(self):
        """Prüft, ob der Entscheid aktuell aktiv ist."""
        from django.utils import timezone
        today = timezone.now().date()
        if self.bis_datum and self.bis_datum < today:
            return False
        return self.von_datum <= today


# ============================================================================
# CRM-FEATURES
# ============================================================================

class Communication(models.Model):
    """
    Kommunikationshistorie für Mandanten.
    Erfasst E-Mails, Anrufe, Meetings und andere Kontakte.
    """
    COMMUNICATION_TYPES = [
        ("EMAIL", "E-Mail"),
        ("ANRUF", "Anruf"),
        ("MEETING", "Meeting"),
        ("NOTIZ", "Notiz"),
        ("SONSTIGES", "Sonstiges"),
    ]
    
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="communications",
        verbose_name="Mandant",
    )
    communication_type = models.CharField(
        "Typ",
        max_length=20,
        choices=COMMUNICATION_TYPES,
        default="NOTIZ",
    )
    subject = models.CharField(
        "Betreff/Thema",
        max_length=255,
        blank=True,
        help_text="Betreff (E-Mail) oder Thema (Anruf/Meeting)",
    )
    content = models.TextField(
        "Inhalt",
        help_text="Inhalt der Kommunikation",
    )
    date = models.DateTimeField(
        "Datum",
        help_text="Datum und Uhrzeit der Kommunikation",
    )
    duration_minutes = models.PositiveIntegerField(
        "Dauer (Minuten)",
        null=True,
        blank=True,
        help_text="Dauer bei Anrufen/Meetings (optional)",
    )
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="communications",
        verbose_name="Erstellt von",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-date", "-created_at"]
        verbose_name = "Kommunikation"
        verbose_name_plural = "Kommunikationen"
    
    def __str__(self):
        return f"{self.get_communication_type_display()} - {self.client.name} ({self.date.strftime('%d.%m.%Y')})"


class Event(models.Model):
    """
    Termine und Events für Mandanten.
    Steuerfristen, Meetings, Erinnerungen.
    """
    EVENT_TYPES = [
        ("MEETING", "Meeting"),
        ("FRIST", "Frist"),
        ("ERINNERUNG", "Erinnerung"),
        ("TERMIN", "Termin"),
        ("SONSTIGES", "Sonstiges"),
    ]
    
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name="Mandant",
    )
    event_type = models.CharField(
        "Typ",
        max_length=20,
        choices=EVENT_TYPES,
        default="TERMIN",
    )
    title = models.CharField(
        "Titel",
        max_length=255,
    )
    description = models.TextField(
        "Beschreibung",
        blank=True,
    )
    start_date = models.DateTimeField(
        "Startdatum",
        help_text="Startdatum und -zeit",
    )
    end_date = models.DateTimeField(
        "Enddatum",
        null=True,
        blank=True,
        help_text="Enddatum und -zeit (optional)",
    )
    reminder_date = models.DateTimeField(
        "Erinnerung",
        null=True,
        blank=True,
        help_text="Erinnerung vor dem Termin (optional)",
    )
    reminder_sent = models.BooleanField(
        "Erinnerung gesendet",
        default=False,
    )
    is_recurring = models.BooleanField(
        "Wiederkehrend",
        default=False,
        help_text="Wiederkehrender Termin (z.B. monatlich)",
    )
    recurring_pattern = models.CharField(
        "Wiederholungsmuster",
        max_length=50,
        blank=True,
        help_text="z.B. 'MONATLICH', 'JAERLICH'",
    )
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
        verbose_name="Erstellt von",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["start_date"]
        verbose_name = "Termin"
        verbose_name_plural = "Termine"
    
    def __str__(self):
        return f"{self.title} - {self.client.name} ({self.start_date.strftime('%d.%m.%Y')})"
    
    def is_overdue(self):
        """Prüft, ob der Termin überfällig ist."""
        from django.utils import timezone
        return self.start_date < timezone.now() and not self.end_date


class Invoice(models.Model):
    """
    Rechnungen für Mandanten.
    """
    PAYMENT_STATUS_CHOICES = [
        ("OFFEN", "Offen"),
        ("TEILWEISE", "Teilweise bezahlt"),
        ("BEZAHLT", "Bezahlt"),
        ("UEBERFAELLIG", "Überfällig"),
        ("STORNIERT", "Storniert"),
    ]
    
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="invoices",
        verbose_name="Mandant",
    )
    invoice_number = models.CharField(
        "Rechnungsnummer",
        max_length=100,
        unique=True,
        help_text="Eindeutige Rechnungsnummer",
    )
    invoice_date = models.DateField(
        "Rechnungsdatum",
    )
    due_date = models.DateField(
        "Fälligkeitsdatum",
        help_text="Fälligkeitsdatum basierend auf Zahlungsziel",
    )
    amount = models.DecimalField(
        "Betrag",
        max_digits=10,
        decimal_places=2,
        help_text="Rechnungsbetrag in CHF (Bruttobetrag)",
    )
    net_amount = models.DecimalField(
        "Nettobetrag",
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Nettobetrag ohne MWST",
    )
    vat_amount = models.DecimalField(
        "MWST-Betrag",
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="MWST-Betrag",
    )
    vat_rate = models.DecimalField(
        "MWST-Satz (%)",
        max_digits=5,
        decimal_places=2,
        default=8.1,
        help_text="MWST-Satz (z.B. 8.1)",
    )
    paid_amount = models.DecimalField(
        "Bezahlter Betrag",
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Bereits bezahlter Betrag",
    )
    payment_status = models.CharField(
        "Zahlungsstatus",
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="OFFEN",
    )
    payment_date = models.DateField(
        "Zahlungsdatum",
        null=True,
        blank=True,
        help_text="Datum der Zahlung",
    )
    description = models.TextField(
        "Beschreibung",
        blank=True,
        help_text="Beschreibung der Leistungen",
    )
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices",
        verbose_name="Erstellt von",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-invoice_date", "-created_at"]
        verbose_name = "Rechnung"
        verbose_name_plural = "Rechnungen"
    
    def __str__(self):
        return f"{self.invoice_number} - {self.client.name} ({self.amount} CHF)"
    
    def save(self, *args, **kwargs):
        """Aktualisiert Zahlungsstatus automatisch."""
        from django.utils import timezone
        from decimal import Decimal
        
        # Aktualisiere Zahlungsstatus basierend auf Beträgen
        if self.paid_amount >= self.amount:
            self.payment_status = "BEZAHLT"
        elif self.paid_amount > Decimal("0"):
            self.payment_status = "TEILWEISE"
        elif self.due_date and self.due_date < timezone.now().date():
            self.payment_status = "UEBERFAELLIG"
        else:
            self.payment_status = "OFFEN"
        
        super().save(*args, **kwargs)
    
    @property
    def remaining_amount(self):
        """Berechnet den offenen Betrag."""
        from decimal import Decimal
        return self.amount - self.paid_amount


class Document(models.Model):
    """
    Dokumente und Dateien für Mandanten.
    Verträge, Steuerdokumente, Belege, etc.
    """
    DOCUMENT_TYPES = [
        ("VERTRAG", "Vertrag"),
        ("STEUER", "Steuer"),
        ("RECHNUNG", "Rechnung"),
        ("BELEG", "Beleg"),
        ("SONSTIGES", "Sonstiges"),
    ]
    
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name="Mandant",
    )
    document_type = models.CharField(
        "Typ",
        max_length=20,
        choices=DOCUMENT_TYPES,
        default="SONSTIGES",
    )
    title = models.CharField(
        "Titel",
        max_length=255,
    )
    description = models.TextField(
        "Beschreibung",
        blank=True,
    )
    file = models.FileField(
        "Datei",
        upload_to="documents/%Y/%m/",
        help_text="Hochgeladene Datei",
    )
    file_size = models.PositiveIntegerField(
        "Dateigröße (Bytes)",
        null=True,
        blank=True,
        help_text="Größe der Datei in Bytes",
    )
    uploaded_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        verbose_name="Hochgeladen von",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Dokument"
        verbose_name_plural = "Dokumente"
    
    def __str__(self):
        return f"{self.title} - {self.client.name}"
    
    def save(self, *args, **kwargs):
        """Speichert Dateigröße automatisch."""
        if self.file and not self.file_size:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    @property
    def file_size_human(self):
        """Gibt Dateigröße in lesbarem Format zurück."""
        if not self.file_size:
            return "0 B"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"


class ClientNote(models.Model):
    """
    Notizen für Mandanten im CRM.
    Erlaubt es, wichtige Informationen zu Mandanten zu dokumentieren,
    z.B. Steuererklärung nächstes Jahr, quartalsweise Notizen, etc.
    """
    NOTE_TYPE_CHOICES = [
        ("STEUER", "Steuererklärung"),
        ("QUARTAL", "Quartalsweise"),
        ("MONAT", "Monatlich"),
        ("ALLGEMEIN", "Allgemein"),
        ("ERINNERUNG", "Erinnerung"),
    ]
    
    STATUS_CHOICES = [
        ("OFFEN", "Offen"),
        ("ERLEDIGT", "Erledigt"),
    ]
    
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="client_notes",
        verbose_name="Mandant",
    )
    title = models.CharField(
        "Titel",
        max_length=255,
        help_text="Titel der Notiz (z.B. 'Steuererklärung 2026')"
    )
    content = models.TextField(
        "Inhalt",
        help_text="Inhalt der Notiz"
    )
    note_type = models.CharField(
        "Typ",
        max_length=20,
        choices=NOTE_TYPE_CHOICES,
        default="ALLGEMEIN",
        help_text="Typ der Notiz"
    )
    note_date = models.DateField(
        "Datum",
        help_text="Datum der Notiz (z.B. Datum der Steuererklärung oder Quartal/Monat)"
    )
    status = models.CharField(
        "Status",
        max_length=20,
        choices=STATUS_CHOICES,
        default="OFFEN",
    )
    task = models.ForeignKey(
        "adeazeit.Task",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="client_notes",
        verbose_name="Verknüpfte Aufgabe",
        help_text="Optional: Verknüpfung zu einer Aufgabe in AdeaZeit"
    )
    archiviert = models.BooleanField(
        "Archiviert",
        default=False,
        help_text="Erledigte Notizen können archiviert werden"
    )
    erledigt_am = models.DateTimeField(
        "Erledigt am",
        null=True,
        blank=True,
        help_text="Datum und Uhrzeit, wann die Notiz als erledigt markiert wurde"
    )
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_client_notes",
        verbose_name="Erstellt von",
        help_text="Benutzer, der die Notiz erstellt hat"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ["-note_date", "-created_at"]
        verbose_name = "Mandanten-Notiz"
        verbose_name_plural = "Mandanten-Notizen"
        indexes = [
            models.Index(fields=['client', 'status'], name='adeacore_cnote_client_st_idx'),
            models.Index(fields=['client', 'archiviert'], name='adeacore_cnote_client_ar_idx'),
            models.Index(fields=['note_date'], name='adeacore_cnote_date_idx'),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.client.name} ({self.note_date})"
    
    def save(self, *args, **kwargs):
        """Setzt erledigt_am automatisch wenn Status auf ERLEDIGT."""
        from django.utils import timezone
        if self.status == 'ERLEDIGT' and not self.erledigt_am:
            self.erledigt_am = timezone.now()
        elif self.status != 'ERLEDIGT':
            self.erledigt_am = None
        super().save(*args, **kwargs)


class CompanyData(models.Model):
    """
    Firmendaten für Adea Treuhand (Singleton).
    Wird für Rechnungen verwendet.
    """
    # Firmenname
    company_name = models.CharField(
        "Firmenname",
        max_length=255,
        default="Adea Treuhand",
        help_text="Vollständiger Firmenname"
    )
    
    # Adresse
    street = models.CharField("Strasse", max_length=255, blank=True)
    house_number = models.CharField("Hausnummer", max_length=50, blank=True)
    zipcode = models.CharField("PLZ", max_length=20, blank=True)
    city = models.CharField("Ort", max_length=255, blank=True)
    country = models.CharField("Land", max_length=100, default="Schweiz")
    
    # Kontakt
    email = models.EmailField("E-Mail", blank=True)
    phone = models.CharField("Telefon", max_length=50, blank=True)
    website = models.URLField("Website", blank=True)
    
    # MWST & Bankdaten
    mwst_pflichtig = models.BooleanField(
        "MWST-pflichtig",
        default=True,
        help_text="Gilt für den Rechnungssteller (Adea Treuhand). Wenn aktiv, wird MWST auf Rechnungen berechnet.",
    )
    mwst_satz = models.DecimalField(
        "MWST-Satz (%)",
        max_digits=5,
        decimal_places=2,
        default=8.1,
        help_text="Standard-MWST-Satz für Rechnungen (z.B. 8.1).",
    )
    mwst_nr = EncryptedCharField(
        "MWST-Nummer (UID MWST)",
        max_length=500,
        blank=True,
        help_text="Format: CHE-123.456.789 MWST"
    )
    iban = EncryptedCharField(
        "IBAN",
        max_length=500,
        blank=True,
        help_text="IBAN für QR-Rechnung"
    )
    bank_name = models.CharField("Bank", max_length=255, blank=True)
    
    # Zusätzliche Angaben
    notes = models.TextField("Notizen", blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Firmendaten"
        verbose_name_plural = "Firmendaten"
    
    def __str__(self):
        return self.company_name
    
    def save(self, *args, **kwargs):
        """Stellt sicher, dass nur ein Eintrag existiert (Singleton)."""
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def get_instance(cls):
        """Gibt die Firmendaten zurück (erstellt falls nicht vorhanden)."""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
    
    @property
    def full_address(self):
        """Gibt die vollständige Adresse zurück."""
        parts = []
        if self.street:
            parts.append(self.street)
        if self.house_number:
            parts.append(self.house_number)
        if self.zipcode or self.city:
            parts.append(f"{self.zipcode} {self.city}".strip())
        if self.country:
            parts.append(self.country)
        return ", ".join(parts) if parts else ""


class CompanyLocation(models.Model):
    """
    Zusätzliche Standorte für den Rechnungs-Briefkopf.
    Werden im PDF in mehreren Spalten dargestellt.
    """

    company = models.ForeignKey(
        CompanyData,
        on_delete=models.CASCADE,
        related_name="locations",
        verbose_name="Firma",
    )
    name = models.CharField("Bezeichnung", max_length=100, blank=True)
    street = models.CharField("Strasse", max_length=255)
    house_number = models.CharField("Hausnummer", max_length=50, blank=True)
    zipcode = models.CharField("PLZ", max_length=20)
    city = models.CharField("Ort", max_length=255)
    country = models.CharField("Land", max_length=100, default="Schweiz")
    is_active = models.BooleanField("Aktiv", default=True)
    sort_order = models.PositiveIntegerField("Sortierung", default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "id"]
        verbose_name = "Standort"
        verbose_name_plural = "Standorte"

    def __str__(self):
        label = self.name or "Standort"
        return f"{label}: {self.street} {self.house_number}, {self.zipcode} {self.city}".strip()


class InvoiceItem(models.Model):
    """
    Rechnungsposition (Zeiteintrag → Rechnungsposition).
    """
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Rechnung"
    )
    time_entry = models.ForeignKey(
        "adeazeit.TimeEntry",
        on_delete=models.PROTECT,
        related_name="invoice_items",
        verbose_name="Zeiteintrag",
        null=True,
        blank=True,
        help_text="Verknüpfung zum ursprünglichen Zeiteintrag"
    )
    
    # Leistungsbeschreibung
    description = models.TextField(
        "Beschreibung",
        help_text="Leistungsbeschreibung (aus Kommentar)"
    )
    service_type_code = models.CharField(
        "Service-Typ",
        max_length=50,
        help_text="Service-Typ Code (z.B. STEU, BUCH)"
    )
    employee_name = models.CharField(
        "Mitarbeiterin",
        max_length=255,
        help_text="Name der Mitarbeiterin"
    )
    service_date = models.DateField(
        "Leistungsdatum",
        help_text="Datum der Leistungserbringung"
    )
    
    # Preise
    quantity = models.DecimalField(
        "Anzahl (Stunden)",
        max_digits=5,
        decimal_places=2,
        help_text="Anzahl Stunden"
    )
    unit_price = models.DecimalField(
        "Einzelpreis (Stundensatz)",
        max_digits=10,
        decimal_places=2,
        help_text="Stundensatz in CHF"
    )
    net_amount = models.DecimalField(
        "Nettobetrag",
        max_digits=10,
        decimal_places=2,
        help_text="Nettobetrag (ohne MWST)"
    )
    
    # MWST
    vat_rate = models.DecimalField(
        "MWST-Satz (%)",
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="MWST-Satz (z.B. 8.1)"
    )
    vat_amount = models.DecimalField(
        "MWST-Betrag",
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="MWST-Betrag"
    )
    gross_amount = models.DecimalField(
        "Bruttobetrag",
        max_digits=10,
        decimal_places=2,
        help_text="Bruttobetrag (mit MWST)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["service_date", "id"]
        verbose_name = "Rechnungsposition"
        verbose_name_plural = "Rechnungspositionen"
    
    def __str__(self):
        return f"{self.service_type_code} - {self.service_date} ({self.gross_amount} CHF)"

