"""
Servidor HTTP temporal para manejar el callback de OAuth2 de Google.
Este servidor se ejecuta en un puerto separado para capturar el código de autorización.
"""

import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging

logger = logging.getLogger(__name__)

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Manejador para el callback de OAuth2"""
    
    def _process_auth_code_immediately(self, auth_code: str):
        """Procesa el código de autorización y guarda las credenciales inmediatamente"""
        try:
            import json
            import yaml
            from google_auth_oauthlib.flow import Flow
            from google.auth.transport.requests import Request
            
            client_secrets_file = "config/client_secret.json"
            if not os.path.exists(client_secrets_file):
                logger.error(f"Client secrets file not found: {client_secrets_file}")
                return False
            
            # Crear flow OAuth
            scopes = ['https://www.googleapis.com/auth/adwords']
            
            # Para credenciales de tipo "installed" (Desktop app), usar el puerto correcto
            flow = Flow.from_client_secrets_file(
                client_secrets_file,
                scopes=scopes
            )
            # Configurar redirect_uri manualmente para loopback
            flow.redirect_uri = f"http://localhost:{self.server.server_port}/oauth2callback"
            
            # Intercambiar código por credenciales
            flow.fetch_token(code=auth_code)
            credentials = flow.credentials
            
            if not credentials or not credentials.refresh_token:
                logger.error("No se obtuvo refresh token")
                return False
            
            # Guardar credenciales en oauth_credentials.json
            creds_data = {
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': list(credentials.scopes) if credentials.scopes else scopes
            }
            
            os.makedirs('config', exist_ok=True)
            with open('config/oauth_credentials.json', 'w') as f:
                json.dump(creds_data, f, indent=2)
            
            logger.info("✓ Credentials saved to oauth_credentials.json")
            
            # Actualizar google-ads.yaml
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
                    
                    logger.info("✓ google-ads.yaml updated with new credentials")
                except Exception as e:
                    logger.warning(f"Could not update google-ads.yaml: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing auth code: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def do_GET(self):
        """Maneja las solicitudes GET del callback de OAuth"""
        try:
            # Parsear la URL para obtener el código de autorización
            parsed_path = urlparse(self.path)
            query_params = parse_qs(parsed_path.query)
            
            if 'code' in query_params:
                # Código de autorización recibido exitosamente
                auth_code = query_params['code'][0]
                
                # Guardar el código en el servidor para que la aplicación principal lo pueda obtener
                self.server.auth_code = auth_code
                self.server.auth_received = True
                
                # Procesar el código INMEDIATAMENTE y guardar las credenciales
                try:
                    self._process_auth_code_immediately(auth_code)
                    logger.info("Auth code processed and credentials saved successfully")
                except Exception as e:
                    logger.error(f"Error processing auth code immediately: {e}")
                
                # Responder con una página de éxito
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                
                success_html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Autenticación Exitosa - Google Ads Dashboard</title>
                    <meta charset="utf-8">
                    <style>
                        body { 
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                            text-align: center; 
                            padding: 50px; 
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            margin: 0;
                            min-height: 100vh;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                        }
                        .container { 
                            max-width: 700px; 
                            margin: 0 auto; 
                            background: white; 
                            padding: 40px; 
                            border-radius: 15px; 
                            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                        }
                        .success { 
                            color: #4caf50; 
                            font-size: 32px; 
                            margin-bottom: 20px; 
                            font-weight: bold;
                        }
                        .subtitle {
                            color: #666;
                            font-size: 18px;
                            margin-bottom: 30px;
                        }
                        .code-section {
                            background: #f8f9fa;
                            border: 2px solid #e9ecef;
                            padding: 20px;
                            border-radius: 10px;
                            margin: 25px 0;
                        }
                        .code-label {
                            color: #495057;
                            font-weight: bold;
                            margin-bottom: 10px;
                            font-size: 14px;
                        }
                        .code { 
                            background: #ffffff;
                            border: 1px solid #dee2e6;
                            padding: 15px; 
                            border-radius: 8px; 
                            font-family: 'Courier New', monospace; 
                            word-break: break-all; 
                            font-size: 14px;
                            color: #212529;
                        }
                        .next-steps {
                            background: #e8f5e8;
                            border-left: 5px solid #4caf50;
                            padding: 20px;
                            border-radius: 8px;
                            margin: 25px 0;
                            text-align: left;
                        }
                        .next-steps h3 {
                            color: #2e7d32;
                            margin-top: 0;
                            font-size: 18px;
                        }
                        .step {
                            margin: 10px 0;
                            padding: 8px 0;
                            color: #1b5e20;
                        }
                        .step-number {
                            background: #4caf50;
                            color: white;
                            border-radius: 50%;
                            width: 25px;
                            height: 25px;
                            display: inline-flex;
                            align-items: center;
                            justify-content: center;
                            margin-right: 10px;
                            font-weight: bold;
                            font-size: 12px;
                        }
                        .return-button {
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            padding: 15px 30px;
                            border: none;
                            border-radius: 25px;
                            font-size: 16px;
                            font-weight: bold;
                            text-decoration: none;
                            display: inline-block;
                            margin: 20px 0;
                            transition: transform 0.2s, box-shadow 0.2s;
                        }
                        .return-button:hover {
                            transform: translateY(-2px);
                            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
                            text-decoration: none;
                            color: white;
                        }
                        .footer-note {
                            color: #6c757d;
                            font-size: 14px;
                            margin-top: 30px;
                            padding-top: 20px;
                            border-top: 1px solid #e9ecef;
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="success">🎉 ¡Autenticación Completada!</div>
                        <div class="subtitle">Tu cuenta de Google Ads ha sido vinculada exitosamente</div>
                        
                        <div class="code-section">
                            <div class="code-label">📋 Código de Autorización Recibido:</div>
                            <div class="code">""" + auth_code + """</div>
                        </div>
                        
                        <div class="next-steps">
                            <h3>🚀 Próximos Pasos</h3>
                            <div class="step">
                                <span class="step-number">1</span>
                                <strong>Regresa a la aplicación principal</strong> haciendo clic en el botón de abajo
                            </div>
                            <div class="step">
                                <span class="step-number">2</span>
                                <strong>La autenticación se detectará automáticamente</strong> y podrás acceder a tus datos
                            </div>
                            <div class="step">
                                <span class="step-number">3</span>
                                <strong>¡Comienza a explorar tu dashboard!</strong> Todas las funciones estarán disponibles
                            </div>
                        </div>
                        
                        <a href="http://localhost:8501" class="return-button" target="_blank">
                            🏠 Regresar al Dashboard de Google Ads
                        </a>
                        
                        <div class="footer-note">
                            💡 <strong>Nota:</strong> Puedes cerrar esta ventana después de regresar a la aplicación principal.<br>
                            El código de autorización se ha guardado automáticamente y no necesitas copiarlo manualmente.
                        </div>
                    </div>
                </body>
                </html>
                """
                
                self.wfile.write(success_html.encode('utf-8'))
                logger.info(f"OAuth callback recibido exitosamente")
                
            elif 'error' in query_params:
                # Error en la autorización
                error = query_params['error'][0]
                error_description = query_params.get('error_description', [''])[0]
                
                self.server.auth_error = f"{error}: {error_description}"
                self.server.auth_received = True
                
                # Responder con una página de error
                self.send_response(400)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                
                error_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Error de Autenticación</title>
                    <meta charset="utf-8">
                    <style>
                        body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; background-color: #ffebee; }}
                        .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        .error {{ color: #f44336; font-size: 24px; margin-bottom: 20px; }}
                        .details {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="error">❌ Error de Autenticación</div>
                        <p>Ocurrió un error durante la autenticación:</p>
                        <div class="details">{error}: {error_description}</div>
                        <p>Puedes cerrar esta ventana e intentar nuevamente.</p>
                    </div>
                </body>
                </html>
                """
                
                self.wfile.write(error_html.encode('utf-8'))
                logger.error(f"Error en OAuth callback: {error} - {error_description}")
                
            else:
                # Solicitud inválida
                self.send_response(400)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                
                invalid_html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Solicitud Inválida</title>
                    <meta charset="utf-8">
                </head>
                <body>
                    <h1>Solicitud Inválida</h1>
                    <p>No se encontró código de autorización en la solicitud.</p>
                </body>
                </html>
                """
                
                self.wfile.write(invalid_html.encode('utf-8'))
                logger.warning("Solicitud OAuth inválida - no se encontró código")
                
        except Exception as e:
            logger.error(f"Error procesando callback OAuth: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>Error interno del servidor</h1>")
    
    def log_message(self, format, *args):
        """Suprimir logs del servidor HTTP para mantener limpia la salida"""
        pass


class OAuthCallbackServer:
    """Servidor temporal para manejar callbacks de OAuth2"""
    
    def __init__(self, port=8080):
        self.port = port
        self.server = None
        self.thread = None
        self.auth_code = None
        self.auth_error = None
        self.auth_received = False
        
    def _find_available_port(self, start_port=8080, max_attempts=10):
        """Encuentra un puerto disponible comenzando desde start_port"""
        import socket
        
        for port in range(start_port, start_port + max_attempts):
            try:
                # Intentar crear un socket en el puerto
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    return port
            except OSError:
                continue
        
        raise Exception(f"No se pudo encontrar un puerto disponible entre {start_port} y {start_port + max_attempts - 1}")
        
    def start(self):
        """Iniciar el servidor en un hilo separado con fallback de puertos"""
        last_error = None
        
        try:
            # Primero intentar con el puerto especificado
            try:
                self.server = HTTPServer(('localhost', self.port), OAuthCallbackHandler)
                self.server.auth_code = None
                self.server.auth_error = None
                self.server.auth_received = False
                
                # Ejecutar servidor en hilo separado
                self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
                self.thread.start()
                
                logger.info(f"Servidor OAuth callback iniciado en puerto {self.port}")
                return True
                
            except OSError as e:
                last_error = e
                logger.warning(f"Puerto {self.port} no disponible: {e}")
                
                # Buscar un puerto alternativo
                try:
                    available_port = self._find_available_port(self.port + 1)
                    logger.info(f"Intentando puerto alternativo: {available_port}")
                    
                    self.port = available_port  # Actualizar el puerto
                    self.server = HTTPServer(('localhost', self.port), OAuthCallbackHandler)
                    self.server.auth_code = None
                    self.server.auth_error = None
                    self.server.auth_received = False
                    
                    # Ejecutar servidor en hilo separado
                    self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
                    self.thread.start()
                    
                    logger.info(f"Servidor OAuth callback iniciado en puerto alternativo {self.port}")
                    return True
                    
                except Exception as fallback_error:
                    last_error = fallback_error
                    logger.error(f"Error con puerto alternativo: {fallback_error}")
            
        except Exception as e:
            last_error = e
            logger.error(f"Error general iniciando servidor OAuth: {e}")
        
        # Si llegamos aquí, no se pudo iniciar el servidor
        error_msg = f"No se pudo iniciar el servidor OAuth. Último error: {last_error}"
        logger.error(error_msg)
        return False
    
    def stop(self):
        """Detener el servidor"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info("Servidor OAuth callback detenido")
    
    def wait_for_callback(self, timeout=300):
        """
        Esperar por el callback de OAuth con timeout
        
        Args:
            timeout (int): Tiempo máximo de espera en segundos (default: 5 minutos)
            
        Returns:
            tuple: (success, auth_code_or_error)
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.server and self.server.auth_received:
                if hasattr(self.server, 'auth_code') and self.server.auth_code:
                    return True, self.server.auth_code
                elif hasattr(self.server, 'auth_error') and self.server.auth_error:
                    return False, self.server.auth_error
            
            time.sleep(0.5)  # Verificar cada 500ms
        
        return False, "Timeout: No se recibió respuesta de OAuth en el tiempo esperado"
    
    def get_redirect_uri(self):
        """Obtener la URI de redirección para este servidor"""
        return f"http://localhost:{self.port}/oauth2callback"