"""
HTTP/Request Helper für AdeaCore.

Klein und bewusst "boring": nur zentrale, wiederverwendbare Request-Helfer.
"""

from __future__ import annotations

from typing import Optional


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

