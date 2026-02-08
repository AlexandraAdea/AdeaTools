"""
Zentrale Helper-Funktionen für AdeaLohn-Modul.

Ziel: DRY-Prinzip durchdringen, Code-Duplikation eliminieren.
"""

from decimal import Decimal
from functools import lru_cache
from typing import Type, Optional, Any, Dict

from django.db import models


# ============================================================================
# Prozent/Dezimal-Konvertierung
# ============================================================================

def percent_to_decimal(percent: float | Decimal | str) -> Decimal:
    """
    Konvertiert Prozentwert (z.B. 5.3) zu Dezimal (z.B. 0.053).
    
    Args:
        percent: Prozentwert (z.B. 5.3 für 5.3%)
    
    Returns:
        Dezimalwert (z.B. Decimal("0.053"))
    
    Examples:
        >>> percent_to_decimal(5.3)
        Decimal('0.053')
        >>> percent_to_decimal("5.3")
        Decimal('0.053')
    """
    if isinstance(percent, str):
        percent = float(percent)
    return Decimal(str(percent)) / Decimal("100")


def decimal_to_percent(decimal: Decimal | float | str) -> Decimal:
    """
    Konvertiert Dezimalwert (z.B. 0.053) zu Prozent (z.B. 5.3).
    
    Args:
        decimal: Dezimalwert (z.B. 0.053 für 5.3%)
    
    Returns:
        Prozentwert (z.B. Decimal("5.3"))
    
    Examples:
        >>> decimal_to_percent(Decimal("0.053"))
        Decimal('5.3')
        >>> decimal_to_percent(0.053)
        Decimal('5.3')
    """
    if isinstance(decimal, str):
        decimal = Decimal(decimal)
    elif isinstance(decimal, float):
        decimal = Decimal(str(decimal))
    return decimal * Decimal("100")


# ============================================================================
# Parameter-Abfrage mit Caching
# ============================================================================

def get_parameter_for_year(
    model_class: Type[models.Model],
    year: int,
    defaults: Optional[Dict[str, Any]] = None,
    **filters
) -> Optional[models.Model]:
    """
    Lädt Parameter für ein bestimmtes Jahr mit Fallback auf Standardwerte.
    
    Args:
        model_class: Django Model-Klasse (z.B. AHVParameter)
        year: Jahr für die Parameter
        defaults: Dictionary mit Standardwerten (falls Parameter nicht existiert)
        **filters: Zusätzliche Filter (z.B. canton="AG" für FAKParameter)
    
    Returns:
        Parameter-Instanz oder None (falls defaults=None)
    
    Examples:
        >>> from adealohn.models import AHVParameter
        >>> params = get_parameter_for_year(AHVParameter, 2025)
        >>> params.rate_employee
        Decimal('0.053')
        
        >>> from adealohn.models import FAKParameter
        >>> params = get_parameter_for_year(FAKParameter, 2025, canton="AG")
    """
    # Versuche Parameter zu laden
    queryset = model_class.objects.filter(year=year, **filters)
    param = queryset.first()
    
    if param:
        return param
    
    # Fallback auf defaults (falls vorhanden)
    if defaults:
        # Erstelle temporäre Instanz mit defaults (nicht gespeichert)
        param = model_class(year=year, **defaults, **filters)
        return param
    
    return None


# Cache-Wrapper für get_parameter_for_year (mit hashbarem Key)
@lru_cache(maxsize=128)
def _get_parameter_cached(model_name: str, year: int, filters_tuple: tuple):
    """
    Interne Cached-Version von get_parameter_for_year.
    """
    from adealohn.models import (
        AHVParameter, ALVParameter, VKParameter, KTGParameter,
        UVGParameter, FAKParameter, BVGParameter
    )
    
    model_map = {
        'AHVParameter': AHVParameter,
        'ALVParameter': ALVParameter,
        'VKParameter': VKParameter,
        'KTGParameter': KTGParameter,
        'UVGParameter': UVGParameter,
        'FAKParameter': FAKParameter,
        'BVGParameter': BVGParameter,
    }
    
    model_class = model_map.get(model_name)
    if not model_class:
        return None
    
    filters = dict(filters_tuple) if filters_tuple else {}
    return get_parameter_for_year(model_class, year, **filters)


def get_parameter_for_year_cached(
    model_class: Type[models.Model],
    year: int,
    defaults: Optional[Dict[str, Any]] = None,
    **filters
) -> Optional[models.Model]:
    """
    Cached-Version von get_parameter_for_year.
    
    Verwendet LRU-Cache für Performance (max 128 Einträge).
    """
    model_name = model_class.__name__
    filters_tuple = tuple(sorted(filters.items()))
    
    result = _get_parameter_cached(model_name, year, filters_tuple)
    
    # Falls None und defaults vorhanden, erstelle temporäre Instanz
    if result is None and defaults:
        return model_class(year=year, **defaults, **filters)
    
    return result


def clear_parameter_cache():
    """
    Leert den Parameter-Cache.
    
    Sollte nach Änderungen an Parametern aufgerufen werden.
    """
    _get_parameter_cached.cache_clear()


# Verwende cached Version standardmäßig
# (Kann später auf get_parameter_for_year_cached umgestellt werden, wenn Caching benötigt wird)
# get_parameter_for_year = get_parameter_for_year_cached


# ============================================================================
# Safe Decimal-Helper
# ============================================================================

def safe_decimal(value: Any, default: Decimal = Decimal("0.00")) -> Decimal:
    """
    Konvertiert einen Wert sicher zu Decimal mit Fallback.
    
    Args:
        value: Wert zum Konvertieren (kann None, str, float, Decimal sein)
        default: Standardwert falls value None oder ungültig
    
    Returns:
        Decimal-Wert
    
    Examples:
        >>> safe_decimal(None)
        Decimal('0.00')
        >>> safe_decimal("123.45")
        Decimal('123.45')
        >>> safe_decimal(123.45)
        Decimal('123.45')
    """
    if value is None:
        return default
    
    try:
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))
    except (ValueError, TypeError):
        return default


# ============================================================================
# YTD-Basis-Helper
# ============================================================================

def get_ytd_basis(employee, field_name: str, default: Decimal = Decimal("0.00")) -> Decimal:
    """
    Lädt YTD-Basis-Wert von einem Employee sicher.
    
    Args:
        employee: Employee-Instanz
        field_name: Feldname (z.B. "alv_ytd_basis", "uvg_ytd_basis")
        default: Standardwert falls Feld nicht existiert oder None
    
    Returns:
        Decimal-Wert
    
    Examples:
        >>> get_ytd_basis(employee, "alv_ytd_basis")
        Decimal('5000.00')
    """
    if not employee:
        return default
    
    value = getattr(employee, field_name, None)
    return safe_decimal(value, default)


# ============================================================================
# WageType-Helper
# ============================================================================

def ensure_wage_type(
    code: str,
    name: str,
    category: str = "BASIS",
    is_lohnwirksam: bool = True,
    ahv_relevant: bool = True,
    alv_relevant: bool = True,
    uv_relevant: bool = True,
    bvg_relevant: bool = True,
    qst_relevant: bool = True,
    taxable: bool = True,
    **overrides
) -> 'WageType':
    """
    Erstellt oder lädt einen WageType mit gegebenen Eigenschaften.
    
    Args:
        code: Eindeutiger Code (z.B. "GRUNDLOHN_STUNDEN")
        name: Anzeigename
        category: Kategorie (Standard: "BASIS")
        is_lohnwirksam: Ist lohnwirksam (Standard: True)
        ahv_relevant: AHV-relevant (Standard: True)
        alv_relevant: ALV-relevant (Standard: True)
        uv_relevant: UV-relevant (Standard: True)
        bvg_relevant: BVG-relevant (Standard: True)
        qst_relevant: QST-relevant (Standard: True)
        taxable: Steuerpflichtig (Standard: True)
        **overrides: Zusätzliche Felder zum Überschreiben
    
    Returns:
        WageType-Instanz
    
    Examples:
        >>> from adealohn.models import WageTypeCategory
        >>> wt = ensure_wage_type(
        ...     "GRUNDLOHN_STUNDEN",
        ...     "Grundlohn Stundenlohn",
        ...     category=WageTypeCategory.GRUNDLOHN
        ... )
    """
    from adealohn.models import WageType, WageTypeCategory
    
    defaults = {
        "name": name,
        "category": category,
        "is_lohnwirksam": is_lohnwirksam,
        "ahv_relevant": ahv_relevant,
        "alv_relevant": alv_relevant,
        "uv_relevant": uv_relevant,
        "bvg_relevant": bvg_relevant,
        "qst_relevant": qst_relevant,
        "taxable": taxable,
        **overrides
    }
    
    wage_type, _ = WageType.objects.get_or_create(code=code, defaults=defaults)
    return wage_type


def ensure_grundlohn_wage_type(employee_type: str = "STUNDEN") -> 'WageType':
    """
    Erstellt oder lädt einen Grundlohn-WageType.
    
    Args:
        employee_type: "STUNDEN" oder "MONAT"
    
    Returns:
        WageType-Instanz
    
    Examples:
        >>> wt = ensure_grundlohn_wage_type("STUNDEN")
    """
    from adealohn.models import WageTypeCategory
    
    code = f"GRUNDLOHN_{employee_type}"
    name = f"Grundlohn {'Stundenlohn' if employee_type == 'STUNDEN' else 'Monatslohn'}"
    
    return ensure_wage_type(
        code=code,
        name=name,
        category=WageTypeCategory.GRUNDLOHN,
        is_lohnwirksam=True,
        ahv_relevant=True,
        alv_relevant=True,
        uv_relevant=True,
        bvg_relevant=True,
        qst_relevant=True,
    )


def ensure_ferien_wage_type() -> 'WageType':
    """
    Erstellt oder lädt einen Ferienentschädigung-WageType.
    
    Returns:
        WageType-Instanz
    
    Examples:
        >>> wt = ensure_ferien_wage_type()
    """
    from adealohn.models import WageTypeCategory
    
    return ensure_wage_type(
        code="FERIENENTSCHAEDIGUNG",
        name="Ferienentschädigung",
        category=WageTypeCategory.ZULAGE,
        is_lohnwirksam=True,
        ahv_relevant=True,
        alv_relevant=True,
        uv_relevant=True,
        bvg_relevant=False,  # WICHTIG: Ferienentschädigung ist NICHT BVG-relevant!
        qst_relevant=True,
    )


# ============================================================================
# Client-Filter-Helper
# ============================================================================

def get_firma_clients_with_lohn_aktiv():
    """
    Lädt alle FIRMA-Clients mit aktiviertem Lohnmodul.
    
    Returns:
        QuerySet von Client-Instanzen
    
    Examples:
        >>> clients = get_firma_clients_with_lohn_aktiv()
    """
    from adeacore.models import Client
    return Client.objects.filter(client_type="FIRMA", lohn_aktiv=True).order_by("name")


# ============================================================================
# WageType-Filter-Helper
# ============================================================================

def filter_wage_types_by_code(
    queryset,
    excluded_codes: list = None,
    excluded_prefixes: list = None
):
    """
    Filtert WageTypes nach ausgeschlossenen Codes und Präfixen.
    
    Args:
        queryset: WageType QuerySet
        excluded_codes: Liste von Codes zum Ausschließen
        excluded_prefixes: Liste von Präfixen zum Ausschließen
    
    Returns:
        Gefilterter QuerySet
    
    Examples:
        >>> from adealohn.models import WageType
        >>> qs = WageType.objects.all()
        >>> qs = filter_wage_types_by_code(
        ...     qs,
        ...     excluded_codes=["GRUNDLOHN_STUNDEN"],
        ...     excluded_prefixes=["SPESEN_"]
        ... )
    """
    if excluded_codes:
        queryset = queryset.exclude(code__in=excluded_codes)
    
    if excluded_prefixes:
        for prefix in excluded_prefixes:
            queryset = queryset.exclude(code__startswith=prefix)
    
    return queryset
