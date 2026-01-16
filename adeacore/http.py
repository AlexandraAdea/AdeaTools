"""
HTTP/Request Helper für AdeaCore.

Klein und bewusst "boring": nur zentrale, wiederverwendbare Request-Helfer.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

from django.http import JsonResponse


def get_client_ip(request, *, default: Optional[str] = "unknown") -> Optional[str]:
    """
    Ermittelt die Client-IP aus einem Django-Request.

    - Nutzt zuerst `HTTP_X_FORWARDED_FOR` (falls vorhanden) und nimmt die erste IP.
    - Fällt sonst auf `REMOTE_ADDR` zurück.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # "client, proxy1, proxy2" -> "client"
        ip = x_forwarded_for.split(",")[0].strip()
        return ip or default
    return request.META.get("REMOTE_ADDR") or default


def json_ok(payload: Optional[Mapping[str, Any]] = None, *, status: int = 200, **extra) -> JsonResponse:
    """
    Standardisierte JSON-Response für Erfolg.

    WICHTIG: `status` default = 200 (wie JsonResponse), damit bestehende Endpunkte
    bei einer reinen DRY-Umstellung kein Verhalten ändern.
    """
    data: dict[str, Any] = {"success": True}
    if payload:
        data.update(dict(payload))
    if extra:
        data.update(extra)
    return JsonResponse(data, status=status)


def json_error(error: str, *, status: int = 200, code: Optional[str] = None, **extra) -> JsonResponse:
    """
    Standardisierte JSON-Response für Fehler.

    Default `status` ist absichtlich 200, weil im Bestand manche Endpunkte Fehler
    ohne HTTP-Status setzen. Wenn ein Status nötig ist: status=400/403/500 explizit setzen.
    """
    data: dict[str, Any] = {"success": False, "error": error}
    if code:
        data["code"] = code
    if extra:
        data.update(extra)
    return JsonResponse(data, status=status)

