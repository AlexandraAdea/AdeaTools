"""
Automatische Backup-Strategie für AdeaTools.

DSGVO/DSG 2023 konform - Art. 32 (Verfügbarkeit)
"""

import os
import shutil
import json
from datetime import datetime, timedelta
from pathlib import Path
from django.conf import settings
from django.core.management import call_command
from django.db import connection
import logging

logger = logging.getLogger(__name__)


class BackupManager:
    """
    Verwaltet automatische Backups der Datenbank und wichtiger Dateien.
    
    Strategie:
    - Täglich automatisch (23:00 Uhr)
    - Vor kritischen Operationen (manuell)
    - Aufbewahrung: 30 Tage
    """
    
    def __init__(self):
        """Initialisiert den Backup Manager."""
        self.backup_dir = Path(settings.BASE_DIR) / 'backups'
        self.backup_dir.mkdir(exist_ok=True)
        self.retention_days = 30
    
    def create_backup(self, backup_type: str = 'auto', description: str = '') -> Path:
        """
        Erstellt ein Backup.
        
        Args:
            backup_type: Typ des Backups ('auto', 'manual', 'before_migration')
            description: Beschreibung des Backups
            
        Returns:
            Pfad zum Backup-Verzeichnis
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{backup_type}_{timestamp}"
        if description:
            backup_name += f"_{description.replace(' ', '_')}"
        
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        try:
            # Backup der Datenbank
            db_backup_path = backup_path / 'database'
            db_backup_path.mkdir(exist_ok=True)
            
            # SQLite: Kopiere Datenbank-Datei
            db_path = settings.DATABASES['default']['NAME']
            if isinstance(db_path, Path):
                db_path = str(db_path)
            
            if os.path.exists(db_path):
                shutil.copy2(db_path, db_backup_path / 'db.sqlite3')
            
            # Backup der Audit-Logs
            logs_dir = Path(settings.BASE_DIR) / 'logs'
            if logs_dir.exists():
                logs_backup_path = backup_path / 'logs'
                shutil.copytree(logs_dir, logs_backup_path, dirs_exist_ok=True)
            
            # Backup-Metadaten
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'type': backup_type,
                'description': description,
                'database': db_path,
                'django_version': settings.DJANGO_VERSION if hasattr(settings, 'DJANGO_VERSION') else 'unknown'
            }
            
            with open(backup_path / 'metadata.json', 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Backup erstellt: {backup_path}")
            
            # Alte Backups löschen
            self.cleanup_old_backups()
            
            return backup_path
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Backups: {e}", exc_info=True)
            # Lösche fehlerhaftes Backup-Verzeichnis
            if backup_path.exists():
                shutil.rmtree(backup_path)
            raise
    
    def cleanup_old_backups(self):
        """Löscht Backups älter als retention_days."""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        deleted_count = 0
        
        for backup_dir in self.backup_dir.iterdir():
            if not backup_dir.is_dir():
                continue
            
            # Prüfe Timestamp im Verzeichnisnamen
            try:
                # Format: auto_20251126_143000
                parts = backup_dir.name.split('_')
                if len(parts) >= 3:
                    date_str = f"{parts[1]}_{parts[2]}"
                    backup_date = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
                    
                    if backup_date < cutoff_date:
                        shutil.rmtree(backup_dir)
                        deleted_count += 1
                        logger.info(f"Altes Backup gelöscht: {backup_dir.name}")
            except (ValueError, IndexError):
                # Falls Format nicht erkannt, überspringe
                continue
        
        if deleted_count > 0:
            logger.info(f"{deleted_count} alte Backups gelöscht")
    
    def list_backups(self) -> list:
        """
        Listet alle verfügbaren Backups.
        
        Returns:
            Liste von Backup-Verzeichnissen (sortiert nach Datum, neueste zuerst)
        """
        backups = []
        
        for backup_dir in self.backup_dir.iterdir():
            if not backup_dir.is_dir():
                continue
            
            metadata_path = backup_dir / 'metadata.json'
            if metadata_path.exists():
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    metadata['path'] = backup_dir
                    backups.append(metadata)
                except Exception:
                    pass
        
        # Sortiere nach Timestamp (neueste zuerst)
        backups.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return backups
    
    def restore_backup(self, backup_path: Path) -> bool:
        """
        Stellt ein Backup wieder her.
        
        Args:
            backup_path: Pfad zum Backup-Verzeichnis
            
        Returns:
            True wenn erfolgreich, False sonst
        """
        try:
            # Prüfe ob Backup existiert
            if not backup_path.exists():
                logger.error(f"Backup nicht gefunden: {backup_path}")
                return False
            
            metadata_path = backup_path / 'metadata.json'
            if not metadata_path.exists():
                logger.error(f"Backup-Metadaten nicht gefunden: {metadata_path}")
                return False
            
            # Lade Metadaten
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Erstelle Backup vor Restore (Sicherheit!)
            self.create_backup(backup_type='manual', description='before_restore')
            
            # Stelle Datenbank wieder her
            db_backup_path = backup_path / 'database' / 'db.sqlite3'
            if db_backup_path.exists():
                db_path = settings.DATABASES['default']['NAME']
                if isinstance(db_path, Path):
                    db_path = str(db_path)
                
                # Backup der aktuellen Datenbank
                if os.path.exists(db_path):
                    shutil.copy2(db_path, f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                
                # Stelle wieder her
                shutil.copy2(db_backup_path, db_path)
                logger.info(f"Datenbank wiederhergestellt aus: {backup_path}")
            
            # Stelle Logs wieder her (optional)
            # Überspringe Logs, falls sie von einem Prozess verwendet werden
            logs_backup_path = backup_path / 'logs'
            if logs_backup_path.exists():
                try:
                    logs_dir = Path(settings.BASE_DIR) / 'logs'
                    if logs_dir.exists():
                        # Versuche einzelne Dateien zu kopieren statt rmtree
                        for log_file in logs_backup_path.glob('*'):
                            if log_file.is_file():
                                try:
                                    shutil.copy2(log_file, logs_dir / log_file.name)
                                except PermissionError:
                                    logger.warning(f"Konnte Log-Datei nicht kopieren (wird verwendet): {log_file.name}")
                    else:
                        shutil.copytree(logs_backup_path, logs_dir)
                    logger.info(f"Logs wiederhergestellt aus: {backup_path}")
                except PermissionError:
                    logger.warning("Konnte Logs nicht wiederherstellen (Dateien werden verwendet)")
            
            logger.info(f"Backup erfolgreich wiederhergestellt: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Wiederherstellen des Backups: {e}", exc_info=True)
            return False


# Globale Instanz
_backup_manager = None


def get_backup_manager() -> BackupManager:
    """Liefert die globale BackupManager-Instanz."""
    global _backup_manager
    if _backup_manager is None:
        _backup_manager = BackupManager()
    return _backup_manager

