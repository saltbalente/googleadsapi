"""
Sistema de Encriptación para Datos Sensibles
Encripta API keys y datos confidenciales localmente
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import os
import logging

logger = logging.getLogger(__name__)


class LocalEncryption:
    """Encripta y desencripta datos sensibles localmente"""
    
    def __init__(self, user_id: str = "saltbalente"):
        """
        Inicializa el sistema de encriptación
        
        Args:
            user_id: ID del usuario (usado como parte de la clave)
        """
        self.user_id = user_id
        self._key = None
    
    def _get_key(self) -> bytes:
        """
        Genera o recupera la clave de encriptación
        
        La clave se genera usando:
        - Machine ID (único por máquina)
        - User ID
        - Salt almacenado
        """
        if self._key:
            return self._key
        
        # Path para guardar el salt
        salt_file = f"data/user_data/{self.user_id}/.salt"
        os.makedirs(os.path.dirname(salt_file), exist_ok=True)
        
        # Generar o cargar salt
        if os.path.exists(salt_file):
            with open(salt_file, 'rb') as f:
                salt = f.read()
        else:
            salt = os.urandom(16)
            with open(salt_file, 'wb') as f:
                f.write(salt)
        
        # Generar clave usando PBKDF2
        # Usa el user_id + machine-specific data
        try:
            username = os.getlogin()
        except:
            username = "default_user"
            
        password = f"{self.user_id}_{username}".encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password))
        self._key = key
        
        return key
    
    def encrypt(self, data: str) -> str:
        """
        Encripta un string
        
        Args:
            data: String a encriptar
            
        Returns:
            String encriptado (base64)
        """
        try:
            f = Fernet(self._get_key())
            encrypted = f.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        
        except Exception as e:
            logger.error(f"Error encriptando datos: {e}")
            return ""
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Desencripta un string
        
        Args:
            encrypted_data: String encriptado
            
        Returns:
            String desencriptado
        """
        try:
            f = Fernet(self._get_key())
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = f.decrypt(decoded)
            return decrypted.decode()
        
        except Exception as e:
            logger.error(f"Error desencriptando datos: {e}")
            return ""


# Instancia global
_encryption = None

def get_encryption(user_id: str = "saltbalente") -> LocalEncryption:
    """Obtiene instancia global de encriptación"""
    global _encryption
    if _encryption is None or _encryption.user_id != user_id:
        _encryption = LocalEncryption(user_id)
    return _encryption