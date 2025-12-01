from decimal import Decimal, ROUND_HALF_UP


class BVGCalculator:
    """
    Berechnet BVG (berufliche Vorsorge, 2. Säule) gemäss konfigurierten Parametern.
    Basis ist bvg_basis (aus WageTypes).
    """

    def calculate_for_payroll(self, payroll):
        from decimal import Decimal
        from adealohn.models import BVGParameter

        params = BVGParameter.objects.filter(year=payroll.year).first()

        if not params:
            return {
                "bvg_insured_salary": Decimal("0.00"),
                "bvg_employee": Decimal("0.00"),
                "bvg_employer": Decimal("0.00"),
            }

        basis = payroll.bvg_basis or Decimal("0.00")
        employee = getattr(payroll, "employee", None)

        # YTD-Logik: Jahreslohn = YTD-Basis + aktuelle Basis
        ytd_basis = getattr(employee, "bvg_ytd_basis", Decimal("0.00")) or Decimal("0.00")
        ytd_basis = Decimal(str(ytd_basis))
        annual_salary = ytd_basis + basis

        # Eintrittsschwelle prüfen
        if annual_salary < params.entry_threshold:
            return {
                "bvg_insured_salary": Decimal("0.00"),
                "bvg_employee": Decimal("0.00"),
                "bvg_employer": Decimal("0.00"),
            }

        # Versicherter Lohn berechnen (jährlich)
        insured_annual = annual_salary - params.coordination_deduction

        # BVG-Korridore anwenden
        insured_annual = max(insured_annual, params.min_insured_salary)
        insured_annual = min(insured_annual, params.max_insured_salary)

        # YTD versicherter Lohn
        ytd_insured = getattr(employee, "bvg_ytd_insured_salary", Decimal("0.00")) or Decimal("0.00")
        ytd_insured = Decimal(str(ytd_insured))

        # Versicherter Lohn des Monats = Gesamt versichert - YTD versichert
        insured_month = insured_annual - ytd_insured
        if insured_month < 0:
            insured_month = Decimal("0.00")

        # Beiträge berechnen und auf 0.05 CHF runden (monatlich)
        bvg_employee_raw = insured_month * params.employee_rate
        bvg_employer_raw = insured_month * params.employer_rate

        bvg_employee = (bvg_employee_raw / Decimal("0.05")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        ) * Decimal("0.05")

        bvg_employer = (bvg_employer_raw / Decimal("0.05")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        ) * Decimal("0.05")

        return {
            "bvg_insured_salary": insured_annual,  # Gesamt versicherter Lohn (jährlich)
            "bvg_insured_month": insured_month,  # Versicherter Lohn des Monats
            "bvg_employee": bvg_employee,
            "bvg_employer": bvg_employer,
        }


