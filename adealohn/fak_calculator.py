from decimal import Decimal

from adeacore.money import round_to_5_rappen


class FAKCalculator:
    """
    Berechnet FAK-Beitrag (Familienausgleichskasse) gemäss Excel-Vorlage:
    - Kantonabhängiger AG-Beitrag vom Bruttolohn
    - Wird vom Arbeitgeber bezahlt
    - Standard: 1.0% (falls kein kantonaler Satz definiert)
    - Aktueller Satz kann auf AHV-Rechnung gefunden werden
    """

    DEFAULT_RATE_EMPLOYER = Decimal("0.01")  # 1.0% Standard (Fallback, gemäss Excel-Vorlage)

    @classmethod
    def calculate_for_payroll(cls, payroll):
        """
        Berechnet FAK-Beitrag für einen PayrollRecord.
        
        WICHTIG: FAK ist kantonabhängig basierend auf dem FIRMENSITZ des Mandanten (Client),
        nicht auf dem Wohnort des Mitarbeiters! Jeder Treuhandmandant kann einen
        unterschiedlichen Firmensitz haben.

        Args:
            payroll: PayrollRecord-Instanz

        Returns:
            dict mit:
                - fak_employer: Arbeitgeberbeitrag (gerundet auf 0.05)
        """
        from adealohn.models import FAKParameter

        gross_salary = payroll.bruttolohn or Decimal("0.00")
        
        # Kanton des FIRMENSITZES des Mandanten (Client) ermitteln
        # PayrollRecord → Employee → Client → work_canton
        canton = None
        try:
            employee = payroll.employee
            if employee and hasattr(employee, 'client') and employee.client:
                # Client ist der Mandant (Firma), dessen Firmensitz relevant ist
                canton = employee.client.work_canton
        except AttributeError:
            # Fallback wenn employee oder client nicht verfügbar
            pass
        
        # FAK-Parameter für Jahr und Kanton suchen
        rate = cls.DEFAULT_RATE_EMPLOYER
        if canton:
            canton_upper = canton.strip().upper() if canton else None
            if canton_upper:
                fak_param = FAKParameter.objects.filter(
                    year=payroll.year,
                    canton=canton_upper
                ).first()
                if fak_param:
                    rate = fak_param.fak_rate_employer
                    # Kein weiterer Fallback nötig, da kantonaler Satz gefunden
        
        # Wenn kein kantonaler Satz gefunden, versuche DEFAULT
        if rate == cls.DEFAULT_RATE_EMPLOYER:
            fak_param_default = FAKParameter.objects.filter(
                year=payroll.year,
                canton="DEFAULT"
            ).first()
            if fak_param_default:
                rate = fak_param_default.fak_rate_employer

        # FAK-Beitrag berechnen
        fak_employer_raw = gross_salary * rate

        # Auf 0.05 CHF runden
        fak_employer = round_to_5_rappen(fak_employer_raw)

        return {
            "fak_employer": fak_employer,
        }
