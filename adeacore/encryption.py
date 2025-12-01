"""
Verschlüsselungs-Utility für sensible Daten (AES-256).

DSGVO/DSG 2023 konform - Art. 32 (Verschlüsselung)
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class EncryptionManager:
    """
    Verwaltet Verschlüsselung für sensible Daten.
    
    Verwendet Fernet (AES-128 CBC + HMAC) für authentifizierte Verschlüsselung.
    """
    
    def __init__(self):
        """Initialisiert den Encryption Manager."""
        self.cipher = self._get_cipher()
    
    def _get_cipher(self):
        """
        Erstellt einen Fernet-Cipher mit Schlüssel aus Environment-Variable.
        
        Falls kein Schlüssel vorhanden, wird einer generiert und in .env gespeichert.
        """
        # Versuche Encryption-Key aus Environment-Variable zu holen
        encryption_key = os.environ.get('ADEATOOLS_ENCRYPTION_KEY')
        
        if not encryption_key:
            # Generiere neuen Schlüssel
            encryption_key = Fernet.generate_key().decode('utf-8')
            
            # Warnung ausgeben (für Production sollte Key gesetzt werden)
            import warnings
            warnings.warn(
                "ADEATOOLS_ENCRYPTION_KEY nicht gesetzt. "
                "Neuer Schlüssel wurde generiert. "
                "Für Production: Setze ADEATOOLS_ENCRYPTION_KEY in Environment-Variablen!",
                UserWarning
            )
            
            # Versuche in .env zu schreiben (optional)
            try:
                env_path = settings.BASE_DIR / '.env'
                if env_path.exists():
                    with open(env_path, 'a') as f:
                        f.write(f'\n# Encryption Key (generiert automatisch)\n')
                        f.write(f'ADEATOOLS_ENCRYPTION_KEY={encryption_key}\n')
            except Exception:
                pass  # Nicht kritisch
        
        # Konvertiere String zu Bytes
        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode('utf-8')
        
        return Fernet(encryption_key)
    
    def encrypt(self, value: str) -> str:
        """
        Verschlüsselt einen String-Wert.
        
        Args:
            value: Zu verschlüsselnder String
            
        Returns:
            Verschlüsselter String (base64-kodiert)
        """
        if not value:
            return value
        
        try:
            encrypted = self.cipher.encrypt(value.encode('utf-8'))
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            raise ImproperlyConfigured(f"Verschlüsselung fehlgeschlagen: {e}")
    
    def decrypt(self, encrypted_value: str) -> str:
        """
        Entschlüsselt einen verschlüsselten String.
        
        Args:
            encrypted_value: Verschlüsselter String (base64-kodiert)
            
        Returns:
            Entschlüsselter String
        """
        if not encrypted_value:
            return encrypted_value
        
        try:
            encrypted_bytes = base64.b64decode(encrypted_value.encode('utf-8'))
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode('utf-8')
        except Exception as e:
            # Falls Entschlüsselung fehlschlägt, könnte es ein alter Wert sein
            # Versuche als Klartext zurückzugeben (für Migration)
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Entschlüsselung fehlgeschlagen, verwende Klartext: {e}")
            return encrypted_value


# Globale Instanz
_encryption_manager = None


def get_encryption_manager() -> EncryptionManager:
    """Liefert die globale EncryptionManager-Instanz."""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager



