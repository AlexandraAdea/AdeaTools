from decimal import Decimal
from typing import TYPE_CHECKING

from adeacore.money import round_to_5_rappen
from .helpers import get_parameter_for_year, safe_decimal, get_ytd_basis

if TYPE_CHECKING:
    from adeacore.models import PayrollRecord


class ALVCalculator:
    """
    Berechnet ALV gemäss konfigurierten Parametern:
    - Beitragssätze konfigurierbar pro Jahr über ALVParameter
    - Nur auf Löhne bis Max-Basis pro Jahr
    - Rentner zahlen keine ALV
    """

    def calculate_for_payroll(self, payroll: "PayrollRecord") -> dict:
        from adealohn.models import ALVParameter

        # Parameter mit Fallback laden (mit Caching)
        defaults = {
            "rate_employee": Decimal("0.011"),  # 1.1% Standard
            "rate_employer": Decimal("0.011"),  # 1.1% Standard
            "max_annual_insured_salary": Decimal("148200.00"),
        }
        params = get_parameter_for_year(ALVParameter, payroll.year, defaults=defaults)
        
        rate_employee = params.rate_employee if params else defaults["rate_employee"]
        rate_employer = params.rate_employer if params else defaults["rate_employer"]
        max_year = params.max_annual_insured_salary if params else defaults["max_annual_insured_salary"]

        basis = safe_decimal(payroll.alv_basis)
        employee = getattr(payroll, "employee", None)
        is_rentner = getattr(employee, "is_rentner", False) if employee else False

        # Keine ALV für Rentner
        if is_rentner:
            return {
                "alv_effective_basis": Decimal("0.00"),
                "alv_employee": Decimal("0.00"),
                "alv_employer": Decimal("0.00"),
            }

        # YTD-Logik: Berechne YTD-Basis + aktuelle Basis
        ytd_basis = get_ytd_basis(employee, "alv_ytd_basis")
        
        # Prüfe ob YTD-Basis bereits über Maximum liegt
        if ytd_basis >= max_year:
            # Bereits über Maximum, keine weitere Berechnung
            capped_current = Decimal("0.00")
        else:
            # Berechne wie viel noch möglich ist
            remaining = max_year - ytd_basis
            capped_current = min(basis, remaining)
        
        effective_basis = capped_current

        # ALV-Beiträge berechnen und auf 0.05 CHF runden
        alv_employee_raw = effective_basis * rate_employee
        alv_employer_raw = effective_basis * rate_employer

        alv_employee = round_to_5_rappen(alv_employee_raw)
        alv_employer = round_to_5_rappen(alv_employer_raw)

        return {
            "alv_effective_basis": effective_basis,
            "alv_employee": alv_employee,
            "alv_employer": alv_employer,
        }



