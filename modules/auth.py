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
            # Asegurarse de que el archivo existe
            if not os.path.exists(self.client_secrets_file):
                self._setup_from_secrets()
                
                if not os.path.exists(self.client_secrets_file):
                    raise FileNotFoundError(f"Archivo client_secret.json no encontrado")
            
            # Crear flow OAuth
            flow = Flow.from_client_secrets_file(
                self.client_secrets_file,
                scopes=self.scopes
            )
            
            # ✅ Usar localhost:8080 para el nuevo client web
            flow.redirect_uri = "http://localhost:8501"  # Puerto de Streamlit
            
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            # Store flow in session
            st.session_state.oauth_flow = flow
            
            return auth_url
            
        except Exception as e:
            logger.error(f"Error generating auth URL: {e}")
            st.error(f"❌ Error: {str(e)}")
            return ""

    def handle_callback(self, authorization_response: str = None) -> bool:
        """Handle OAuth callback con el nuevo client"""
        try:
            if not authorization_response:
                st.error("❌ Por favor, pega la URL completa después de autorizar")
                return False
            
            # Obtener el flow
            flow = st.session_state.get('oauth_flow')
            if not flow:
                flow = Flow.from_client_secrets_file(
                    self.client_secrets_file,
                    scopes=self.scopes
                )
                flow.redirect_uri = "http://localhost:8080"
            
            # Si pegó la URL completa
            if authorization_response.startswith('http'):
                # Extraer el código de la URL
                from urllib.parse import urlparse, parse_qs
                parsed_url = urlparse(authorization_response)
                query_params = parse_qs(parsed_url.query)
                
                if 'code' in query_params:
                    code = query_params['code'][0]
                    flow.fetch_token(code=code)
                else:
                    st.error("❌ No se encontró código en la URL")
                    return False
            else:
                # Si pegó solo el código
                flow.fetch_token(code=authorization_response)
            
            # Guardar credenciales
            credentials = flow.credentials
            st.session_state.credentials = credentials
            
            # Guardar en archivo
            self._save_credentials_to_file(credentials)
            
            if credentials.refresh_token:
                st.success("✅ ¡Autenticación exitosa!")
                
                # Mostrar el refresh token para guardarlo en secrets
                st.code(f"""
    # Guarda este refresh_token en tus Streamlit Secrets:

    [google_ads]
    refresh_token = "{credentials.refresh_token}"
                """)
                
                return True
            else:
                st.warning("⚠️ Autenticación exitosa pero sin refresh token")
                return True
                
        except Exception as e:
            logger.error(f"Error en callback: {e}")
            st.error(f"❌ Error: {str(e)}")
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