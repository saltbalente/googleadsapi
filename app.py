"""
Google Ads Dashboard - Main Streamlit Application
Multi-page dashboard for Google Ads management and analytics
"""

import streamlit as st
import os
import sys
from pathlib import Path
import logging
from datetime import datetime
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import modules
from modules.auth import GoogleAdsAuth, require_auth
from modules.google_ads_client import GoogleAdsClientWrapper
from modules.ai_ad_generator import AIAdGenerator
from services.billing_service import BillingService
from services.campaign_service import CampaignService
from services.report_service import ReportService
from services.alert_service import AlertService
from utils.logger import get_logger, setup_logging
from utils.cache import CacheManager
from utils.i18n import I18n, init_i18n, t, create_locale_selector

# Load environment variables from .env
load_dotenv(override=True)

# Initialize i18n system
init_i18n(default_locale='es')

# Configure logging
setup_logging(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    log_file=os.getenv('LOG_FILE'),
    json_format=os.getenv('LOG_FORMAT', '').lower() == 'json'
)
logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title=t("page_titles.google_ads_dashboard"),
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://developers.google.com/google-ads/api',
        'Report a bug': None,
        'About': t("page_titles.about_description")
    }
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(90deg, #f0f8ff, #e6f3ff);
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    
    .alert-high {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    
    .alert-medium {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    
    .alert-low {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
        padding: 1rem;
        border-radius: 4px;
        margin: 0.5rem 0;
    }
    
    .sidebar-logo {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-connected {
        background-color: #4caf50;
    }
    
    .status-disconnected {
        background-color: #f44336;
    }
    
    .navigation-item {
        padding: 0.5rem 1rem;
        margin: 0.25rem 0;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .navigation-item:hover {
        background-color: #f0f8ff;
        transform: translateX(5px);
    }
    
    .footer {
        text-align: center;
        padding: 2rem;
        color: #666;
        border-top: 1px solid #eee;
        margin-top: 3rem;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'google_ads_client' not in st.session_state:
        wrapper = GoogleAdsClientWrapper()
        st.session_state.google_ads_client = wrapper
        
        # ✅ Verificar que el cliente real funciona
        real_client = wrapper.get_client()
        if real_client:
            st.success("✅ Cliente de Google Ads inicializado correctamente")
        else:
            st.error("❌ Error al inicializar el cliente de Google Ads")
    
    if 'services' not in st.session_state:
        st.session_state.services = {}
    
    if 'customer_ids' not in st.session_state:
        st.session_state.customer_ids = []
    
    if 'selected_customer' not in st.session_state:
        st.session_state.selected_customer = None
    
    if 'cache_manager' not in st.session_state:
        st.session_state.cache_manager = CacheManager()
    
    # ✅ Inicializar AI Ad Generator
    if 'ai_ad_generator' not in st.session_state:
        try:
            st.session_state.ai_ad_generator = AIAdGenerator()
            logger.info("✅ AI Ad Generator inicializado correctamente")
        except Exception as e:
            logger.error(f"❌ Error inicializando AI Ad Generator: {e}")
            st.session_state.ai_ad_generator = None

def initialize_services():
    """Initialize Google Ads client and services"""
    try:
        # Use existing client if present, otherwise create a new one
        client = st.session_state.get('google_ads_client') or GoogleAdsClientWrapper()
        
        # If client was just created, test connection and store in session
        if not st.session_state.get('google_ads_client'):
            if client.test_connection():
                st.session_state.google_ads_client = client
            else:
                st.error("❌ Failed to connect to Google Ads API. Please check your configuration.")
                return False
        
        # Ensure services are initialized
        if not st.session_state.get('services'):
            st.session_state.services = {
                'billing': BillingService(client),
                'campaign': CampaignService(client),
                'report': ReportService(client),
                'alert': AlertService(client)
            }
        
        # Ensure customer IDs are loaded
        if not st.session_state.get('customer_ids'):
            st.session_state.customer_ids = client.get_customer_ids()
        
        # Ensure a selected customer is set
        if st.session_state.customer_ids and not st.session_state.get('selected_customer'):
            st.session_state.selected_customer = st.session_state.customer_ids[0]
        
        # ========== DESPUÉS DE INICIALIZAR SERVICIOS ==========
        
        # Inicializar lista de anuncios de IA pendientes
        if 'pending_ai_ads' not in st.session_state:
            st.session_state.pending_ai_ads = []
            logger.info("✅ Lista de anuncios de IA inicializada")
        
        # Limpiar anuncios usados antiguos (opcional, ejecutar periódicamente)
        if 'pending_ai_ads' in st.session_state:
            # Mantener solo últimos 50 anuncios no usados
            unused_ads = [ad for ad in st.session_state.pending_ai_ads if not ad.get('used', False)]
            st.session_state.pending_ai_ads = unused_ads[:50]
        
        logger.info(f"Services initialized successfully. Found {len(st.session_state.customer_ids)} customer accounts.")
        return True
    
    except Exception as e:
        logger.error(f"Error initializing services: {e}")
        st.error(f"❌ Error initializing services: {e}")
        return False

def render_sidebar():
    """Render the sidebar with navigation and account selection"""
    with st.sidebar:
        # Logo and title
        st.markdown("""
        <div class="sidebar-logo">
            <h2>📊 Google Ads</h2>
            <p>Dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Connection status
        if st.session_state.google_ads_client:
            st.markdown("""
            <div style="text-align: center; margin-bottom: 1rem;">
                <span class="status-indicator status-connected"></span>
                <span style="color: #4caf50; font-weight: bold;">Connected</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align: center; margin-bottom: 1rem;">
                <span class="status-indicator status-disconnected"></span>
                <span style="color: #f44336; font-weight: bold;">Disconnected</span>
            </div>
            """, unsafe_allow_html=True)
        
        # Account selection
        if st.session_state.customer_ids and st.session_state.get('selected_customer'):
            st.subheader("📋 Cuenta Activa")
            
            # Nombres de las cuentas
            account_names = {
                '7094116152': 'Página 3',
                '1803044752': 'Página 5',
                '9759913462': 'Página 4',
                '6639082872': 'Account',
                '1919262845': 'Marketing',
                '7004285893': 'Página 9'
            }
            
            current_name = account_names.get(st.session_state.selected_customer, 'Cuenta')
            st.info(f"**{current_name}**  \n`{st.session_state.selected_customer}`")
            
            # ✅ NUEVO: Mostrar moneda detectada
            if 'services' in st.session_state and st.session_state.services:
                try:
                    # Importar BidAdjustmentService para detectar moneda
                    from services.bid_adjustment_service import BidAdjustmentService
                    bid_service = BidAdjustmentService(st.session_state.google_ads_client)
                    currency = bid_service.get_account_currency(st.session_state.selected_customer)
                    min_bid = bid_service.get_min_bid_for_currency(currency)
                    
                    st.success(f"💰 **Moneda:** {currency}")
                    st.caption(f"Puja mínima: {min_bid/1_000_000:,.2f} {currency}")
                except Exception as e:
                    logger.warning(f"No se pudo detectar moneda: {e}")
            
            # Botón para cambiar de cuenta
            if st.button("🔄 Cambiar Cuenta", use_container_width=True):
                del st.session_state['selected_customer']
                st.rerun()
        
        st.divider()
        
        # Navigation
        st.subheader("🧭 Navigation")
        
        # Page navigation info
        st.info("""
        **Available Pages:**
        
        📊 **Overview** - Dashboard summary and KPIs
        
        💰 **Billing** - Budget tracking and spend analysis
        
        🎯 **Campaigns** - Campaign performance and management
        
        📈 **Reports** - Custom reports and data export
        
        🚨 **Alerts** - Alert management and monitoring
        
        🤖 **AI Ad Generator** - Generate ads with AI (OpenAI & Gemini)
        
        🎯 **Keyword Health** - Keyword optimization and health scores
        
        📢 **Ad Health** - Ad optimization and health scores
        
        ⚙️ **Settings** - Configuration and preferences
        """)
        
        st.divider()
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Refresh Data", use_container_width=True):
                try:
                    if hasattr(st.session_state.cache_manager, 'clear'):
                        st.session_state.cache_manager.clear()
                    elif hasattr(st.session_state.cache_manager, 'clear_cache'):
                        st.session_state.cache_manager.clear_cache()
                except:
                    pass
                st.success("✅ Datos actualizados")
                st.rerun()
        
        with col2:
            if st.button("📊 Check Alerts", use_container_width=True):
                if 'alert' in st.session_state.services:
                    with st.spinner("Checking alerts..."):
                        alerts = st.session_state.services['alert'].check_alerts([st.session_state.selected_customer])
                        if alerts:
                            st.success(f"Found {len(alerts)} new alerts!")
                        else:
                            st.info("No new alerts found.")
        
        # System info
        st.divider()
        st.subheader("ℹ️ System Info")
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.text(f"Last Updated: {current_time}")
        
        if st.session_state.customer_ids:
            st.text(f"Accounts: {len(st.session_state.customer_ids)}")
        
        # Cache stats
        if hasattr(st.session_state.cache_manager, 'get_stats'):
            try:
                cache_stats = st.session_state.cache_manager.get_stats()
                st.text(f"Cache Entries: {cache_stats.get('entries', 0)}")
            except:
                pass
        
        # Language selector
        st.divider()
        create_locale_selector()

def render_main_content():
    """Render the main content area"""
    
    # Main header
    st.markdown("""
    <div class="main-header">
        📊 Google Ads Dashboard
    </div>
    """, unsafe_allow_html=True)
    
    # Check if services are initialized
    if not st.session_state.google_ads_client:
        st.warning("⚠️ Google Ads API not connected. Please check your configuration.")
        return
    
    # Welcome message for authenticated users
    if st.session_state.selected_customer:
        # Mostrar información de cuenta seleccionada
        account_names = {
            '7094116152': 'Página 3',
            '1803044752': 'Página 5',
            '9759913462': 'Página 4',
            '6639082872': 'Account',
            '1919262845': 'Marketing Creativo Innovador',
            '7004285893': 'Página 9'
        }
        account_name = account_names.get(st.session_state.selected_customer, 'Cuenta')
        
        st.success(f"✅ Cuenta activa: **{account_name}** (`{st.session_state.selected_customer}`)")
        
        st.info("""
        **🎯 ¡Cuenta seleccionada correctamente!**
        
        Usa el menú de navegación en el sidebar para explorar:
        - 📊 **Overview** - KPIs y métricas generales
        - 💰 **Billing** - Gastos y presupuestos
        - 🎯 **Campaigns** - Rendimiento de campañas
        - 📈 **Reports** - Reportes personalizados
        - 🚨 **Alerts** - Alertas y notificaciones
        - 🤖 **AI Ad Generator** - Generar anuncios con IA
        - 🎯 **Keyword Health** - Optimización de keywords
        - 📢 **Ad Health** - Optimización de anuncios
        - ⚙️ **Settings** - Configuración y diagnóstico
        """)

def main():
    """Main application function"""
    try:
        # Initialize session state
        initialize_session_state()
        
        # Initialize authentication
        auth = GoogleAdsAuth()
        
        # Check authentication status
        if not auth.is_authenticated():
            st.warning("🔐 Por favor autentícate con la API de Google Ads para continuar")
            
            st.markdown("---")
            
            # Botón principal de autenticación
            st.markdown("### 🚀 Iniciar Autenticación")
            st.info("""
            **📋 Instrucciones:**
            1. Haz clic en el botón "Iniciar Autenticación"
            2. Serás redirigido a Google para autorizar la aplicación
            3. Después de autorizar, verás una página de confirmación
            4. Regresa a esta página y recárgala (F5 o el botón de recargar)
            5. ¡Listo! Ya estarás autenticado
            """)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🔑 Iniciar Autenticación con Google Ads", use_container_width=True, type="primary"):
                    try:
                        auth_url = auth.get_auth_url()
                        if auth_url:
                            st.success("✅ ¡Servidor de autenticación iniciado!")
                            st.markdown("### 🔗 Haz clic en el enlace para continuar:")
                            st.markdown(f"## [**➡️ Autenticar con Google Ads**]({auth_url})")
                            st.warning("⚠️ **Importante:** Después de completar la autenticación en Google, **regresa a esta página y recárgala (F5)**")
                        else:
                            st.error("❌ Error al generar URL de autorización. Verifica tu archivo client_secret.json.")
                    except Exception as e:
                        st.error(f"❌ Error generando URL de autenticación: {str(e)}")
                        st.info("💡 Verifica que el archivo config/client_secret.json exista y sea válido.")
            
            st.markdown("---")
            st.markdown("### ℹ️ Sobre el mensaje de verificación de Google")
            st.info("""
            Es normal ver el mensaje **"Google no ha verificado esta aplicación"**.
            
            Esto ocurre porque tu aplicación está en modo de desarrollo. Para continuar:
            
            1. Haz clic en **"Opciones avanzadas"** o **"Advanced"**
            2. Luego haz clic en **"Ir a ApiFull (no seguro)"** o **"Go to ApiFull (unsafe)"**
            3. Autoriza los permisos solicitados
            
            **Nota:** Solo tú puedes acceder a esta aplicación con tus credenciales.
            """)
            
            return
        
        # Initialize services if authenticated
        if not st.session_state.get('services'):
            with st.spinner("Inicializando servicios de Google Ads..."):
                if not initialize_services():
                    st.error("Error al inicializar los servicios")
                    return
        
        # Verificar si hay cuentas disponibles
        if not st.session_state.get('customer_ids'):
            st.error("⚠️ No se encontraron cuentas de Google Ads")
            st.info("""
            **Posibles soluciones:**
            1. Verifica que el archivo `config/accounts.txt` tenga IDs de cuentas
            2. Asegúrate de que las cuentas estén vinculadas a tu cuenta manager (MCC)
            3. Revisa que el `login_customer_id` en `config/google-ads.yaml` sea correcto
            """)
            return
        
        # Mostrar selector de cuenta si no hay una seleccionada
        if not st.session_state.get('selected_customer'):
            st.markdown("## 🎯 Selecciona una Cuenta de Google Ads")
            st.info(f"✅ Autenticado correctamente. Se encontraron **{len(st.session_state.customer_ids)}** cuentas disponibles.")
            
            # Crear opciones de cuentas con nombres descriptivos
            account_names = {
                '7094116152': '📊 Página 3 (709-411-6152)',
                '1803044752': '📊 Página 5 (180-304-4752)',
                '9759913462': '📊 Página 4 (975-991-3462)',
                '6639082872': '📊 Account (663-908-2872)',
                '1919262845': '📊 Marketing Creativo Innovador (191-926-2845)',
                '7004285893': '📊 Página 9 (700-428-5893)'
            }
            
            # Crear opciones para el selectbox
            account_options = []
            for customer_id in st.session_state.customer_ids:
                name = account_names.get(customer_id, f'📊 Cuenta {customer_id}')
                account_options.append((name, customer_id))
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                selected_account = st.selectbox(
                    "Selecciona una cuenta:",
                    options=[opt[0] for opt in account_options],
                    key='account_selector'
                )
                
                if st.button("✅ Continuar con esta cuenta", use_container_width=True, type="primary"):
                    # Encontrar el customer_id correspondiente
                    for name, customer_id in account_options:
                        if name == selected_account:
                            st.session_state.selected_customer = customer_id
                            st.success(f"✅ Cuenta seleccionada: {name}")
                            st.rerun()
                            break
            
            st.markdown("---")
            st.info("💡 **Tip:** Puedes cambiar de cuenta en cualquier momento desde el sidebar")
            return
        
        # Render sidebar
        render_sidebar()
        
        # Render main content
        render_main_content()
        
        # Footer
        st.markdown("""
        <div class="footer">
            <p>Google Ads Dashboard | Built with Streamlit | 
            <a href="https://developers.google.com/google-ads/api" target="_blank">Google Ads API Documentation</a></p>
        </div>
        """, unsafe_allow_html=True)
    
    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error(f"❌ Application error: {e}")
        
        if st.button("🔄 Restart Application"):
            st.rerun()

if __name__ == "__main__":
    main()