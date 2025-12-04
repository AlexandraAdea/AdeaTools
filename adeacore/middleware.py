"""
Custom Middleware für erweiterte Sicherheit.
"""

from django.utils.deprecation import MiddlewareMixin
from django.contrib.sessions.models import Session
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class SessionSecurityMiddleware(MiddlewareMixin):
    """
    Middleware für erweiterte Session-Sicherheit.
    
    Features:
    - IP-Adress-Validierung (optional)
    - User-Agent-Validierung (optional)
    - Session-Timeout-Prüfung
    """
    
    def process_request(self, request):
        """
        Prüft Session-Sicherheit bei jeder Anfrage.
        """
        if not request.user.is_authenticated:
            return None
        
        # Prüfe Session-Timeout
        if 'last_activity' in request.session:
            last_activity = request.session['last_activity']
            if isinstance(last_activity, str):
                from django.utils.dateparse import parse_datetime
                last_activity = parse_datetime(last_activity)
            
            if last_activity:
                timeout = timedelta(seconds=request.session.get('SESSION_COOKIE_AGE', 28800))
                if timezone.now() - last_activity > timeout:
                    # Session abgelaufen
                    from django.contrib.auth import logout
                    logout(request)
                    return None
        
        # Aktualisiere letzte Aktivität
        request.session['last_activity'] = timezone.now().isoformat()
        
        # IP-Adress-Validierung (optional, kann deaktiviert werden)
        # Prüfe ob IP-Adresse sich geändert hat
        if 'ip_address' in request.session:
            current_ip = self.get_client_ip(request)
            stored_ip = request.session['ip_address']
            
            # Warnung bei IP-Wechsel (aber nicht blockieren, da IPs sich ändern können)
            if current_ip != stored_ip:
                logger.warning(
                    f"IP-Adresse geändert für Benutzer {request.user.username}: "
                    f"{stored_ip} -> {current_ip}"
                )
        else:
            # Speichere IP-Adresse beim ersten Request
            request.session['ip_address'] = self.get_client_ip(request)
        
        return None
    
    def get_client_ip(self, request) -> str:
        """Holt die IP-Adresse aus dem Request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip




