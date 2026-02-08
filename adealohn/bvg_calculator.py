from decimal import Decimal

from adeacore.money import round_to_5_rappen
from .helpers import get_parameter_for_year, safe_decimal, get_ytd_basis
from adealohn.models import BVGParameter


class BVGCalculator:
    """
    Berechnet BVG (berufliche Vorsorge, 2. Säule) gemäss konfigurierten Parametern.
    Basis ist bvg_basis (aus WageTypes).
    """

    def calculate_for_payroll(self, payroll):
        # Parameter mit Fallback laden (mit Caching)
        params = get_parameter_for_year(BVGParameter, payroll.year)

        if not params:
            return {
                "bvg_insured_salary": Decimal("0.00"),
                "bvg_employee": Decimal("0.00"),
                "bvg_employer": Decimal("0.00"),
            }

        basis = safe_decimal(payroll.bvg_basis)
        employee = getattr(payroll, "employee", None)

        # YTD-Logik: Jahreslohn = YTD-Basis + aktuelle Basis
        ytd_basis = get_ytd_basis(employee, "bvg_ytd_basis")
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
        ytd_insured = get_ytd_basis(employee, "bvg_ytd_insured_salary")

        # Versicherter Lohn des Monats = Gesamt versichert - YTD versichert
        insured_month = insured_annual - ytd_insured
        if insured_month < 0:
            insured_month = Decimal("0.00")

        # Beiträge berechnen und auf 0.05 CHF runden (monatlich)
        bvg_employee_raw = insured_month * params.employee_rate
        bvg_employer_raw = insured_month * params.employer_rate

        bvg_employee = round_to_5_rappen(bvg_employee_raw)
        bvg_employer = round_to_5_rappen(bvg_employer_raw)

        return {
            "bvg_insured_salary": insured_annual,  # Gesamt versicherter Lohn (jährlich)
            "bvg_insured_month": insured_month,  # Versicherter Lohn des Monats
            "bvg_employee": bvg_employee,
            "bvg_employer": bvg_employer,
        }


