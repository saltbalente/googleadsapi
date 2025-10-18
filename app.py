"""
app.py - Google Ads Dashboard 2030 - Ultra Modern Dark Design
Dashboard multipestaña con UI/UX futurista
Versión: 2.0 Ultra - Español
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
from utils.account_cache_manager import AccountCacheManager  # ✅ CORRECTO
from modules.google_ads_client import GoogleAdsClientWrapper



# Load environment variables
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

# ============================================================================
# ULTRA MODERN 2030 DARK THEME CSS - ESPAÑOL
# ============================================================================

ULTRA_MODERN_CSS = """
<style>
    /* ============================================
       🎨 GLOBAL DARK THEME
       ============================================ */
    
    :root {
        --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --secondary-gradient: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        --success-gradient: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        --dark-bg: #0a0e27;
        --dark-surface: #141b2d;
        --dark-card: #1a2235;
        --dark-hover: #222b3e;
        --accent-blue: #4facfe;
        --accent-purple: #667eea;
        --accent-pink: #f093fb;
        --text-primary: #ffffff;
        --text-secondary: #b0b8d4;
        --text-muted: #6b7897;
    }
    
    /* Main app background */
    .stApp {
        background: var(--dark-bg);
        color: var(--text-primary);
    }
    
    /* Remove default Streamlit padding */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* ============================================
       🎯 GLASSMORPHISM CARDS
       ============================================ */
    
    .glass-card {
        background: rgba(26, 34, 53, 0.6);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .glass-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(102, 126, 234, 0.2);
        border-color: rgba(102, 126, 234, 0.3);
    }
    
    /* ============================================
       🌟 HEADER ULTRA MODERN
       ============================================ */
    
    .ultra-header {
        position: relative;
        background: var(--primary-gradient);
        padding: 3rem 2rem;
        border-radius: 24px;
        margin-bottom: 2rem;
        overflow: hidden;
        box-shadow: 0 20px 60px rgba(102, 126, 234, 0.3);
    }
    
    .ultra-header::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: pulse 4s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.1); opacity: 0.8; }
    }
    
    .ultra-header h1 {
        position: relative;
        z-index: 1;
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        margin: 0;
        background: linear-gradient(to right, #fff, #f0f0f0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 30px rgba(255, 255, 255, 0.3);
        letter-spacing: -1px;
    }
    
    .ultra-header p {
        position: relative;
        z-index: 1;
        text-align: center;
        margin-top: 0.5rem;
        font-size: 1.1rem;
        color: rgba(255, 255, 255, 0.9);
        font-weight: 300;
    }
    
    /* ============================================
       🔘 NAVIGATION BUTTONS MODERN
       ============================================ */
    
    .nav-button {
        display: block;
        width: 100%;
        padding: 1.25rem;
        margin: 0.75rem 0;
        background: var(--dark-card);
        border: 2px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        text-decoration: none;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .nav-button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: var(--primary-gradient);
        transition: left 0.4s ease;
        z-index: 0;
    }
    
    .nav-button:hover::before {
        left: 0;
    }
    
    .nav-button:hover {
        transform: translateY(-5px) scale(1.02);
        border-color: var(--accent-blue);
        box-shadow: 0 15px 40px rgba(102, 126, 234, 0.3);
    }
    
    .nav-button-content {
        position: relative;
        z-index: 1;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .nav-button-left {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .nav-button-icon {
        font-size: 2.5rem;
        filter: drop-shadow(0 0 10px currentColor);
        transition: transform 0.3s ease;
    }
    
    .nav-button:hover .nav-button-icon {
        transform: scale(1.2) rotate(5deg);
    }
    
    .nav-button-text {
        text-align: left;
    }
    
    .nav-button-title {
        color: var(--text-primary);
        font-size: 1.3rem;
        font-weight: 700;
        margin: 0;
        transition: color 0.3s ease;
    }
    
    .nav-button:hover .nav-button-title {
        color: white;
    }
    
    .nav-button-description {
        color: var(--text-secondary);
        font-size: 0.9rem;
        margin: 0.25rem 0 0 0;
        transition: color 0.3s ease;
    }
    
    .nav-button:hover .nav-button-description {
        color: rgba(255, 255, 255, 0.9);
    }
    
    .nav-button-arrow {
        font-size: 1.5rem;
        color: var(--text-muted);
        transition: all 0.3s ease;
    }
    
    .nav-button:hover .nav-button-arrow {
        color: white;
        transform: translateX(5px);
    }
    
    /* ============================================
       🎨 SIDEBAR ULTRA MODERN
       ============================================ */
    
    [data-testid="stSidebar"] {
        background: var(--dark-surface);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .sidebar-logo {
        text-align: center;
        padding: 2rem 1rem;
        background: var(--primary-gradient);
        border-radius: 16px;
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
    }
    
    .sidebar-logo::after {
        content: '';
        position: absolute;
        bottom: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.2) 0%, transparent 70%);
        animation: rotate 10s linear infinite;
    }
    
    @keyframes rotate {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .sidebar-logo h2 {
        position: relative;
        z-index: 1;
        margin: 0;
        font-size: 1.8rem;
        font-weight: 800;
        color: white;
        text-shadow: 0 0 20px rgba(255, 255, 255, 0.5);
    }
    
    .sidebar-logo p {
        position: relative;
        z-index: 1;
        margin: 0.5rem 0 0 0;
        color: rgba(255, 255, 255, 0.9);
        font-weight: 300;
    }
    
    /* ============================================
       🔘 MODERN BUTTONS
       ============================================ */
    
    .stButton > button {
        background: var(--primary-gradient);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* ============================================
       📊 STATUS INDICATORS
       ============================================ */
    
    .status-container {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 1rem;
        background: var(--dark-card);
        border-radius: 12px;
        margin-bottom: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .status-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
        animation: breathe 2s ease-in-out infinite;
    }
    
    @keyframes breathe {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.7; transform: scale(1.1); }
    }
    
    .status-connected {
        background: #4ade80;
        box-shadow: 0 0 15px #4ade80;
    }
    
    .status-disconnected {
        background: #ef4444;
        box-shadow: 0 0 15px #ef4444;
    }
    
    .status-text {
        font-weight: 600;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* ============================================
       🎯 ACCOUNT CARD
       ============================================ */
    
    .account-card {
        background: var(--dark-card);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
        position: relative;
        overflow: hidden;
    }
    
    .account-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: var(--success-gradient);
    }
    
    .account-name {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
    }
    
    .account-id {
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        color: var(--text-muted);
        background: rgba(255, 255, 255, 0.05);
        padding: 0.25rem 0.75rem;
        border-radius: 8px;
        display: inline-block;
    }
    
    /* ============================================
       💰 CURRENCY BADGE
       ============================================ */
    
    .currency-badge {
        background: var(--success-gradient);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 12px;
        font-weight: 700;
        text-align: center;
        box-shadow: 0 4px 15px rgba(79, 172, 254, 0.3);
        margin-top: 1rem;
    }
    
    /* ============================================
       📱 NAVIGATION ITEMS SIDEBAR
       ============================================ */
    
    .nav-section {
        margin: 1.5rem 0;
    }
    
    .nav-section-title {
        color: var(--text-muted);
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 1rem;
        padding-left: 0.5rem;
    }
    
    .nav-item {
        display: flex;
        align-items: center;
        padding: 0.75rem 1rem;
        margin: 0.25rem 0;
        border-radius: 12px;
        background: transparent;
        transition: all 0.3s ease;
        cursor: pointer;
        border: 1px solid transparent;
    }
    
    .nav-item:hover {
        background: var(--dark-hover);
        border-color: rgba(102, 126, 234, 0.3);
        transform: translateX(5px);
    }
    
    .nav-item-icon {
        font-size: 1.2rem;
        margin-right: 0.75rem;
        width: 24px;
        text-align: center;
    }
    
    .nav-item-text {
        color: var(--text-secondary);
        font-weight: 500;
        font-size: 0.9rem;
    }
    
    /* ============================================
       📊 SYSTEM INFO CARDS
       ============================================ */
    
    .system-info {
        background: var(--dark-card);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .system-info-label {
        color: var(--text-muted);
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .system-info-value {
        color: var(--text-primary);
        font-weight: 700;
        font-family: 'Courier New', monospace;
    }
    
    /* ============================================
       🌊 ANIMATED BACKGROUND
       ============================================ */
    
    .animated-bg {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: -1;
        opacity: 0.03;
        background: 
            radial-gradient(circle at 20% 50%, var(--accent-blue) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, var(--accent-purple) 0%, transparent 50%),
            radial-gradient(circle at 40% 20%, var(--accent-pink) 0%, transparent 50%);
        animation: gradient-shift 15s ease infinite;
    }
    
    @keyframes gradient-shift {
        0%, 100% { transform: translate(0, 0); }
        33% { transform: translate(20px, -20px); }
        66% { transform: translate(-20px, 20px); }
    }
    
    /* ============================================
       📱 RESPONSIVE
       ============================================ */
    
    @media (max-width: 768px) {
        .ultra-header h1 {
            font-size: 2rem;
        }
        
        .nav-button {
            padding: 1rem;
        }
        
        .nav-button-icon {
            font-size: 2rem;
        }
        
        .nav-button-title {
            font-size: 1.1rem;
        }
    }
    
    /* ============================================
       🎯 SCROLLBAR CUSTOM
       ============================================ */
    
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--dark-surface);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--accent-blue);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-purple);
    }
</style>
"""

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Google Ads Dashboard 2030",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://developers.google.com/google-ads/api',
        'Report a bug': None,
        'About': '🚀 Google Ads Dashboard 2030 - Edición Ultra Moderna'
    }
)

# Apply ultra modern CSS
st.markdown(ULTRA_MODERN_CSS, unsafe_allow_html=True)

# Animated background
st.markdown('<div class="animated-bg"></div>', unsafe_allow_html=True)


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def initialize_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'google_ads_client' not in st.session_state:
        wrapper = GoogleAdsClientWrapper()
        st.session_state.google_ads_client = wrapper
        
        real_client = wrapper.get_client()
        if real_client:
            logger.info("✅ Cliente de Google Ads inicializado")
    
    if 'services' not in st.session_state:
        st.session_state.services = {}
    
    if 'customer_ids' not in st.session_state:
        st.session_state.customer_ids = []
    
    if 'selected_customer' not in st.session_state:
        st.session_state.selected_customer = None
    
    if 'cache_manager' not in st.session_state:
        st.session_state.cache_manager = CacheManager()
    
    # ⬅️ ESTE ES CRÍTICO
    if 'account_cache_manager' not in st.session_state:
        st.session_state.account_cache_manager = AccountCacheManager(
            cache_file="data/account_names_cache.json",
            cache_days=30
        )
        logger.info("✅ Account Cache Manager inicializado")
    
    if 'ai_ad_generator' not in st.session_state:
        try:
            st.session_state.ai_ad_generator = AIAdGenerator()
            logger.info("✅ AI Ad Generator inicializado")
        except Exception as e:
            logger.error(f"❌ Error inicializando AI Ad Generator: {e}")
            st.session_state.ai_ad_generator = None


 
def initialize_services():
    """Initialize Google Ads services"""
    try:
        client = st.session_state.get('google_ads_client') or GoogleAdsClientWrapper()
        
        if not st.session_state.get('google_ads_client'):
            if client.test_connection():
                st.session_state.google_ads_client = client
            else:
                return False
        
        if not st.session_state.get('services'):
            st.session_state.services = {
                'billing': BillingService(client),
                'campaign': CampaignService(client),
                'report': ReportService(client),
                'alert': AlertService(client)
            }
        
        if not st.session_state.get('customer_ids'):
            st.session_state.customer_ids = client.get_customer_ids()
        
        if st.session_state.customer_ids and not st.session_state.get('selected_customer'):
            st.session_state.selected_customer = st.session_state.customer_ids[0]
        
        if 'pending_ai_ads' not in st.session_state:
            st.session_state.pending_ai_ads = []
        
        logger.info(f"✅ Services initialized. {len(st.session_state.customer_ids)} accounts found.")
        return True
    
    except Exception as e:
        logger.error(f"❌ Error initializing services: {e}")
        return False


def get_account_names(customer_ids: list) -> dict:
    """
    Obtiene los nombres de las cuentas con sistema de caché inteligente
    
    1. Primero intenta obtener desde caché local
    2. Si no existe o está expirado, consulta la API
    3. Guarda los nuevos nombres en caché
    
    Args:
        customer_ids: Lista de IDs de clientes
        
    Returns:
        Diccionario con {customer_id: account_name}
    """
    cache_manager = st.session_state.account_cache_manager
    
    # Intentar obtener desde caché
    cached_names = cache_manager.get_all_account_names()
    
    # Verificar qué cuentas faltan en el caché
    missing_ids = [cid for cid in customer_ids if cid not in cached_names]
    
    if not missing_ids and cached_names:
        # Todas las cuentas están en caché válido
        logger.info(f"✅ Usando nombres desde caché: {len(cached_names)} cuentas")
        return {cid: cached_names[cid] for cid in customer_ids if cid in cached_names}
    
    # Si hay cuentas faltantes, consultar la API
    logger.info(f"🔄 Consultando API para {len(missing_ids)} cuentas nuevas o expiradas")
    
    account_names = cached_names.copy() if cached_names else {}
    
    try:
        client = st.session_state.google_ads_client
        if client and hasattr(client, 'get_account_descriptive_names'):
            # Obtener nombres desde la API solo para las cuentas faltantes
            new_names = client.get_account_descriptive_names(missing_ids)
            
            # Actualizar el diccionario con los nombres nuevos
            account_names.update(new_names)
            
            # Guardar en caché
            cache_manager.set_multiple_accounts(new_names)
            
            logger.info(f"✅ Nombres actualizados: {len(new_names)} desde API, {len(cached_names)} desde caché")
        else:
            # Si no hay cliente o método, usar nombres por defecto
            logger.warning("⚠️ Método get_account_descriptive_names no disponible")
            for cid in missing_ids:
                account_names[cid] = f"Cuenta {cid}"
    
    except Exception as e:
        logger.error(f"❌ Error obteniendo nombres: {e}")
        # Usar nombres por defecto para las faltantes
        for cid in missing_ids:
            if cid not in account_names:
                account_names[cid] = f"Cuenta {cid}"
    
    return account_names



# ============================================================================
# ULTRA MODERN SIDEBAR - ESPAÑOL
# ============================================================================

def render_ultra_modern_sidebar():
    """Render ultra modern sidebar with glassmorphism - Español"""
    with st.sidebar:
        # Logo con animación
        st.markdown("""
        <div class="sidebar-logo">
            <h2>🚀 GOOGLE ADS</h2>
            <p>Dashboard 2030</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Connection status con animación
        if st.session_state.google_ads_client:
            st.markdown("""
            <div class="status-container">
                <div class="status-dot status-connected"></div>
                <span class="status-text" style="color: #4ade80;">CONECTADO</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="status-container">
                <div class="status-dot status-disconnected"></div>
                <span class="status-text" style="color: #ef4444;">DESCONECTADO</span>
            </div>
            """, unsafe_allow_html=True)
        
        # Account selection
        if st.session_state.customer_ids and st.session_state.get('selected_customer'):
            st.markdown('<div class="nav-section-title">📋 CUENTA ACTIVA</div>', unsafe_allow_html=True)
            
            # ⬅️ USAR FUNCIÓN CON CACHÉ
            account_names = get_account_names(st.session_state.customer_ids)
            current_name = account_names.get(st.session_state.selected_customer, 'Cuenta')
            
            st.markdown(f"""
            <div class="account-card">
                <div class="account-name">{current_name}</div>
                <div class="account-id">{st.session_state.selected_customer}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Detectar moneda
            if 'services' in st.session_state and st.session_state.services:
                try:
                    from services.bid_adjustment_service import BidAdjustmentService
                    bid_service = BidAdjustmentService(st.session_state.google_ads_client)
                    currency = bid_service.get_account_currency(st.session_state.selected_customer)
                    min_bid = bid_service.get_min_bid_for_currency(currency)
                    
                    st.markdown(f"""
                    <div class="currency-badge">
                        💰 {currency} | Puja Mín: {min_bid/1_000_000:,.2f}
                    </div>
                    """, unsafe_allow_html=True)
                except:
                    pass
            
            # Botón para cambiar cuenta con selectbox
            if st.button("🔄 Cambiar Cuenta", use_container_width=True):
                st.session_state.show_account_selector = True
            
            # Mostrar selectbox si se activó
            if st.session_state.get('show_account_selector', False):
                account_options = []
                for customer_id in st.session_state.customer_ids:
                    name = account_names.get(customer_id, 'Cuenta')
                    display_text = f"{customer_id} - {name}"
                    account_options.append((display_text, customer_id))
                
                # Encontrar el índice de la cuenta seleccionada actualmente
                current_index = 0
                for idx, (display, cid) in enumerate(account_options):
                    if cid == st.session_state.selected_customer:
                        current_index = idx
                        break
                
                selected_account_display = st.selectbox(
                    "Selecciona una cuenta:",
                    options=[opt[0] for opt in account_options],
                    index=current_index,
                    key='sidebar_account_selector'
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Cambiar", use_container_width=True):
                        for display, customer_id in account_options:
                            if display == selected_account_display:
                                st.session_state.selected_customer = customer_id
                                st.session_state.show_account_selector = False
                                st.success(f"✅ Cambiado a: {display}")
                                st.rerun()
                                break
                
                with col2:
                    if st.button("❌ Cancelar", use_container_width=True):
                        st.session_state.show_account_selector = False
                        st.rerun()
        
        st.divider()
        
        # Navigation
        st.markdown('<div class="nav-section-title">🧭 NAVEGACIÓN</div>', unsafe_allow_html=True)
        
        pages = [
            ("📊", "Resumen"),
            ("💰", "Facturación"),
            ("🎯", "Campañas"),
            ("📈", "Reportes"),
            ("🚨", "Alertas"),
            ("🤖", "Generador IA"),
            ("🎯", "Salud Keywords"),
            ("📢", "Salud Anuncios"),
            ("⚙️", "Configuración"),
        ]
        
        for icon, name in pages:
            st.markdown(f"""
            <div class="nav-item">
                <div class="nav-item-icon">{icon}</div>
                <div class="nav-item-text">{name}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # Quick Actions
        st.markdown('<div class="nav-section-title">⚡ ACCIONES RÁPIDAS</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Actualizar", use_container_width=True):
                try:
                    st.session_state.cache_manager.clear()
                except:
                    pass
                st.success("✅ Actualizado")
                st.rerun()
        
        with col2:
            if st.button("📊 Alertas", use_container_width=True):
                st.info("✓ Verificado")
        
        st.divider()
        
        # System Info
        st.markdown('<div class="nav-section-title">ℹ️ INFO DEL SISTEMA</div>', unsafe_allow_html=True)
        
        current_time = datetime.now().strftime("%H:%M:%S")
        
        st.markdown(f"""
        <div class="system-info">
            <div class="system-info-label">Hora</div>
            <div class="system-info-value">{current_time}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.customer_ids:
            st.markdown(f"""
            <div class="system-info">
                <div class="system-info-label">Cuentas</div>
                <div class="system-info-value">{len(st.session_state.customer_ids)}</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Cache stats
        if hasattr(st.session_state.cache_manager, 'get_stats'):
            try:
                cache_stats = st.session_state.cache_manager.get_stats()
                st.markdown(f"""
                <div class="system-info">
                    <div class="system-info-label">Cache</div>
                    <div class="system-info-value">{cache_stats.get('entries', 0)}</div>
                </div>
                """, unsafe_allow_html=True)
            except:
                pass


# ============================================================================
# ULTRA MODERN MAIN CONTENT - ESPAÑOL CON BOTONES DE NAVEGACIÓN
# ============================================================================

def render_ultra_modern_content():
    """Render ultra modern main content - Español con botones de navegación"""
    
    # Ultra modern header
    st.markdown("""
    <div class="ultra-header">
        <h1>🚀 GOOGLE ADS DASHBOARD 2030</h1>
        <p>Edición Ultra Moderna - Analítica Potenciada por IA</p>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.google_ads_client:
        st.warning("⚠️ API de Google Ads no conectada")
        return
    
    if st.session_state.selected_customer:
        account_names = get_account_names([st.session_state.selected_customer])
        account_name = account_names.get(st.session_state.selected_customer, 'Cuenta')
        
        # Glass card con info de cuenta
        st.markdown(f"""
        <div class="glass-card">
            <h2 style="margin-top: 0; color: var(--text-primary);">
                ✅ Cuenta Activa: <span style="background: var(--primary-gradient); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{account_name}</span>
            </h2>
            <p style="color: var(--text-secondary); font-family: 'Courier New', monospace;">
                Customer ID: {st.session_state.selected_customer}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # NAVEGACIÓN CON BOTONES MODERNOS
        st.markdown("""
        <div style="margin: 2rem 0;">
            <h2 style="color: var(--text-primary); margin-bottom: 1.5rem; font-size: 1.8rem; font-weight: 700;">
                🎯 Navegación Rápida
            </h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Botones de navegación en grid 2 columnas
        col1, col2 = st.columns(2)
        
        with col1:
            # Overview
            st.markdown("""
            <a href="/overview" target="_self" class="nav-button">
                <div class="nav-button-content">
                    <div class="nav-button-left">
                        <div class="nav-button-icon">📊</div>
                        <div class="nav-button-text">
                            <div class="nav-button-title">Resumen General</div>
                            <div class="nav-button-description">KPIs y métricas en tiempo real</div>
                        </div>
                    </div>
                    <div class="nav-button-arrow">→</div>
                </div>
            </a>
            """, unsafe_allow_html=True)
            
            # Campaigns
            st.markdown("""
            <a href="/campaigns" target="_self" class="nav-button">
                <div class="nav-button-content">
                    <div class="nav-button-left">
                        <div class="nav-button-icon">🎯</div>
                        <div class="nav-button-text">
                            <div class="nav-button-title">Campañas</div>
                            <div class="nav-button-description">Gestión y optimización de campañas</div>
                        </div>
                    </div>
                    <div class="nav-button-arrow">→</div>
                </div>
            </a>
            """, unsafe_allow_html=True)
            
            # Alerts
            st.markdown("""
            <a href="/alerts" target="_self" class="nav-button">
                <div class="nav-button-content">
                    <div class="nav-button-left">
                        <div class="nav-button-icon">🚨</div>
                        <div class="nav-button-text">
                            <div class="nav-button-title">Alertas</div>
                            <div class="nav-button-description">Gestión de alertas en tiempo real</div>
                        </div>
                    </div>
                    <div class="nav-button-arrow">→</div>
                </div>
            </a>
            """, unsafe_allow_html=True)
            
            # Keyword Health
            st.markdown("""
            <a href="/Keyword_Health" target="_self" class="nav-button">
                <div class="nav-button-content">
                    <div class="nav-button-left">
                        <div class="nav-button-icon">🎯</div>
                        <div class="nav-button-text">
                            <div class="nav-button-title">Salud de Keywords</div>
                            <div class="nav-button-description">Optimización y scoring de keywords</div>
                        </div>
                    </div>
                    <div class="nav-button-arrow">→</div>
                </div>
            </a>
            """, unsafe_allow_html=True)
        
        with col2:
            # Billing
            st.markdown("""
            <a href="/billing" target="_self" class="nav-button">
                <div class="nav-button-content">
                    <div class="nav-button-left">
                        <div class="nav-button-icon">💰</div>
                        <div class="nav-button-text">
                            <div class="nav-button-title">Facturación</div>
                            <div class="nav-button-description">Seguimiento de presupuesto y gastos</div>
                        </div>
                    </div>
                    <div class="nav-button-arrow">→</div>
                </div>
            </a>
            """, unsafe_allow_html=True)
            
            # Reports
            st.markdown("""
            <a href="/reports" target="_self" class="nav-button">
                <div class="nav-button-content">
                    <div class="nav-button-left">
                        <div class="nav-button-icon">📈</div>
                        <div class="nav-button-text">
                            <div class="nav-button-title">Reportes</div>
                            <div class="nav-button-description">Reportes personalizados y exportación</div>
                        </div>
                    </div>
                    <div class="nav-button-arrow">→</div>
                </div>
            </a>
            """, unsafe_allow_html=True)
            
            # AI Generator
            st.markdown("""
            <a href="/ai_ad_generator" target="_self" class="nav-button">
                <div class="nav-button-content">
                    <div class="nav-button-left">
                        <div class="nav-button-icon">🤖</div>
                        <div class="nav-button-text">
                            <div class="nav-button-title">Generador IA</div>
                            <div class="nav-button-description">Genera anuncios con OpenAI y Gemini</div>
                        </div>
                    </div>
                    <div class="nav-button-arrow">→</div>
                </div>
            </a>
            """, unsafe_allow_html=True)
            
            # Ad Health
            st.markdown("""
            <a href="/Ad_Health" target="_self" class="nav-button">
                <div class="nav-button-content">
                    <div class="nav-button-left">
                        <div class="nav-button-icon">📢</div>
                        <div class="nav-button-text">
                            <div class="nav-button-title">Salud de Anuncios</div>
                            <div class="nav-button-description">Optimización y quality scores</div>
                        </div>
                    </div>
                    <div class="nav-button-arrow">→</div>
                </div>
            </a>
            """, unsafe_allow_html=True)
        
        st.markdown("<br><br>", unsafe_allow_html=True)


# ============================================================================
# MAIN APPLICATION - ESPAÑOL
# ============================================================================

def main():
    """Main application with ultra modern design - Español"""
    try:
        initialize_session_state()
        
        auth = GoogleAdsAuth()
        # ============================================================================
        # ✅ CAPTURA AUTOMÁTICA DE CÓDIGO OAUTH
        # ============================================================================
        import time

        query_params = st.query_params

        if "code" in query_params and not auth.is_authenticated():
            st.markdown("""
            <div class="glass-card" style="text-align: center; padding: 3rem;">
                <h1>🔄 Procesando Autenticación</h1>
                <p style="color: var(--text-secondary);">Validando credenciales con Google Ads API...</p>
            </div>
            """, unsafe_allow_html=True)
            
            with st.spinner("⏳ Procesando código de autorización..."):
                # Obtener código
                auth_code = query_params.get("code")
                
                # Construir URL completa
                base_url = "https://appadsapi-miynrefpxescytebdgkkng.streamlit.app"
                full_url = f"{base_url}/?code={auth_code}"
                
                # Incluir scope si existe
                if "scope" in query_params:
                    scope = query_params.get("scope")
                    full_url += f"&scope={scope}"
                
                # Procesar callback
                try:
                    if auth.handle_callback(full_url):
                        st.balloons()
                        st.success("✅ ¡Autenticación completada exitosamente!")
                        
                        # Mostrar refresh token
                        if 'credentials' in st.session_state:
                            creds = st.session_state.credentials
                            if hasattr(creds, 'refresh_token') and creds.refresh_token:
                                st.markdown("""
                                <div class="glass-card">
                                    <h2 style="color: #4facfe; text-align: center;">🔑 Refresh Token Obtenido</h2>
                                    <p style="color: var(--text-secondary); text-align: center;">Guarda este token en tus Streamlit Secrets para mantener la autenticación permanente</p>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                st.code(f'refresh_token = "{creds.refresh_token}"', language='toml')
                                
                                st.info("""
                                **📋 Para mantener la autenticación permanente:**
                                1. Ve a tu app en Streamlit Cloud
                                2. Click en "⋮" → Settings → Secrets
                                3. Busca la sección `[google_ads]`
                                4. Actualiza o agrega la línea: `refresh_token = "..."`
                                5. Click en "Save"
                                6. Click en "Reboot app"
                                """)
                        
                        # Esperar 3 segundos para que el usuario vea el token
                        time.sleep(3)
                        
                        # Limpiar query params y recargar
                        st.query_params.clear()
                        st.rerun()
                    else:
                        st.error("❌ Error procesando la autenticación")
                        st.warning("Por favor, intenta el proceso de autenticación nuevamente")
                        
                        if st.button("🔄 Reintentar", type="primary"):
                            st.query_params.clear()
                            st.rerun()
                            
                except Exception as e:
                    st.error(f"❌ Error durante la autenticación: {str(e)}")
                    
                    with st.expander("🔍 Ver detalles técnicos del error"):
                        import traceback
                        st.code(traceback.format_exc())
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🔄 Volver a intentar", type="primary"):
                            st.query_params.clear()
                            st.rerun()
                    with col2:
                        if st.button("🏠 Ir al inicio"):
                            st.query_params.clear()
                            st.switch_page("app.py")
            
            # Detener ejecución aquí para no mostrar el resto de la app
            st.stop()
        if not auth.is_authenticated():
            # Auth screen
            st.markdown("""
            <div class="ultra-header">
                <h1>🔐 AUTENTICACIÓN REQUERIDA</h1>
                <p>Conectar con la API de Google Ads</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="glass-card">
                <h3 style="color: var(--text-primary);">📋 Instrucciones</h3>
                <ol style="color: var(--text-secondary); line-height: 2;">
                    <li>Haz clic en "Iniciar Autenticación"</li>
                    <li>Autoriza la aplicación en Google</li>
                    <li>Regresa a esta página y recarga (F5)</li>
                </ol>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🔑 Iniciar Autenticación", use_container_width=True, type="primary"):
                    try:
                        auth_url = auth.get_auth_url()
                        if auth_url:
                            st.success("✅ ¡Servidor de autenticación iniciado!")
                            st.markdown(f"### [**➡️ Haz clic aquí para autenticar**]({auth_url})")
                        else:
                            st.error("❌ Error generando URL de autorización")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            
            return
        
        if not st.session_state.get('services'):
            with st.spinner("Inicializando servicios..."):
                if not initialize_services():
                    st.error("Error inicializando servicios")
                    return
        
        if not st.session_state.get('customer_ids'):
            st.error("⚠️ No se encontraron cuentas de Google Ads")
            return
        
        if not st.session_state.get('selected_customer'):
            # Account selector
            st.markdown("""
            <div class="ultra-header">
                <h1>🎯 SELECCIONA UNA CUENTA</h1>
                <p>Elige una cuenta de Google Ads para continuar</p>
            </div>
            """, unsafe_allow_html=True)
            
            account_names = get_account_names(st.session_state.customer_ids)
            
            account_options = []
            for customer_id in st.session_state.customer_ids:
                name = account_names.get(customer_id, 'Cuenta')
                display_text = f"{customer_id} - {name}"
                account_options.append((display_text, customer_id))
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                selected_account_display = st.selectbox(
                    "Selecciona una cuenta:",
                    options=[opt[0] for opt in account_options],
                    key='account_selector'
                )
                
                # ✅ BOTÓN DE FORZAR ACTUALIZACIÓN AQUÍ
                if st.button("🔄 Forzar Actualización de Nombres", use_container_width=True):
                    st.session_state.account_cache_manager.clear_cache()
                    st.success("✅ Caché limpiado. Recargando...")
                    st.rerun()
                
                if st.button("✅ Continuar", use_container_width=True, type="primary"):
                    for display, customer_id in account_options:
                        if display == selected_account_display:
                            st.session_state.selected_customer = customer_id
                            st.success(f"✅ Seleccionada: {display}")
                            st.rerun()
                            break
            
            return
        
        # Render main app
        render_ultra_modern_sidebar()
        render_ultra_modern_content()
    
    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error(f"❌ Error: {e}")
        
        if st.button("🔄 Reiniciar"):
            st.rerun()


if __name__ == "__main__":
    main()