"""
Google Ads OAuth 2.0 Authentication Module
Handles authentication flow and token management
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
from .oauth_server import OAuthCallbackServer

logger = logging.getLogger(__name__)

class GoogleAdsAuth:
    """Handles Google Ads API authentication using OAuth 2.0"""
    
    def __init__(self, client_secrets_file: str = "config/client_secret.json"):
        self.client_secrets_file = client_secrets_file
        self.scopes = ['https://www.googleapis.com/auth/adwords']
        self.oauth_server = OAuthCallbackServer(port=8080)
        self.redirect_uri = self.oauth_server.get_redirect_uri()
        
    def get_credentials(self) -> Optional[Credentials]:
        """Get valid credentials from session state, saved file, or environment"""
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
        """Generate OAuth authorization URL and start callback server"""
        try:
            if not os.path.exists(self.client_secrets_file):
                raise FileNotFoundError(f"Archivo client_secret.json no encontrado: {self.client_secrets_file}")
            
            # Iniciar servidor de callback con manejo mejorado de errores
            server_started = self.oauth_server.start()
            if not server_started:
                # Proporcionar información más específica sobre el error
                error_details = []
                error_details.append("• El servidor OAuth no pudo iniciarse")
                error_details.append(f"• Puerto intentado: {self.oauth_server.port}")
                error_details.append("• Posibles causas:")
                error_details.append("  - Otro proceso está usando los puertos disponibles")
                error_details.append("  - Permisos insuficientes para crear el servidor")
                error_details.append("  - Firewall bloqueando las conexiones locales")
                
                error_msg = "\n".join(error_details)
                raise Exception(f"No se pudo iniciar el servidor de callback OAuth:\n{error_msg}")
            
            # Actualizar redirect_uri con el puerto que realmente se está usando
            self.redirect_uri = self.oauth_server.get_redirect_uri()
                
            # Para credenciales de tipo "installed" (Desktop app)
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
            st.session_state.oauth_server = self.oauth_server
            
            # Mostrar información del servidor iniciado
            if self.oauth_server.port != 8080:
                st.info(f"ℹ️ Servidor OAuth iniciado en puerto alternativo: {self.oauth_server.port}")
            
            return auth_url
            
        except FileNotFoundError as e:
            logger.error(f"Client secrets file not found: {e}")
            st.error(f"❌ Archivo de configuración no encontrado: {str(e)}")
            return ""
        except Exception as e:
            logger.error(f"Error generating auth URL: {e}")
            st.error(f"❌ Error al generar URL de autenticación:\n{str(e)}")
            return ""
    
    def handle_callback(self, authorization_code: str = None) -> bool:
        """Handle OAuth callback and store credentials"""
        try:
            # Si se proporciona código manualmente, usarlo directamente
            if authorization_code:
                logger.info("Usando código de autorización proporcionado manualmente")
            else:
                # Intentar obtener el código del servidor OAuth activo
                oauth_server = st.session_state.get('oauth_server')
                if oauth_server and oauth_server.server:
                    if hasattr(oauth_server.server, 'auth_received') and oauth_server.server.auth_received:
                        if hasattr(oauth_server.server, 'auth_code') and oauth_server.server.auth_code:
                            authorization_code = oauth_server.server.auth_code
                            logger.info("Código de autorización obtenido del servidor OAuth")
                        elif hasattr(oauth_server.server, 'auth_error') and oauth_server.server.auth_error:
                            st.error(f"❌ Error en autenticación: {oauth_server.server.auth_error}")
                            return False
                
                # Si aún no tenemos código, verificar si hay un flow guardado para crear uno nuevo
                if not authorization_code:
                    logger.warning("No se encontró código de autorización en el servidor OAuth")
                    st.error("❌ No se recibió código de autorización. Por favor, intenta el proceso nuevamente.")
                    return False
            
            # Obtener o crear el flow OAuth
            flow = st.session_state.get('oauth_flow')
            if not flow:
                # Si no hay flow en session, intentar crear uno nuevo
                if not os.path.exists(self.client_secrets_file):
                    st.error("❌ Archivo client_secret.json no encontrado")
                    return False
                
                from google_auth_oauthlib.flow import Flow
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
            
            if not authorization_code:
                st.error("No se recibió código de autorización.")
                return False
            
            flow.fetch_token(code=authorization_code)
            
            credentials = flow.credentials
            st.session_state.credentials = credentials
            
            # Save credentials to file for persistence
            self._save_credentials_to_file(credentials)
            
            # Limpiar servidor de session state
            if 'oauth_server' in st.session_state:
                del st.session_state['oauth_server']
            
            # Optionally save refresh token for future use
            if credentials.refresh_token:
                st.success("¡Autenticación exitosa! Token de actualización obtenido.")
                logger.info("OAuth authentication completed successfully")
            else:
                st.warning("Autenticación exitosa, pero no se obtuvo token de actualización. Es posible que necesites volver a autenticarte.")
            
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
        st.success("Logged out successfully")
    
    def _save_credentials_to_file(self, credentials: Credentials):
        """Save credentials to oauth_credentials.json file and update google-ads.yaml"""
        try:
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
            st.warning("⚠️ Authentication required to access this page")
            st.info("Please go to Settings page to authenticate with Google Ads API")
            st.stop()
        return func(*args, **kwargs)
    return wrapper