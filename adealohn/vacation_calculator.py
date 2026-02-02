from decimal import Decimal


class VacationCalculator:
    """
    Berechnet Ferienentschädigung (Ferienzuschlag) gemäss Schweizer Recht:
    - 4 Wochen: 8.33% Zuschlag
    - 5 Wochen: 10.64% Zuschlag (Standard)
    - 6 Wochen: 13.04% Zuschlag
    - Wird nur bei Stundenlöhnen berechnet
    - Gehört zum Bruttolohn, ist AHV/ALV/NBU-pflichtig, aber NICHT BVG-pflichtig
    """

    RATE_4_WEEKS = Decimal("0.0833")  # 8.33%
    RATE_5_WEEKS = Decimal("0.1064")  # 10.64%
    RATE_6_WEEKS = Decimal("0.1304")  # 13.04%

    @classmethod
    def get_rate_for_weeks(cls, weeks: int) -> Decimal:
        """
        Gibt den Ferienzuschlag-Prozentsatz für die angegebene Anzahl Wochen zurück.
        """
        if weeks == 4:
            return cls.RATE_4_WEEKS
        elif weeks == 5:
            return cls.RATE_5_WEEKS
        elif weeks == 6:
            return cls.RATE_6_WEEKS
        else:
            # Fallback: 5 Wochen (Standard)
            return cls.RATE_5_WEEKS

    @classmethod
    def calculate_vacation_allowance(cls, base_salary: Decimal, vacation_weeks: int) -> Decimal:
        """
        Berechnet die Ferienentschädigung für einen gegebenen Grundlohn.

        Args:
            base_salary: Grundlohn (Stunden × Stundenlohn)
            vacation_weeks: Anzahl Ferienwochen (4, 5 oder 6)

        Returns:
            Ferienentschädigung (gerundet auf 0.01)
        """
        if base_salary <= 0:
            return Decimal("0.00")

        rate = cls.get_rate_for_weeks(vacation_weeks)
        vacation_allowance = base_salary * rate

        return vacation_allowance.quantize(Decimal("0.01"))
