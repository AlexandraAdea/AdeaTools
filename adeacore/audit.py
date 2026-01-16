"""
Audit-Logging-System für alle Datenänderungen.

DSGVO/DSG 2023 konform - Art. 30 (Verzeichnis der Verarbeitungstätigkeiten)
OR Art. 957f (Revisionspflicht)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from django.conf import settings
from django.contrib.auth import get_user_model

from adeacore.http import get_client_ip

User = get_user_model()

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Protokolliert alle sicherheitsrelevanten Aktionen.
    
    Format: JSON (eine Zeile pro Aktion)
    Aufbewahrung: 10 Jahre (OR-Pflicht)
    """
    
    def __init__(self):
        """Initialisiert den Audit Logger."""
        self.log_dir = Path(settings.BASE_DIR) / 'logs'
        self.log_dir.mkdir(exist_ok=True)
        
        # Log-Datei: Eine pro Jahr
        year = datetime.now().year
        self.log_file = self.log_dir / f'audit_{year}.jsonl'
    
    def log_action(
        self,
        user: Optional[User],
        action: str,
        model_name: str,
        object_id: Optional[int] = None,
        object_repr: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[str] = None
    ):
        """
        Protokolliert eine Aktion.
        
        Args:
            user: Benutzer der die Aktion ausgeführt hat
            action: Aktion (CREATE, UPDATE, DELETE, VIEW, LOGIN, LOGOUT)
            model_name: Name des Models (z.B. 'Client', 'EmployeeInternal')
            object_id: ID des Objekts
            object_repr: String-Repräsentation des Objekts
            changes: Dict mit Änderungen (für UPDATE)
            ip_address: IP-Adresse des Benutzers
            user_agent: User-Agent des Browsers
            details: Zusätzliche Details
        """
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'user': user.username if user else 'system',
                'user_id': user.id if user else None,
                'action': action,
                'model': model_name,
                'object_id': object_id,
                'object_repr': object_repr,
                'changes': changes or {},
                'ip_address': ip_address,
                'user_agent': user_agent,
                'details': details
            }
            
            # Als JSON-Zeile anhängen (append-only!)
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            
            # Auch in Django-Logging (für Debugging)
            logger.info(f"Audit: {action} {model_name} {object_id} by {user.username if user else 'system'}")
            
        except Exception as e:
            # Fehler beim Logging sollten nicht die Anwendung stoppen
            logger.error(f"Audit-Logging fehlgeschlagen: {e}", exc_info=True)
    
    def get_logs(
        self,
        user: Optional[str] = None,
        action: Optional[str] = None,
        model_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> list:
        """
        Holt Audit-Logs mit Filtern.
        
        Args:
            user: Benutzername (Filter)
            action: Aktion (Filter)
            model_name: Model-Name (Filter)
            start_date: Start-Datum (Filter)
            end_date: End-Datum (Filter)
            limit: Maximale Anzahl Ergebnisse
            
        Returns:
            Liste von Log-Einträgen
        """
        logs = []
        
        try:
            if not self.log_file.exists():
                return logs
            
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        
                        # Filter anwenden
                        if user and entry.get('user') != user:
                            continue
                        if action and entry.get('action') != action:
                            continue
                        if model_name and entry.get('model') != model_name:
                            continue
                        
                        # Datum-Filter
                        if start_date or end_date:
                            entry_date = datetime.fromisoformat(entry['timestamp'])
                            if start_date and entry_date < start_date:
                                continue
                            if end_date and entry_date > end_date:
                                continue
                        
                        logs.append(entry)
                        
                        if len(logs) >= limit:
                            break
                    
                    except json.JSONDecodeError:
                        continue  # Überspringe ungültige Zeilen
            
            # Neueste zuerst
            logs.reverse()
            
        except Exception as e:
            logger.error(f"Fehler beim Lesen von Audit-Logs: {e}", exc_info=True)
        
        return logs


# Globale Instanz
_audit_logger = None


def get_audit_logger() -> AuditLogger:
    """Liefert die globale AuditLogger-Instanz."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def get_user_agent(request) -> Optional[str]:
    """Holt den User-Agent aus dem Request."""
    return request.META.get('HTTP_USER_AGENT', '')[:500]  # Begrenze Länge




