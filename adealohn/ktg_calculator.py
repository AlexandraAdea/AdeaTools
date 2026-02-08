from decimal import Decimal

from adeacore.money import round_to_5_rappen
from .helpers import get_parameter_for_year, safe_decimal
from adealohn.models import KTGParameter


class KTGCalculator:
    """
    Berechnet KTG (Krankentaggeldversicherung) gemäss Schweizer Marktstandard 2025.
    Basis ist uv_basis (nicht brutto).
    """

    def calculate_for_payroll(self, payroll):
        # Parameter mit Fallback laden (mit Caching)
        params = get_parameter_for_year(KTGParameter, payroll.year)

        if not params:
            return {
                "ktg_effective_basis": Decimal("0.00"),
                "ktg_employee": Decimal("0.00"),
                "ktg_employer": Decimal("0.00"),
            }

        basis = safe_decimal(payroll.uv_basis)

        # Optional: Kappung anwenden
        if params.ktg_max_basis:
            effective_basis = min(basis, params.ktg_max_basis)
        else:
            effective_basis = basis

        # KTG-Beiträge berechnen und auf 0.05 CHF runden
        ktg_employee_raw = effective_basis * params.ktg_rate_employee
        ktg_employer_raw = effective_basis * params.ktg_rate_employer

        ktg_employee = round_to_5_rappen(ktg_employee_raw)
        ktg_employer = round_to_5_rappen(ktg_employer_raw)

        return {
            "ktg_effective_basis": effective_basis,
            "ktg_employee": ktg_employee,
            "ktg_employer": ktg_employer,
        }



