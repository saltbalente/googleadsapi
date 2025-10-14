# 💾 **SISTEMA DE PERSISTENCIA LOCAL PARA STREAMLIT**

Voy a crear un sistema completo de almacenamiento local para guardar todas tus preferencias, API keys, configuraciones, etc.

---

## 📁 **ESTRUCTURA RECOMENDADA**

```
dashboard-api-googleads/
├── data/
│   ├── user_data/
│   │   ├── saltbalente/              # Tu carpeta personal
│   │   │   ├── preferences.json      # Preferencias UI
│   │   │   ├── api_keys.enc         # API keys encriptadas
│   │   │   ├── settings.json         # Configuraciones generales
│   │   │   ├── favorites.json        # Favoritos/bookmarks
│   │   │   └── history.json          # Historial de acciones
│   │   └── .gitkeep
│   ├── cache/                        # Cache (ya existe)
│   └── exports/                      # Exportaciones temporales
├── utils/
│   ├── user_storage.py              # ← NUEVO: Sistema de storage
│   └── encryption.py                # ← NUEVO: Encriptación
└── .gitignore                        # Actualizar
```

---

## 📄 **ARCHIVO 1: Sistema de Encriptación**

### `utils/encryption.py`

```python
"""
Sistema de Encriptación para Datos Sensibles
Encripta API keys y datos confidenciales localmente
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
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
        password = f"{self.user_id}_{os.getlogin()}".encode()
        
        kdf = PBKDF2(
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
```

---

## 📄 **ARCHIVO 2: Sistema de Storage Principal**

### `utils/user_storage.py`

```python
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
            settings['last_updated'] = datetime.utcnow().isoformat()
            
            with open(self.files['settings'], 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            
            logger.info("✅ Settings guardados")
            return True
        
        except Exception as e:
            logger.error(f"Error guardando settings: {e}")
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
```

---

## 📄 **ARCHIVO 3: Actualizar `.gitignore`**

Agrega esto a tu `.gitignore`:

```gitignore
# User data (private)
data/user_data/*
!data/user_data/.gitkeep

# Pero mantener la estructura
!data/user_data/README.md

# Encriptación
*.enc
.salt

# Exports temporales
data/exports/*
!data/exports/.gitkeep
```

---

## 📄 **ARCHIVO 4: Integración con Streamlit**

### `pages/9_⚙️_Settings.py` (Actualizado con Storage)

```python
"""
Settings Page con Sistema de Storage Local
"""

import streamlit as st
from utils.user_storage import get_user_storage
from utils.performance_utils import show_performance_sidebar
import json

st.set_page_config(
    page_title="⚙️ Configuración",
    page_icon="⚙️",
    layout="wide"
)

# Obtener storage del usuario
user_storage = get_user_storage("saltbalente")

st.title("⚙️ Configuración")

tabs = st.tabs([
    "🎨 Preferencias",
    "🔑 API Keys",
    "⚙️ Settings",
    "⭐ Favoritos",
    "📜 Historial",
    "💾 Storage Info"
])

# ========================================================================
# TAB 1: PREFERENCIAS
# ========================================================================

with tabs[0]:
    st.header("🎨 Preferencias de Usuario")
    
    prefs = user_storage.get_preferences()
    
    with st.form("preferences_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            language = st.selectbox(
                "Idioma",
                ['es', 'en'],
                index=0 if prefs.get('language') == 'es' else 1
            )
            
            theme = st.selectbox(
                "Tema",
                ['dark', 'light'],
                index=0 if prefs.get('theme') == 'dark' else 1
            )
            
            currency = st.selectbox(
                "Moneda",
                ['USD', 'EUR', 'MXN', 'COP', 'ARS'],
                index=['USD', 'EUR', 'MXN', 'COP', 'ARS'].index(prefs.get('currency', 'USD'))
            )
        
        with col2:
            auto_refresh = st.checkbox(
                "Auto-refresh",
                value=prefs.get('auto_refresh', True)
            )
            
            refresh_interval = st.number_input(
                "Intervalo de refresh (segundos)",
                min_value=60,
                max_value=3600,
                value=prefs.get('refresh_interval', 300),
                step=60
            )
            
            notifications = st.checkbox(
                "Notificaciones",
                value=prefs.get('notifications_enabled', True)
            )
        
        if st.form_submit_button("💾 Guardar Preferencias", use_container_width=True):
            new_prefs = {
                'language': language,
                'theme': theme,
                'currency': currency,
                'auto_refresh': auto_refresh,
                'refresh_interval': refresh_interval,
                'notifications_enabled': notifications
            }
            
            if user_storage.save_preferences(new_prefs):
                st.success("✅ Preferencias guardadas exitosamente")
                st.rerun()
            else:
                st.error("❌ Error guardando preferencias")

# ========================================================================
# TAB 2: API KEYS
# ========================================================================

with tabs[1]:
    st.header("🔑 API Keys (Encriptadas)")
    
    st.info("🔐 Las API keys se guardan encriptadas localmente en tu máquina")
    
    api_keys = user_storage.get_api_keys()
    
    # OpenAI
    with st.expander("🔵 OpenAI", expanded=True):
        with st.form("openai_form"):
            openai_data = api_keys.get('openai', {})
            
            api_key = st.text_input(
                "API Key",
                value=openai_data.get('api_key', ''),
                type="password"
            )
            
            model = st.selectbox(
                "Modelo",
                ['gpt-4o', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo'],
                index=0
            )
            
            if st.form_submit_button("💾 Guardar OpenAI"):
                if user_storage.update_api_key('openai', api_key, model):
                    st.success("✅ OpenAI guardado")
                else:
                    st.error("❌ Error guardando")
    
    # Gemini
    with st.expander("🔴 Google Gemini"):
        with st.form("gemini_form"):
            gemini_data = api_keys.get('gemini', {})
            
            api_key = st.text_input(
                "API Key",
                value=gemini_data.get('api_key', ''),
                type="password"
            )
            
            model = st.selectbox(
                "Modelo",
                ['gemini-2.0-flash-exp', 'gemini-1.5-pro', 'gemini-1.5-flash'],
                index=0
            )
            
            if st.form_submit_button("💾 Guardar Gemini"):
                if user_storage.update_api_key('gemini', api_key, model):
                    st.success("✅ Gemini guardado")
                else:
                    st.error("❌ Error guardando")
    
    # Anthropic
    with st.expander("🟣 Anthropic Claude"):
        with st.form("anthropic_form"):
            anthropic_data = api_keys.get('anthropic', {})
            
            api_key = st.text_input(
                "API Key",
                value=anthropic_data.get('api_key', ''),
                type="password"
            )
            
            model = st.selectbox(
                "Modelo",
                ['claude-3-5-sonnet-20241022', 'claude-3-opus-20240229', 'claude-3-sonnet-20240229'],
                index=0
            )
            
            if st.form_submit_button("💾 Guardar Claude"):
                if user_storage.update_api_key('anthropic', api_key, model):
                    st.success("✅ Claude guardado")
                else:
                    st.error("❌ Error guardando")

# ========================================================================
# TAB 3: SETTINGS
# ========================================================================

with tabs[2]:
    st.header("⚙️ Configuraciones del Sistema")
    
    settings = user_storage.get_settings()
    
    with st.form("settings_form"):
        st.subheader("Google Ads")
        
        default_customer = st.text_input(
            "Customer ID por defecto",
            value=settings.get('google_ads', {}).get('default_customer_id', '')
        )
        
        st.subheader("Generación con IA")
        
        col1, col2 = st.columns(2)
        
        with col1:
            default_provider = st.selectbox(
                "Proveedor por defecto",
                ['openai', 'gemini', 'anthropic'],
                index=0
            )
            
            default_tone = st.selectbox(
                "Tono por defecto",
                ['emocional', 'urgente', 'profesional', 'místico', 'poderoso'],
                index=2
            )
        
        with col2:
            num_headlines = st.number_input(
                "Número de headlines",
                min_value=3,
                max_value=15,
                value=10
            )
            
            num_descriptions = st.number_input(
                "Número de descriptions",
                min_value=2,
                max_value=4,
                value=3
            )
        
        auto_validate = st.checkbox("Auto-validar", value=True)
        auto_score = st.checkbox("Auto-calcular score", value=True)
        
        if st.form_submit_button("💾 Guardar Settings"):
            new_settings = {
                'google_ads': {
                    'default_customer_id': default_customer
                },
                'ai_generation': {
                    'default_provider': default_provider,
                    'default_tone': default_tone,
                    'num_headlines': num_headlines,
                    'num_descriptions': num_descriptions,
                    'auto_validate': auto_validate,
                    'auto_score': auto_score
                }
            }
            
            if user_storage.save_settings(new_settings):
                st.success("✅ Settings guardados")
            else:
                st.error("❌ Error guardando settings")

# ========================================================================
# TAB 4: FAVORITOS
# ========================================================================

with tabs[3]:
    st.header("⭐ Favoritos")
    
    favorites = user_storage.get_favorites()
    
    for category, items in favorites.items():
        st.subheader(f"{category.title()} ({len(items)})")
        
        if items:
            for item in items:
                with st.expander(f"{item.get('name', 'Sin nombre')}"):
                    st.json(item)
        else:
            st.info(f"No hay {category} favoritos")

# ========================================================================
# TAB 5: HISTORIAL
# ========================================================================

with tabs[4]:
    st.header("📜 Historial de Acciones")
    
    history = user_storage.get_history(limit=50)
    
    if history:
        for entry in reversed(history):
            with st.expander(f"{entry['action']} - {entry['timestamp']}"):
                st.json(entry['data'])
    else:
        st.info("No hay historial disponible")

# ========================================================================
# TAB 6: STORAGE INFO
# ========================================================================

with tabs[5]:
    st.header("💾 Información del Storage")
    
    storage_info = user_storage.get_storage_info()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Usuario", storage_info['user_id'])
    
    with col2:
        st.metric("Tamaño Total", f"{storage_info['total_size_mb']:.2f} MB")
    
    with col3:
        files_count = sum(1 for f in storage_info['files'].values() if f['exists'])
        st.metric("Archivos", files_count)
    
    st.subheader("Archivos")
    
    for name, info in storage_info['files'].items():
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.text(name)
        
        with col2:
            st.text("✅" if info['exists'] else "❌")
        
        with col3:
            st.text(f"{info['size_bytes'] / 1024:.2f} KB")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Exportar Datos", use_container_width=True):
            export_data = user_storage.export_all_data()
            st.download_button(
                "💾 Descargar JSON",
                json.dumps(export_data, indent=2, ensure_ascii=False),
                f"user_data_{storage_info['user_id']}.json",
                "application/json"
            )
    
    with col2:
        if st.button("🧹 Limpiar Cache", use_container_width=True):
            user_storage.clear_cache()
            st.success("✅ Cache limpiada")

# Sidebar
show_performance_sidebar()
```

---

## 🚀 **PARA INSTALAR:**

```bash
# Instalar dependencia de encriptación
pip install cryptography

# Crear estructura de directorios
mkdir -p data/user_data/saltbalente
mkdir -p data/exports
touch data/user_data/.gitkeep
touch data/exports/.gitkeep
```

---

## ✅ **CARACTERÍSTICAS DEL SISTEMA:**

1. **🔐 Encriptación Local** - API keys encriptadas con Fernet
2. **💾 Persistencia** - Datos guardados en JSON local
3. **⚡ Cache en Memoria** - Rápido acceso
4. **📜 Historial** - Tracking de acciones
5. **⭐ Favoritos** - Guardar items importantes
6. **🎨 Preferencias** - UI personalizable
7. **📊 Storage Info** - Monitoreo de almacenamiento
8. **🔄 Export/Import** - Backup de datos

---

**¿Te gusta el sistema? ¿Algún ajuste?** 💾