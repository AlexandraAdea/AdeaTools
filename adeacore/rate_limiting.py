"""
Rate-Limiting für Login und API-Endpunkte.

Schützt vor Brute-Force-Angriffen und DDoS.
"""

import time
from datetime import datetime, timedelta
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate-Limiter für verschiedene Endpunkte.
    
    Verwendet Django-Cache für Speicherung der Rate-Limit-Daten.
    """
    
    def __init__(self, max_requests: int = 5, window_seconds: int = 300):
        """
        Initialisiert Rate-Limiter.
        
        Args:
            max_requests: Maximale Anzahl Anfragen im Zeitfenster
            window_seconds: Zeitfenster in Sekunden (Standard: 5 Minuten)
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    def is_allowed(self, key: str) -> tuple[bool, int]:
        """
        Prüft ob Anfrage erlaubt ist.
        
        Args:
            key: Eindeutiger Schlüssel (z.B. IP-Adresse oder Username)
            
        Returns:
            Tuple (is_allowed, remaining_requests)
        """
        cache_key = f"rate_limit:{key}"
        now = timezone.now()
        
        # Hole aktuelle Anfragen
        requests = cache.get(cache_key, [])
        
        # Entferne alte Anfragen (älter als Zeitfenster)
        cutoff_time = now - timedelta(seconds=self.window_seconds)
        requests = [req_time for req_time in requests if req_time > cutoff_time]
        
        # Prüfe ob Limit überschritten
        if len(requests) >= self.max_requests:
            # Berechne verbleibende Zeit bis nächste Anfrage möglich
            oldest_request = min(requests)
            retry_after = int((oldest_request + timedelta(seconds=self.window_seconds) - now).total_seconds())
            return False, retry_after
        
        # Füge aktuelle Anfrage hinzu
        requests.append(now)
        cache.set(cache_key, requests, timeout=self.window_seconds)
        
        remaining = self.max_requests - len(requests)
        return True, remaining
    
    def reset(self, key: str):
        """Setzt Rate-Limit für einen Schlüssel zurück."""
        cache_key = f"rate_limit:{key}"
        cache.delete(cache_key)


# Globale Rate-Limiter-Instanzen
login_rate_limiter = RateLimiter(max_requests=5, window_seconds=300)  # 5 Versuche in 5 Minuten
api_rate_limiter = RateLimiter(max_requests=100, window_seconds=60)  # 100 Anfragen pro Minute


def rate_limit_login(view_func):
    """
    Decorator für Login-Views mit Rate-Limiting.
    
    Verwendet IP-Adresse als Schlüssel.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Hole IP-Adresse
        ip_address = get_client_ip(request)
        
        # Prüfe Rate-Limit
        is_allowed, retry_after = login_rate_limiter.is_allowed(ip_address)
        
        if not is_allowed:
            # Rate-Limit überschritten
            response = HttpResponse(
                "Zu viele Login-Versuche. Bitte versuchen Sie es später erneut.",
                status=429  # Too Many Requests
            )
            response['Retry-After'] = str(retry_after)
            return response
        
        # Rate-Limit OK, fahre fort
        return view_func(request, *args, **kwargs)
    
    return wrapper


def rate_limit_api(view_func):
    """
    Decorator für API-Views mit Rate-Limiting.
    
    Verwendet IP-Adresse als Schlüssel.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Hole IP-Adresse
        ip_address = get_client_ip(request)
        
        # Prüfe Rate-Limit
        is_allowed, remaining = api_rate_limiter.is_allowed(ip_address)
        
        if not is_allowed:
            # Rate-Limit überschritten
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'retry_after': remaining
            }, status=429)
        
        # Rate-Limit OK, füge Header hinzu
        response = view_func(request, *args, **kwargs)
        if hasattr(response, 'headers'):
            response['X-RateLimit-Remaining'] = str(remaining)
            response['X-RateLimit-Limit'] = str(api_rate_limiter.max_requests)
        return response
    
    return wrapper


def get_client_ip(request) -> str:
    """Holt die IP-Adresse aus dem Request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    return ip


def reset_login_rate_limit(username: str, ip_address: str):
    """
    Setzt Rate-Limit nach erfolgreichem Login zurück.
    
    Args:
        username: Benutzername
        ip_address: IP-Adresse
    """
    # Setze beide Limits zurück (Username und IP)
    login_rate_limiter.reset(f"username:{username}")
    login_rate_limiter.reset(ip_address)

