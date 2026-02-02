from decimal import Decimal

from adeacore.money import round_to_5_rappen


class FAKCalculator:
    """
    Berechnet FAK-Beitrag (Familienausgleichskasse) gemäss Schweizer Recht:
    - Kantonabhängiger AG-Beitrag vom Bruttolohn
    - Wird vom Arbeitgeber bezahlt
    - Standard: 1.025% (falls kein kantonaler Satz definiert)
    """

    DEFAULT_RATE_EMPLOYER = Decimal("0.01025")  # 1.025% Standard (Fallback)

    @classmethod
    def calculate_for_payroll(cls, payroll):
        """
        Berechnet FAK-Beitrag für einen PayrollRecord.
        Verwendet kantonalen Satz basierend auf Arbeitgeberort (Client.work_canton).

        Args:
            payroll: PayrollRecord-Instanz

        Returns:
            dict mit:
                - fak_employer: Arbeitgeberbeitrag (gerundet auf 0.05)
        """
        from adealohn.models import FAKParameter

        gross_salary = payroll.gross_salary or Decimal("0.00")
        
        # Kanton des Arbeitgebers ermitteln
        employee = getattr(payroll, "employee", None)
        canton = None
        if employee and employee.client:
            canton = employee.client.work_canton
        
        # FAK-Parameter für Jahr und Kanton suchen
        rate = cls.DEFAULT_RATE_EMPLOYER
        if canton:
            fak_param = FAKParameter.objects.filter(
                year=payroll.year,
                canton=canton.upper() if canton else None
            ).first()
            if fak_param:
                rate = fak_param.fak_rate_employer
            else:
                # Fallback: DEFAULT-Parameter suchen
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
