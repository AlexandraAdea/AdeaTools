from decimal import Decimal, ROUND_HALF_UP


class AHVCalculator:
    """
    Berechnet AHV-Beiträge basierend auf der AHV-Basis eines PayrollRecords.
    Berücksichtigt Rentnerfreibetrag falls aktiviert.
    """

    RATE_EMPLOYEE = Decimal("0.053")  # 5.3% Arbeitnehmer
    RATE_EMPLOYER = Decimal("0.053")  # 5.3% Arbeitgeber
    RENTNER_FREIBETRAG_MONAT = Decimal("1400.00")

    @classmethod
    def calculate_for_payroll(cls, payroll):
        """
        Berechnet AHV-Beiträge für einen PayrollRecord.

        Args:
            payroll: PayrollRecord-Instanz

        Returns:
            dict mit:
                - ahv_effective_basis: Bemessungsgrundlage nach Freibetrag
                - ahv_employee: Arbeitnehmerbeitrag (gerundet auf 0.05)
                - ahv_employer: Arbeitgeberbeitrag (gerundet auf 0.05)
        """
        basis = payroll.ahv_basis
        employee = payroll.employee

        # Rentnerfreibetrag anwenden
        if employee.is_rentner and employee.ahv_freibetrag_aktiv:
            effective_basis = max(basis - cls.RENTNER_FREIBETRAG_MONAT, Decimal("0"))
        else:
            effective_basis = basis

        # AHV-Beiträge berechnen
        ahv_employee_raw = effective_basis * cls.RATE_EMPLOYEE
        ahv_employer_raw = effective_basis * cls.RATE_EMPLOYER

        # Auf 0.05 CHF runden
        ahv_employee = (ahv_employee_raw / Decimal("0.05")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        ) * Decimal("0.05")

        ahv_employer = (ahv_employer_raw / Decimal("0.05")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        ) * Decimal("0.05")

        return {
            "ahv_effective_basis": effective_basis,
            "ahv_employee": ahv_employee,
            "ahv_employer": ahv_employer,
        }




