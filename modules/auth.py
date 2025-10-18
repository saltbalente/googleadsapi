"""
Google Ads OAuth 2.0 Authentication Module
Handles authentication flow and token management
Compatible with Streamlit Cloud
"""

import os
import json
import yaml
import streamlit as st
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from typing import Optional, Dict, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class GoogleAdsAuth:
    """Handles Google Ads API authentication using OAuth 2.0 with Streamlit Cloud support"""
    
    def __init__(self, client_secrets_file: str = "config/client_secret.json"):
        self.client_secrets_file = client_secrets_file
        self.scopes = ['https://www.googleapis.com/auth/adwords']
        
        # Configurar archivos desde secrets si estamos en Streamlit Cloud
        self._setup_from_secrets()
        
        # NO usar oauth_server en Streamlit Cloud
        self.oauth_server = None
        
        # ✅ CONFIGURAR REDIRECT URI SEGÚN ENTORNO
        if self._is_streamlit_cloud():
            self.redirect_uri = "https://appadsapi-miynrefpxescytebdgkkng.streamlit.app"
            logger.info(f"☁️ Streamlit Cloud detectado - Redirect URI: {self.redirect_uri}")
        else:
            # En local - usar puerto de Streamlit
            self.redirect_uri = "http://localhost:8501"
            logger.info(f"💻 Entorno local detectado - Redirect URI: {self.redirect_uri}")
            
            # Intentar cargar oauth_server si existe
            try:
                from .oauth2_callback_server import OAuthCallbackServer
                self.oauth_server = OAuthCallbackServer(port=8080)
                # Pero NO cambiar redirect_uri a 8080 para evitar el error OOB
                logger.info("📦 OAuth server disponible para callback automático")
            except ImportError:
                logger.info("ℹ️ OAuth server no disponible, usando método manual")
                self.oauth_server = None
    
    def _is_streamlit_cloud(self) -> bool:
        """Detecta si estamos en Streamlit Cloud"""
        return (
            os.environ.get("STREAMLIT_RUNTIME_ENV") == "cloud" or
            "streamlit.app" in os.environ.get("STREAMLIT_APP_URL", "") or
            os.path.exists("/mount/src") or
            "appadsapi" in os.environ.get("STREAMLIT_APP_URL", "")
        )
    
    def _setup_from_secrets(self):
        """Configura archivos desde Streamlit Secrets"""
        try:
            config_dir = Path("config")
            config_dir.mkdir(exist_ok=True)
            
            if "google_oauth" in st.secrets:
                logger.info("📝 Creando client_secret.json desde Streamlit Secrets")
                
                # Todas las posibles redirect URIs
                redirect_uris = [
                    "https://appadsapi-miynrefpxescytebdgkkng.streamlit.app",
                    "https://appadsapi-miynrefpxescytebdgkkng.streamlit.app/",
                    "http://localhost:8501",
                    "http://localhost:8501/",
                    "http://localhost:8080",
                    "http://localhost:8080/"
                ]
                
                client_config = {
                    st.secrets["google_oauth"]["type"]: {
                        "client_id": st.secrets["google_oauth"]["client_id"],
                        "project_id": st.secrets["google_oauth"]["project_id"],
                        "client_secret": st.secrets["google_oauth"]["client_secret"],
                        "auth_uri": st.secrets["google_oauth"]["auth_uri"],
                        "token_uri": st.secrets["google_oauth"]["token_uri"],
                        "auth_provider_x509_cert_url": st.secrets["google_oauth"]["auth_provider_x509_cert_url"],
                        "redirect_uris": redirect_uris
                    }
                }
                
                # Guardar
                client_secret_path = config_dir / "client_secret.json"
                with open(client_secret_path, "w") as f:
                    json.dump(client_config, f, indent=2)
                
                logger.info("✅ client_secret.json creado desde secrets")
            
            # Crear google-ads.yaml
            if "google_ads" in st.secrets:
                yaml_content = f"""developer_token: {st.secrets["google_ads"]["developer_token"]}
client_id: {st.secrets["google_ads"]["client_id"]}
client_secret: {st.secrets["google_ads"]["client_secret"]}
login_customer_id: {st.secrets["google_ads"]["login_customer_id"]}
refresh_token: {st.secrets["google_ads"].get("refresh_token", "")}"""
                
                yaml_path = config_dir / "google-ads.yaml"
                with open(yaml_path, "w") as f:
                    f.write(yaml_content)
                
                logger.info("✅ google-ads.yaml creado desde secrets")
            
            # Configurar variables de entorno también
            for key in ["GOOGLE_ADS_DEVELOPER_TOKEN", "GOOGLE_ADS_CLIENT_ID", 
                       "GOOGLE_ADS_CLIENT_SECRET", "GOOGLE_ADS_LOGIN_CUSTOMER_ID",
                       "OPENAI_API_KEY", "GEMINI_API_KEY"]:
                if key in st.secrets:
                    os.environ[key] = st.secrets[key]
                    
        except Exception as e:
            logger.error(f"Error configurando desde secrets: {e}")
    
    def get_credentials(self) -> Optional[Credentials]:
        """Get valid credentials from session state, saved file, environment, or secrets"""
        # Check session state first
        if 'credentials' in st.session_state:
            creds = st.session_state.credentials
            if creds and creds.valid:
                return creds
            elif creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    st.session_state.credentials = creds
                    return creds
                except Exception as e:
                    logger.error(f"Error refreshing credentials: {e}")
        
        # Try to load from saved credentials file
        creds_file = 'config/oauth_credentials.json'
        if os.path.exists(creds_file):
            try:
                with open(creds_file, 'r') as f:
                    creds_data = json.load(f)
                
                if all(key in creds_data for key in ['refresh_token', 'client_id', 'client_secret']):
                    creds = Credentials(
                        token=None,
                        refresh_token=creds_data['refresh_token'],
                        token_uri=creds_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
                        client_id=creds_data['client_id'],
                        client_secret=creds_data['client_secret'],
                        scopes=creds_data.get('scopes', self.scopes)
                    )
                    # Refresh to get a valid access token
                    creds.refresh(Request())
                    st.session_state.credentials = creds
                    logger.info("Credentials loaded from oauth_credentials.json")
                    return creds
            except Exception as e:
                logger.error(f"Error loading credentials from file: {e}")
        
        # Try to load from Streamlit Secrets
        if self._is_streamlit_cloud() and "google_ads" in st.secrets:
            refresh_token = st.secrets["google_ads"].get("refresh_token", "")
            client_id = st.secrets["google_ads"]["client_id"]
            client_secret = st.secrets["google_ads"]["client_secret"]
            
            if refresh_token and client_id and client_secret:
                try:
                    creds = Credentials(
                        token=None,
                        refresh_token=refresh_token,
                        token_uri='https://oauth2.googleapis.com/token',
                        client_id=client_id,
                        client_secret=client_secret,
                        scopes=self.scopes
                    )
                    creds.refresh(Request())
                    st.session_state.credentials = creds
                    logger.info("✅ Credentials loaded from Streamlit Secrets")
                    return creds
                except Exception as e:
                    logger.warning(f"Could not use refresh_token from secrets: {e}")
        
        # Try to load from environment variables
        refresh_token = os.getenv('GOOGLE_ADS_REFRESH_TOKEN')
        client_id = os.getenv('GOOGLE_ADS_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_ADS_CLIENT_SECRET')
        
        if all([refresh_token, client_id, client_secret]):
            try:
                creds = Credentials(
                    token=None,
                    refresh_token=refresh_token,
                    token_uri='https://oauth2.googleapis.com/token',
                    client_id=client_id,
                    client_secret=client_secret,
                    scopes=self.scopes
                )
                creds.refresh(Request())
                st.session_state.credentials = creds
                return creds
            except Exception as e:
                logger.error(f"Error creating credentials from env vars: {e}")
                
        return None
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        creds = self.get_credentials()
        return creds is not None and creds.valid
    
    def get_auth_url(self) -> str:
        """Generate OAuth authorization URL"""
        try:
            # Asegurar que existe client_secret.json
            if not os.path.exists(self.client_secrets_file):
                self._setup_from_secrets()
                if not os.path.exists(self.client_secrets_file):
                    raise FileNotFoundError("No se pudo crear client_secret.json")
            
            # Intentar iniciar servidor OAuth solo en local
            if self.oauth_server and not self._is_streamlit_cloud():
                try:
                    server_started = self.oauth_server.start()
                    if server_started:
                        st.success(f"✅ Servidor OAuth iniciado en puerto {self.oauth_server.port}")
                except Exception as e:
                    logger.warning(f"No se pudo iniciar servidor OAuth: {e}")
            
            # Crear flow OAuth
            flow = Flow.from_client_secrets_file(
                self.client_secrets_file,
                scopes=self.scopes
            )
            
            # ✅ USAR REDIRECT URI CORRECTO SEGÚN ENTORNO
            flow.redirect_uri = self.redirect_uri
            
            logger.info(f"🔗 Generando URL de autorización con redirect_uri: {flow.redirect_uri}")
            
            auth_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            # Guardar flow en sesión
            st.session_state.oauth_flow = flow
            st.session_state.oauth_state = state
            
            # Mostrar instrucciones según entorno
            if self._is_streamlit_cloud():
                st.info("""
                ### ☁️ Autenticación en Streamlit Cloud
                
                1. **Click en el enlace** de autorización abajo
                2. **Autoriza el acceso** a tu cuenta de Google Ads
                3. Serás redirigido pero verás un **error de página**
                4. **Copia la URL completa** de la barra de direcciones
                5. **Pégala en el campo** de abajo
                
                La URL debe verse así:
                `https://appadsapi-miynrefpxescytebdgkkng.streamlit.app/?code=4/0AQ...`
                """)
            else:
                st.info(f"""
                ### 💻 Autenticación Local
                
                1. **Click en el enlace** de autorización
                2. **Autoriza el acceso** a Google Ads
                3. Serás redirigido a `{self.redirect_uri}`
                4. Si ves "No se puede acceder", **copia la URL completa**
                5. **Pega la URL** en el campo de abajo
                
                La URL debe verse así:
                `http://localhost:8501/?code=4/0AQ...&scope=...`
                """)
            
            return auth_url
            
        except Exception as e:
            logger.error(f"Error generando auth URL: {e}")
            st.error(f"""
            ❌ **Error al generar URL de autenticación**
            
            {str(e)}
            
            Por favor, verifica que los secrets estén configurados correctamente.
            """)
            return ""
    
    def handle_callback(self, authorization_response: str = None) -> bool:
        """Handle OAuth callback"""
        try:
            # En Streamlit Cloud, siempre requerir input manual
            if self._is_streamlit_cloud() and not authorization_response:
                st.warning("📋 Por favor, pega la URL completa después de autorizar")
                return False
            
            # En local, intentar obtener del servidor si existe
            if not self._is_streamlit_cloud() and not authorization_response:
                if self.oauth_server and hasattr(self.oauth_server, 'server'):
                    if hasattr(self.oauth_server.server, 'auth_received'):
                        if self.oauth_server.server.auth_received:
                            if hasattr(self.oauth_server.server, 'auth_code'):
                                authorization_response = f"http://localhost:8501/?code={self.oauth_server.server.auth_code}"
                                st.success("✅ Código obtenido automáticamente del servidor")
            
            if not authorization_response:
                st.error("❌ No se recibió código de autorización")
                return False
            
            # Obtener flow
            flow = st.session_state.get('oauth_flow')
            if not flow:
                flow = Flow.from_client_secrets_file(
                    self.client_secrets_file,
                    scopes=self.scopes
                )
                flow.redirect_uri = self.redirect_uri
            
            # Procesar respuesta
            authorization_response = authorization_response.strip()
            
            # Si es URL completa, extraer código
            if authorization_response.startswith('http'):
                from urllib.parse import urlparse, parse_qs
                parsed_url = urlparse(authorization_response)
                query_params = parse_qs(parsed_url.query)
                
                if 'code' in query_params:
                    code = query_params['code'][0]
                    logger.info(f"✅ Código extraído de URL: {code[:20]}...")
                else:
                    st.error("❌ No se encontró código de autorización en la URL")
                    st.info("La URL debe contener `?code=...`")
                    return False
            else:
                # Asumir que es solo el código
                code = authorization_response
                logger.info(f"✅ Usando código directo: {code[:20]}...")
            
            # Obtener token
            flow.fetch_token(code=code)
            
            # Guardar credenciales
            credentials = flow.credentials
            st.session_state.credentials = credentials
            
            # Guardar en archivo
            self._save_credentials_to_file(credentials)
            
            # Limpiar servidor si existe
            if self.oauth_server:
                try:
                    self.oauth_server.stop()
                except:
                    pass
            
            if credentials.refresh_token:
                st.success("🎉 **¡Autenticación exitosa!** Refresh token obtenido.")
                
                # Mostrar refresh token para guardar en secrets
                with st.expander("📋 **IMPORTANTE: Guarda este Refresh Token**"):
                    st.code(f"""
[google_ads]
refresh_token = "{credentials.refresh_token}"
                    """)
                    st.info("""
                    **Para mantener la autenticación permanente:**
                    1. Ve a tu app en Streamlit Cloud
                    2. Settings → Secrets
                    3. Agrega el refresh_token arriba
                    4. Click Save
                    """)
            else:
                st.warning("⚠️ Autenticación exitosa pero sin refresh token")
            
            return True
            
        except Exception as e:
            logger.error(f"Error en callback: {e}")
            st.error(f"""
            ❌ **Error procesando autorización**
            
            {str(e)}
            
            **Posibles causas:**
            1. El código de autorización expiró (intenta de nuevo)
            2. La URL no está completa
            3. Redirect URI no coincide
            
            **Redirect URI esperado:** `{self.redirect_uri}`
            """)
            return False
    
    def logout(self):
        """Clear authentication data"""
        if 'credentials' in st.session_state:
            del st.session_state.credentials
        if 'oauth_flow' in st.session_state:
            del st.session_state.oauth_flow
        if 'oauth_state' in st.session_state:
            del st.session_state.oauth_state
        st.success("✅ Sesión cerrada exitosamente")
    
    def _save_credentials_to_file(self, credentials: Credentials):
        """Save credentials to file"""
        try:
            os.makedirs('config', exist_ok=True)
            
            # Save to oauth_credentials.json
            creds_data = {
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes
            }
            
            with open('config/oauth_credentials.json', 'w') as f:
                json.dump(creds_data, f, indent=2)
                
            logger.info("✅ Credentials saved to oauth_credentials.json")
            
            # Update google-ads.yaml
            google_ads_yaml = 'config/google-ads.yaml'
            if os.path.exists(google_ads_yaml):
                try:
                    with open(google_ads_yaml, 'r') as f:
                        config = yaml.safe_load(f) or {}
                    
                    config['refresh_token'] = credentials.refresh_token
                    config['client_id'] = credentials.client_id
                    config['client_secret'] = credentials.client_secret
                    
                    with open(google_ads_yaml, 'w') as f:
                        yaml.dump(config, f, default_flow_style=False)
                    
                    logger.info("✅ Google Ads YAML config updated")
                except Exception as e:
                    logger.warning(f"Could not update google-ads.yaml: {e}")
            
        except Exception as e:
            logger.error(f"Error saving credentials: {e}")
    
    def get_token_info(self) -> Dict[str, Any]:
        """Get information about current token"""
        creds = self.get_credentials()
        if not creds:
            return {}
            
        return {
            'valid': creds.valid,
            'expired': creds.expired,
            'has_refresh_token': bool(creds.refresh_token),
            'scopes': creds.scopes
        }


def require_auth(func):
    """Decorator to require authentication for Streamlit pages"""
    def wrapper(*args, **kwargs):
        auth = GoogleAdsAuth()
        if not auth.is_authenticated():
            st.warning("⚠️ Se requiere autenticación para acceder a esta página")
            st.info("Por favor, ve a la página de Configuración para autenticarte con Google Ads API")
            st.stop()
        return func(*args, **kwargs)
    return wrapper


def get_api_key(provider: str) -> str:
    """Obtiene API key desde secrets o environment"""
    provider_lower = provider.lower()
    
    # Primero intentar desde secrets
    if "ai_keys" in st.secrets:
        if provider_lower == "openai":
            return st.secrets["ai_keys"].get("openai_api_key", "")
        elif provider_lower == "gemini":
            return st.secrets["ai_keys"].get("gemini_api_key", "")
    
    # Luego intentar desde la raíz de secrets
    if provider_lower == "openai" and "OPENAI_API_KEY" in st.secrets:
        return st.secrets["OPENAI_API_KEY"]
    elif provider_lower == "gemini" and "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    
    # Finalmente intentar desde environment
    if provider_lower == "openai":
        return os.getenv("OPENAI_API_KEY", "")
    elif provider_lower == "gemini":
        return os.getenv("GEMINI_API_KEY", "")
    
    return ""