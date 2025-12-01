from decimal import Decimal, ROUND_HALF_UP


class KTGCalculator:
    """
    Berechnet KTG (Krankentaggeldversicherung) gemäss Schweizer Marktstandard 2025.
    Basis ist uv_basis (nicht brutto).
    """

    def calculate_for_payroll(self, payroll):
        from decimal import Decimal
        from adealohn.models import KTGParameter

        params = KTGParameter.objects.first()

        if not params:
            return {
                "ktg_effective_basis": Decimal("0.00"),
                "ktg_employee": Decimal("0.00"),
                "ktg_employer": Decimal("0.00"),
            }

        basis = payroll.uv_basis or Decimal("0.00")

        # Optional: Kappung anwenden
        if params.ktg_max_basis:
            effective_basis = min(basis, params.ktg_max_basis)
        else:
            effective_basis = basis

        # KTG-Beiträge berechnen und auf 0.05 CHF runden
        ktg_employee_raw = effective_basis * params.ktg_rate_employee
        ktg_employer_raw = effective_basis * params.ktg_rate_employer

        ktg_employee = (ktg_employee_raw / Decimal("0.05")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        ) * Decimal("0.05")

        ktg_employer = (ktg_employer_raw / Decimal("0.05")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        ) * Decimal("0.05")

        return {
            "ktg_effective_basis": effective_basis,
            "ktg_employee": ktg_employee,
            "ktg_employer": ktg_employer,
        }



