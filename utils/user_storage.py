"""
Sistema de Almacenamiento Local de Usuario
Guarda preferencias, API keys, configuraciones, etc.
"""

import json
import os
from typing import Any, Dict, Optional, List
from datetime import datetime
from pathlib import Path
import logging
from utils.encryption import get_encryption

logger = logging.getLogger(__name__)


class UserStorage:
    """
    Sistema de almacenamiento local para datos de usuario
    
    Características:
    - Guarda datos en JSON
    - Encripta API keys automáticamente
    - Sincronización automática
    - Historial de cambios
    """
    
    def __init__(self, user_id: str = "saltbalente"):
        """
        Inicializa el storage del usuario
        
        Args:
            user_id: ID único del usuario
        """
        self.user_id = user_id
        self.base_path = Path(f"data/user_data/{user_id}")
        self.encryption = get_encryption(user_id)
        
        # Crear directorios
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Paths de archivos
        self.files = {
            'preferences': self.base_path / 'preferences.json',
            'api_keys': self.base_path / 'api_keys.enc',
            'settings': self.base_path / 'settings.json',
            'favorites': self.base_path / 'favorites.json',
            'history': self.base_path / 'history.json',
            'campaigns_config': self.base_path / 'campaigns_config.json',
            'theme': self.base_path / 'theme.json'
        }
        
        # Cache en memoria
        self._cache = {}
        
        logger.info(f"✅ UserStorage inicializado para {user_id}")
    
    # ========================================================================
    # PREFERENCIAS (UI, idioma, etc.)
    # ========================================================================
    
    def get_preferences(self) -> Dict[str, Any]:
        """Obtiene preferencias del usuario"""
        if 'preferences' in self._cache:
            return self._cache['preferences']
        
        try:
            if self.files['preferences'].exists():
                with open(self.files['preferences'], 'r', encoding='utf-8') as f:
                    prefs = json.load(f)
            else:
                prefs = self._get_default_preferences()
                self.save_preferences(prefs)
            
            self._cache['preferences'] = prefs
            return prefs
        
        except Exception as e:
            logger.error(f"Error cargando preferencias: {e}")
            return self._get_default_preferences()
    
    def save_preferences(self, preferences: Dict[str, Any]) -> bool:
        """Guarda preferencias del usuario"""
        try:
            preferences['last_updated'] = datetime.utcnow().isoformat()
            
            with open(self.files['preferences'], 'w', encoding='utf-8') as f:
                json.dump(preferences, f, indent=2, ensure_ascii=False)
            
            self._cache['preferences'] = preferences
            logger.info("✅ Preferencias guardadas")
            return True
        
        except Exception as e:
            logger.error(f"Error guardando preferencias: {e}")
            return False
    
    def update_preference(self, key: str, value: Any) -> bool:
        """Actualiza una preferencia específica"""
        prefs = self.get_preferences()
        prefs[key] = value
        return self.save_preferences(prefs)
    
    def _get_default_preferences(self) -> Dict[str, Any]:
        """Preferencias por defecto"""
        return {
            'language': 'es',
            'theme': 'dark',
            'currency': 'USD',
            'timezone': 'UTC',
            'date_format': '%Y-%m-%d',
            'notifications_enabled': True,
            'auto_refresh': True,
            'refresh_interval': 300,  # 5 minutos
            'default_customer_id': None,
            'sidebar_collapsed': False,
            'created_at': datetime.utcnow().isoformat()
        }
    
    # ========================================================================
    # API KEYS (ENCRIPTADAS)
    # ========================================================================
    
    def get_api_keys(self) -> Dict[str, str]:
        """Obtiene API keys desencriptadas"""
        if 'api_keys' in self._cache:
            return self._cache['api_keys']
        
        try:
            if self.files['api_keys'].exists():
                with open(self.files['api_keys'], 'r', encoding='utf-8') as f:
                    encrypted_data = f.read()
                
                # Desencriptar
                decrypted = self.encryption.decrypt(encrypted_data)
                if decrypted:
                    api_keys = json.loads(decrypted)
                else:
                    api_keys = self._get_default_api_keys()
            else:
                api_keys = self._get_default_api_keys()
            
            self._cache['api_keys'] = api_keys
            return api_keys
        
        except Exception as e:
            logger.error(f"Error cargando API keys: {e}")
            return self._get_default_api_keys()
    
    def save_api_keys(self, api_keys: Dict[str, str]) -> bool:
        """Guarda API keys encriptadas"""
        try:
            # Agregar timestamp
            api_keys['last_updated'] = datetime.utcnow().isoformat()
            
            # Encriptar
            json_data = json.dumps(api_keys, indent=2)
            encrypted = self.encryption.encrypt(json_data)
            
            if not encrypted:
                logger.error("Falló la encriptación")
                return False
            
            # Guardar
            with open(self.files['api_keys'], 'w', encoding='utf-8') as f:
                f.write(encrypted)
            
            self._cache['api_keys'] = api_keys
            logger.info("✅ API keys guardadas (encriptadas)")
            return True
        
        except Exception as e:
            logger.error(f"Error guardando API keys: {e}")
            return False
    
    def update_api_key(self, provider: str, api_key: str, model: Optional[str] = None) -> bool:
        """Actualiza una API key específica"""
        api_keys = self.get_api_keys()
        
        api_keys[provider] = {
            'api_key': api_key,
            'model': model,
            'added_at': datetime.utcnow().isoformat()
        }
        
        return self.save_api_keys(api_keys)
    
    def get_api_key(self, provider: str) -> Optional[Dict[str, str]]:
        """Obtiene una API key específica"""
        api_keys = self.get_api_keys()
        return api_keys.get(provider)
    
    def _get_default_api_keys(self) -> Dict[str, Any]:
        """API keys por defecto (vacías)"""
        return {
            'openai': {'api_key': '', 'model': 'gpt-4o'},
            'gemini': {'api_key': '', 'model': 'gemini-2.0-flash-exp'},
            'anthropic': {'api_key': '', 'model': 'claude-3-5-sonnet-20241022'},
            'created_at': datetime.utcnow().isoformat()
        }
    
    # ========================================================================
    # CONFIGURACIONES GENERALES
    # ========================================================================
    
    def get_settings(self) -> Dict[str, Any]:
        """Obtiene configuraciones generales"""
        try:
            if self.files['settings'].exists():
                with open(self.files['settings'], 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self._get_default_settings()
        
        except Exception as e:
            logger.error(f"Error cargando settings: {e}")
            return self._get_default_settings()
    
    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """Guarda configuraciones generales"""
        try:
            # Merge con configuración existente
            current_settings = self.get_settings()
            current_settings.update(settings)
            current_settings['updated_at'] = datetime.utcnow().isoformat()
            
            with open(self.files['settings'], 'w', encoding='utf-8') as f:
                json.dump(current_settings, f, indent=2, ensure_ascii=False)
            
            return True
        
        except Exception as e:
            logger.error(f"Error guardando settings: {e}")
            return False
    
    def save_ai_settings(self, ai_settings: Dict[str, Any]) -> bool:
        """Guarda configuraciones específicas de IA"""
        try:
            # Obtener configuración actual
            current_settings = self.get_settings()
            
            # Actualizar sección de IA
            current_settings['ai_generation'] = ai_settings
            current_settings['updated_at'] = datetime.utcnow().isoformat()
            
            # Guardar
            with open(self.files['settings'], 'w', encoding='utf-8') as f:
                json.dump(current_settings, f, indent=2, ensure_ascii=False)
            
            return True
        
        except Exception as e:
            logger.error(f"Error guardando configuración de IA: {e}")
            return False

    def _get_default_settings(self) -> Dict[str, Any]:
        """Settings por defecto"""
        return {
            'google_ads': {
                'default_customer_id': None,
                'login_customer_id': None,
                'auto_select_account': False
            },
            'ai_generation': {
                'default_provider': 'openai',
                'default_tone': 'profesional',
                'num_headlines': 10,
                'num_descriptions': 3,
                'auto_validate': True,
                'auto_score': True
            },
            'exports': {
                'default_format': 'csv',
                'include_metadata': True
            },
            'created_at': datetime.utcnow().isoformat()
        }
    
    # ========================================================================
    # FAVORITOS
    # ========================================================================
    
    def get_favorites(self) -> Dict[str, List]:
        """Obtiene favoritos del usuario"""
        try:
            if self.files['favorites'].exists():
                with open(self.files['favorites'], 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {'campaigns': [], 'keywords': [], 'ads': []}
        
        except Exception as e:
            logger.error(f"Error cargando favoritos: {e}")
            return {'campaigns': [], 'keywords': [], 'ads': []}
    
    def add_favorite(self, category: str, item: Dict[str, Any]) -> bool:
        """Agrega un item a favoritos"""
        try:
            favorites = self.get_favorites()
            
            if category not in favorites:
                favorites[category] = []
            
            # Evitar duplicados
            item_id = item.get('id')
            if item_id and not any(f.get('id') == item_id for f in favorites[category]):
                favorites[category].append({
                    **item,
                    'added_at': datetime.utcnow().isoformat()
                })
                
                with open(self.files['favorites'], 'w', encoding='utf-8') as f:
                    json.dump(favorites, f, indent=2, ensure_ascii=False)
                
                return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error agregando favorito: {e}")
            return False
    
    # ========================================================================
    # HISTORIAL
    # ========================================================================
    
    def add_to_history(self, action: str, data: Dict[str, Any]) -> bool:
        """Agrega una acción al historial"""
        try:
            history = self._load_json(self.files['history'], [])
            
            history.append({
                'action': action,
                'data': data,
                'timestamp': datetime.utcnow().isoformat(),
                'user': self.user_id
            })
            
            # Mantener solo últimos 1000 registros
            history = history[-1000:]
            
            with open(self.files['history'], 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            
            return True
        
        except Exception as e:
            logger.error(f"Error guardando en historial: {e}")
            return False
    
    def get_history(self, limit: int = 100) -> List[Dict]:
        """Obtiene historial de acciones"""
        try:
            history = self._load_json(self.files['history'], [])
            return history[-limit:]
        
        except Exception as e:
            logger.error(f"Error cargando historial: {e}")
            return []
    
    def save_ad_history(self, ad_data: Dict[str, Any]) -> bool:
        """
        Guarda un anuncio en el historial para uso en campañas
        
        Args:
            ad_data: Datos del anuncio a guardar
            
        Returns:
            bool: True si se guardó exitosamente
        """
        try:
            # Cargar historial existente
            history = self._load_json(self.files['history'], [])
            
            # Agregar nuevo anuncio con timestamp
            ad_entry = {
                'type': 'ad_saved',
                'timestamp': datetime.utcnow().isoformat(),
                'ad_data': ad_data
            }
            
            history.append(ad_entry)
            
            # Mantener solo los últimos 1000 registros
            if len(history) > 1000:
                history = history[-1000:]
            
            # Guardar historial actualizado
            with open(self.files['history'], 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Anuncio guardado en historial: {ad_data.get('id', 'sin_id')}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando anuncio en historial: {e}")
            return False
    
    def save_autopilot_blueprint(self, blueprint_data: Dict[str, Any]) -> bool:
        """
        Guarda un blueprint de AUTOPILOT 2050
        
        Args:
            blueprint_data: Datos del blueprint a guardar
            
        Returns:
            bool: True si se guardó exitosamente
        """
        try:
            # Crear archivo de blueprints si no existe
            blueprints_file = self.base_path / 'autopilot_blueprints.json'
            
            # Cargar blueprints existentes
            blueprints = self._load_json(blueprints_file, [])
            
            # Agregar nuevo blueprint con timestamp y ID único
            import uuid
            blueprint_entry = {
                **blueprint_data,
                'saved_at': datetime.utcnow().isoformat(),
                'id': str(uuid.uuid4())
            }
            
            blueprints.append(blueprint_entry)
            
            # Mantener solo los últimos 50 blueprints
            if len(blueprints) > 50:
                blueprints = blueprints[-50:]
            
            # Guardar blueprints actualizados
            with open(blueprints_file, 'w', encoding='utf-8') as f:
                json.dump(blueprints, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Blueprint de AUTOPILOT guardado: {blueprint_entry['id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error guardando blueprint de AUTOPILOT: {e}")
            return False
    
    def get_autopilot_blueprints(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los blueprints de AUTOPILOT 2050
        
        Returns:
            List[Dict]: Lista de blueprints guardados
        """
        try:
            blueprints_file = self.base_path / 'autopilot_blueprints.json'
            return self._load_json(blueprints_file, [])
            
        except Exception as e:
            logger.error(f"Error cargando blueprints de AUTOPILOT: {e}")
            return []

    # ========================================================================
    # UTILIDADES
    # ========================================================================
    
    def _load_json(self, file_path: Path, default: Any) -> Any:
        """Carga un archivo JSON con fallback"""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return default
        except:
            return default
    
    def clear_cache(self):
        """Limpia la cache en memoria"""
        self._cache = {}
        logger.info("🧹 Cache de UserStorage limpiada")
    
    def export_all_data(self) -> Dict[str, Any]:
        """Exporta todos los datos del usuario"""
        return {
            'user_id': self.user_id,
            'exported_at': datetime.utcnow().isoformat(),
            'preferences': self.get_preferences(),
            'settings': self.get_settings(),
            'favorites': self.get_favorites(),
            'history': self.get_history(limit=500),
            # API keys NO se exportan por seguridad
        }
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Obtiene información del storage"""
        total_size = sum(
            f.stat().st_size if f.exists() else 0
            for f in self.files.values()
        )
        
        return {
            'user_id': self.user_id,
            'base_path': str(self.base_path),
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'files': {
                name: {
                    'exists': path.exists(),
                    'size_bytes': path.stat().st_size if path.exists() else 0
                }
                for name, path in self.files.items()
            }
        }


# ============================================================================
# INSTANCIA GLOBAL
# ============================================================================

_user_storage = None

def get_user_storage(user_id: str = "saltbalente") -> UserStorage:
    """Obtiene instancia global de UserStorage"""
    global _user_storage
    if _user_storage is None or _user_storage.user_id != user_id:
        _user_storage = UserStorage(user_id)
    return _user_storage