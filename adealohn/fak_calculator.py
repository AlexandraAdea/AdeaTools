from decimal import Decimal

from adeacore.money import round_to_5_rappen


class FAKCalculator:
    """
    Berechnet FAK-Beitrag (Familienausgleichskasse) gemäss Schweizer Recht:
    - 1.025% AG vom Bruttolohn
    - Wird vom Arbeitgeber bezahlt
    """

    RATE_EMPLOYER = Decimal("0.01025")  # 1.025% Arbeitgeber

    @classmethod
    def calculate_for_payroll(cls, payroll):
        """
        Berechnet FAK-Beitrag für einen PayrollRecord.

        Args:
            payroll: PayrollRecord-Instanz

        Returns:
            dict mit:
                - fak_employer: Arbeitgeberbeitrag (gerundet auf 0.05)
        """
        gross_salary = payroll.gross_salary or Decimal("0.00")

        # FAK-Beitrag berechnen
        fak_employer_raw = gross_salary * cls.RATE_EMPLOYER

        # Auf 0.05 CHF runden
        fak_employer = round_to_5_rappen(fak_employer_raw)

        return {
            "fak_employer": fak_employer,
        }
