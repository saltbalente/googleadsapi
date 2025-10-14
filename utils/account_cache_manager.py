"""
Account Cache Manager - Gestión de caché persistente para nombres de cuentas
Evita consultas innecesarias a la API de Google Ads
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class AccountCacheManager:
    """Gestiona el caché persistente de nombres de cuentas de Google Ads"""
    
    def __init__(self, cache_file: str = "data/account_names_cache.json", cache_days: int = 30):
        """
        Inicializa el gestor de caché de cuentas
        
        Args:
            cache_file: Ruta del archivo de caché
            cache_days: Días antes de que expire el caché (default: 30)
        """
        self.cache_file = Path(cache_file)
        self.cache_days = cache_days
        self._ensure_cache_directory()
        
    def _ensure_cache_directory(self):
        """Crea el directorio de caché si no existe"""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        
    def _load_cache(self) -> Dict:
        """Carga el caché desde el archivo JSON"""
        if not self.cache_file.exists():
            return {}
        
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                logger.info(f"✅ Caché cargado: {len(cache_data.get('accounts', {}))} cuentas")
                return cache_data
        except Exception as e:
            logger.error(f"❌ Error cargando caché: {e}")
            return {}
    
    def _save_cache(self, cache_data: Dict):
        """Guarda el caché en el archivo JSON"""
        try:
            cache_data['last_updated'] = datetime.now().isoformat()
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Caché guardado: {len(cache_data.get('accounts', {}))} cuentas")
        except Exception as e:
            logger.error(f"❌ Error guardando caché: {e}")
    
    def _is_cache_valid(self, cache_data: Dict) -> bool:
        """Verifica si el caché es válido (no ha expirado)"""
        if not cache_data or 'last_updated' not in cache_data:
            return False
        
        try:
            last_updated = datetime.fromisoformat(cache_data['last_updated'])
            expiration_date = last_updated + timedelta(days=self.cache_days)
            is_valid = datetime.now() < expiration_date
            
            if is_valid:
                days_left = (expiration_date - datetime.now()).days
                logger.info(f"✅ Caché válido. Expira en {days_left} días")
            else:
                logger.info("⚠️ Caché expirado")
            
            return is_valid
        except Exception as e:
            logger.error(f"❌ Error validando caché: {e}")
            return False
    
    def get_account_name(self, customer_id: str) -> Optional[str]:
        """
        Obtiene el nombre de una cuenta desde el caché
        
        Args:
            customer_id: ID del cliente
            
        Returns:
            Nombre de la cuenta o None si no está en caché
        """
        cache_data = self._load_cache()
        
        if not self._is_cache_valid(cache_data):
            return None
        
        accounts = cache_data.get('accounts', {})
        return accounts.get(customer_id)
    
    def get_all_account_names(self) -> Dict[str, str]:
        """
        Obtiene todos los nombres de cuentas del caché
        
        Returns:
            Diccionario con {customer_id: account_name}
        """
        cache_data = self._load_cache()
        
        if not self._is_cache_valid(cache_data):
            return {}
        
        return cache_data.get('accounts', {})
    
    def set_account_name(self, customer_id: str, account_name: str):
        """
        Guarda el nombre de una cuenta en el caché
        
        Args:
            customer_id: ID del cliente
            account_name: Nombre de la cuenta
        """
        cache_data = self._load_cache()
        
        if 'accounts' not in cache_data:
            cache_data['accounts'] = {}
        
        cache_data['accounts'][customer_id] = account_name
        self._save_cache(cache_data)
        logger.info(f"✅ Nombre guardado en caché: {customer_id} -> {account_name}")
    
    def set_multiple_accounts(self, accounts: Dict[str, str]):
        """
        Guarda múltiples nombres de cuentas en el caché
        
        Args:
            accounts: Diccionario con {customer_id: account_name}
        """
        cache_data = self._load_cache()
        
        if 'accounts' not in cache_data:
            cache_data['accounts'] = {}
        
        cache_data['accounts'].update(accounts)
        self._save_cache(cache_data)
        logger.info(f"✅ {len(accounts)} cuentas guardadas en caché")
    
    def clear_cache(self):
        """Limpia todo el caché"""
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
                logger.info("✅ Caché limpiado")
        except Exception as e:
            logger.error(f"❌ Error limpiando caché: {e}")
    
    def get_cache_info(self) -> Dict:
        """
        Obtiene información sobre el estado del caché
        
        Returns:
            Diccionario con información del caché
        """
        cache_data = self._load_cache()
        
        if not cache_data:
            return {
                'exists': False,
                'valid': False,
                'accounts_count': 0
            }
        
        is_valid = self._is_cache_valid(cache_data)
        accounts_count = len(cache_data.get('accounts', {}))
        
        info = {
            'exists': True,
            'valid': is_valid,
            'accounts_count': accounts_count,
            'last_updated': cache_data.get('last_updated', 'Desconocido'),
            'cache_file': str(self.cache_file)
        }
        
        if is_valid and 'last_updated' in cache_data:
            last_updated = datetime.fromisoformat(cache_data['last_updated'])
            expiration_date = last_updated + timedelta(days=self.cache_days)
            info['expires_in_days'] = (expiration_date - datetime.now()).days
        
        return info