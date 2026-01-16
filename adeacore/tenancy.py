"""
Multi-Tenant Helper (Client als Mandant).

Ziel: zentrale, konsistente Session->Client Auflösung mit den gleichen Sicherheitschecks
wie bisher in AdeaLohn (nur FIRMA + lohn_aktiv).
"""

from __future__ import annotations

from typing import Optional


def resolve_current_client(request, *, session_key: str = "active_client_id") -> Optional["Client"]:
    """
    Liefert den aktiven Mandanten (Client) aus der Session und cached ihn auf dem Request.

    Verhalten (1:1 zu bisheriger Logik in `adealohn.mixins.TenantMixin` und
    `adeacore.context_processors.current_client`):
    - Session-Key `active_client_id` lesen
    - Client laden
    - Sicherheitscheck: nur `client_type == "FIRMA"` UND `lohn_aktiv == True`
    - bei Verstoß: Session-Key entfernen und `None` zurückgeben
    """
    # Cache: wenn bereits gesetzt, wiederverwenden (verhindert Doppel-Queries)
    if hasattr(request, "current_client"):
        return getattr(request, "current_client")

    active_client_id = request.session.get(session_key)
    if not active_client_id:
        request.current_client = None
        return None

    from adeacore.models import Client  # local import to avoid import cycles

    try:
        client = Client.objects.get(pk=active_client_id)
    except Client.DoesNotExist:
        request.session.pop(session_key, None)
        request.current_client = None
        return None

    # Sicherheitsprüfung: Nur FIRMA-Clients mit aktiviertem Lohnmodul erlauben
    if client.client_type != "FIRMA" or not client.lohn_aktiv:
        request.session.pop(session_key, None)
        request.current_client = None
        return None

    request.current_client = client
    return client

