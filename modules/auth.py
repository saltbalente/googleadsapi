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
        
        # Configuración de OAuth según el entorno
        if self._is_streamlit_cloud():
            # En Streamlit Cloud no podemos usar servidor local
            self.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
            self.oauth_server = None
        else:
            # En local, usar el servidor OAuth
            try:
                from .oauth_server import OAuthCallbackServer
                self.oauth_server = OAuthCallbackServer(port=8080)
                self.redirect_uri = self.oauth_server.get_redirect_uri()
            except:
                # Si falla, usar método manual
                self.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
                self.oauth_server = None
    
    def _is_streamlit_cloud(self) -> bool:
        """Detecta si estamos en Streamlit Cloud"""
        return (
            os.environ.get("STREAMLIT_RUNTIME_ENV") == "cloud" or
            "streamlit.app" in os.environ.get("STREAMLIT_APP_URL", "") or
            os.path.exists("/mount/src") or
            "google_oauth" in st.secrets or
            "google_ads" in st.secrets
        )
    
    def _setup_from_secrets(self):
        """Configura archivos de credenciales desde Streamlit Secrets"""
        if not self._is_streamlit_cloud():
            return
        
        try:
            # Crear directorio config si no existe
            config_dir = Path("config")
            config_dir.mkdir(exist_ok=True)
            
            # Crear client_secret.json desde secrets
            if "google_oauth" in st.secrets:
                logger.info("📝 Configurando client_secret.json desde Streamlit Secrets")
                
                client_config = {
                    st.secrets["google_oauth"]["type"]: {
                        "client_id": st.secrets["google_oauth"]["client_id"],
                        "project_id": st.secrets["google_oauth"]["project_id"],
                        "auth_uri": st.secrets["google_oauth"]["auth_uri"],
                        "token_uri": st.secrets["google_oauth"]["token_uri"],
                        "auth_provider_x509_cert_url": st.secrets["google_oauth"]["auth_provider_x509_cert_url"],
                        "client_secret": st.secrets["google_oauth"]["client_secret"],
                        "redirect_uris": st.secrets["google_oauth"]["redirect_uris"]
                    }
                }
                
                # Guardar temporalmente
                client_secret_path = config_dir / "client_secret.json"
                with open(client_secret_path, "w") as f:
                    json.dump(client_config, f, indent=2)
                
                logger.info("✅ client_secret.json creado desde secrets")
            
            # Crear google-ads.yaml desde secrets
            if "google_ads" in st.secrets:
                logger.info("📝 Configurando google-ads.yaml desde Streamlit Secrets")
                
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
            if "GOOGLE_ADS_DEVELOPER_TOKEN" in st.secrets:
                os.environ['GOOGLE_ADS_DEVELOPER_TOKEN'] = st.secrets["GOOGLE_ADS_DEVELOPER_TOKEN"]
            if "GOOGLE_ADS_CLIENT_ID" in st.secrets:
                os.environ['GOOGLE_ADS_CLIENT_ID'] = st.secrets["GOOGLE_ADS_CLIENT_ID"]
            if "GOOGLE_ADS_CLIENT_SECRET" in st.secrets:
                os.environ['GOOGLE_ADS_CLIENT_SECRET'] = st.secrets["GOOGLE_ADS_CLIENT_SECRET"]
            if "GOOGLE_ADS_LOGIN_CUSTOMER_ID" in st.secrets:
                os.environ['GOOGLE_ADS_LOGIN_CUSTOMER_ID'] = st.secrets["GOOGLE_ADS_LOGIN_CUSTOMER_ID"]
            if "OPENAI_API_KEY" in st.secrets:
                os.environ['OPENAI_API_KEY'] = st.secrets["OPENAI_API_KEY"]
            if "GEMINI_API_KEY" in st.secrets:
                os.environ['GEMINI_API_KEY'] = st.secrets["GEMINI_API_KEY"]
                
            logger.info("✅ Variables de entorno configuradas desde secrets")
                
        except Exception as e:
            logger.error(f"❌ Error configurando desde secrets: {e}")
    
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
            # Asegurarse de que el archivo existe (crearlo desde secrets si es necesario)
            if not os.path.exists(self.client_secrets_file):
                self._setup_from_secrets()
                
                if not os.path.exists(self.client_secrets_file):
                    raise FileNotFoundError(f"Archivo client_secret.json no encontrado: {self.client_secrets_file}")
            
            # Iniciar servidor solo si estamos en local
            if self.oauth_server and not self._is_streamlit_cloud():
                server_started = self.oauth_server.start()
                if not server_started:
                    logger.warning("No se pudo iniciar servidor OAuth, usando método manual")
                    self.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
                else:
                    self.redirect_uri = self.oauth_server.get_redirect_uri()
            
            # Crear flow OAuth
            flow = Flow.from_client_secrets_file(
                self.client_secrets_file,
                scopes=self.scopes
            )
            flow.redirect_uri = self.redirect_uri
            
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'  # Force consent screen to ensure refresh token
            )
            
            # Store flow in session for later use
            st.session_state.oauth_flow = flow
            if self.oauth_server:
                st.session_state.oauth_server = self.oauth_server
            
            # Información adicional para Streamlit Cloud
            if self._is_streamlit_cloud():
                st.info("📱 Estás en Streamlit Cloud. Después de autorizar, copia el código que aparece y pégalo aquí.")
            elif self.oauth_server and self.oauth_server.port != 8080:
                st.info(f"ℹ️ Servidor OAuth iniciado en puerto: {self.oauth_server.port}")
            
            return auth_url
            
        except FileNotFoundError as e:
            logger.error(f"Client secrets file not found: {e}")
            st.error(f"""
            ❌ **Archivo de configuración no encontrado**
            
            En Streamlit Cloud, asegúrate de configurar los secrets correctamente.
            Ve a Settings → Secrets y agrega la configuración.
            """)
            return ""
        except Exception as e:
            logger.error(f"Error generating auth URL: {e}")
            st.error(f"❌ Error al generar URL de autenticación:\n{str(e)}")
            return ""
    
    def handle_callback(self, authorization_code: str = None) -> bool:
        """Handle OAuth callback and store credentials"""
        try:
            # En Streamlit Cloud, siempre usar código manual
            if self._is_streamlit_cloud() and not authorization_code:
                st.error("❌ Por favor, pega el código de autorización")
                return False
            
            # Si se proporciona código manualmente, usarlo directamente
            if authorization_code:
                logger.info("Usando código de autorización proporcionado manualmente")
            else:
                # Intentar obtener el código del servidor OAuth (solo local)
                oauth_server = st.session_state.get('oauth_server')
                if oauth_server and oauth_server.server:
                    if hasattr(oauth_server.server, 'auth_received') and oauth_server.server.auth_received:
                        if hasattr(oauth_server.server, 'auth_code') and oauth_server.server.auth_code:
                            authorization_code = oauth_server.server.auth_code
                            logger.info("Código de autorización obtenido del servidor OAuth")
                        elif hasattr(oauth_server.server, 'auth_error') and oauth_server.server.auth_error:
                            st.error(f"❌ Error en autenticación: {oauth_server.server.auth_error}")
                            return False
                
                if not authorization_code:
                    logger.warning("No se encontró código de autorización")
                    st.error("❌ No se recibió código de autorización. Por favor, intenta el proceso nuevamente.")
                    return False
            
            # Obtener o crear el flow OAuth
            flow = st.session_state.get('oauth_flow')
            if not flow:
                # Si no hay flow en session, intentar crear uno nuevo
                if not os.path.exists(self.client_secrets_file):
                    self._setup_from_secrets()
                    
                    if not os.path.exists(self.client_secrets_file):
                        st.error("❌ Archivo client_secret.json no encontrado")
                        return False
                
                flow = Flow.from_client_secrets_file(
                    self.client_secrets_file,
                    scopes=self.scopes
                )
                flow.redirect_uri = self.redirect_uri
                logger.info("Flow OAuth creado desde archivo de configuración")
            
            # Handle both authorization code and full URL
            if authorization_code and authorization_code.startswith('http'):
                # Extract code from URL if user pasted the full redirect URL
                from urllib.parse import urlparse, parse_qs
                parsed_url = urlparse(authorization_code)
                query_params = parse_qs(parsed_url.query)
                if 'code' in query_params:
                    authorization_code = query_params['code'][0]
                else:
                    st.error("No se encontró el código de autorización en la URL proporcionada.")
                    return False
            
            # Handle code from "urn:ietf:wg:oauth:2.0:oob" flow (copy-paste method)
            authorization_code = authorization_code.strip()
            
            if not authorization_code:
                st.error("No se recibió código de autorización.")
                return False
            
            flow.fetch_token(code=authorization_code)
            
            credentials = flow.credentials
            st.session_state.credentials = credentials
            
            # Save credentials
            self._save_credentials_to_file(credentials)
            
            # Update Streamlit Secrets if possible
            if self._is_streamlit_cloud() and credentials.refresh_token:
                st.info(f"""
                ✅ **Token obtenido exitosamente!**
                
                Para hacer permanente la autenticación, agrega este refresh_token a tus Streamlit Secrets:
                
                ```toml
                [google_ads]
                refresh_token = "{credentials.refresh_token}"
                ```
                """)
            
            # Limpiar servidor de session state
            if 'oauth_server' in st.session_state:
                del st.session_state['oauth_server']
            
            # Success message
            if credentials.refresh_token:
                st.success("¡Autenticación exitosa! Token de actualización obtenido.")
                logger.info("OAuth authentication completed successfully")
            else:
                st.warning("Autenticación exitosa, pero no se obtuvo token de actualización.")
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling OAuth callback: {e}")
            st.error(f"Error en la autenticación: {str(e)}")
            st.info("Asegúrate de que el código de autorización sea correcto y no haya expirado.")
            return False
    
    def logout(self):
        """Clear authentication data"""
        if 'credentials' in st.session_state:
            del st.session_state.credentials
        if 'oauth_flow' in st.session_state:
            del st.session_state.oauth_flow
        st.success("Sesión cerrada exitosamente")
    
    def _save_credentials_to_file(self, credentials: Credentials):
        """Save credentials to oauth_credentials.json file and update google-ads.yaml"""
        try:
            # Ensure config directory exists
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
                
            logger.info("Credentials saved to oauth_credentials.json")
            
            # Also update google-ads.yaml with the refresh token
            google_ads_yaml = 'config/google-ads.yaml'
            if os.path.exists(google_ads_yaml):
                try:
                    with open(google_ads_yaml, 'r') as f:
                        config = yaml.safe_load(f) or {}
                    
                    # Update credentials in the config
                    config['refresh_token'] = credentials.refresh_token
                    config['client_id'] = credentials.client_id
                    config['client_secret'] = credentials.client_secret
                    
                    with open(google_ads_yaml, 'w') as f:
                        yaml.dump(config, f, default_flow_style=False)
                    
                    logger.info("Google Ads YAML config updated with new credentials")
                except Exception as e:
                    logger.warning(f"Could not update google-ads.yaml: {e}")
            
        except Exception as e:
            logger.error(f"Error saving credentials to file: {e}")

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


# Función helper para obtener API keys desde secrets
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