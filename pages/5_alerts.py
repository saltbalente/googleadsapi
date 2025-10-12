"""
Página de Alertas y Monitoreo - Diseño Ultra Moderno 2030
Sistema de alertas y monitoreo con glassmorphism dark theme en español
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta, date
import logging

from modules.auth import require_auth
from modules.models import AlertPriority, AlertStatus
from utils.logger import get_logger
from utils.formatters import format_currency, format_percentage, format_number, format_date

logger = get_logger(__name__)

# Configuración de página
st.set_page_config(
    page_title="Alertas - Dashboard Google Ads",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CSS PERSONALIZADO - ULTRA MODERNO 2030 ====================
def inject_ultra_modern_css():
    """Inyecta CSS ultra moderno con glassmorphism"""
    st.markdown("""
    <style>
    /* ==================== IMPORTS & VARIABLES ==================== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    :root {
        --primary: #667eea;
        --primary-dark: #764ba2;
        --success: #38ef7d;
        --warning: #ff9800;
        --danger: #f44336;
        --info: #4facfe;
        --bg-dark: #0a0a1a;
        --bg-darker: #050510;
        --glass-bg: rgba(255, 255, 255, 0.03);
        --glass-border: rgba(255, 255, 255, 0.08);
        --text-primary: #ffffff;
        --text-secondary: rgba(255, 255, 255, 0.7);
        --text-muted: rgba(255, 255, 255, 0.4);
    }
    
    /* ==================== GLOBAL ==================== */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, var(--bg-darker) 0%, var(--bg-dark) 50%, #1a1a2e 100%);
        background-attachment: fixed;
    }
    
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-image: 
            linear-gradient(rgba(102, 126, 234, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(102, 126, 234, 0.03) 1px, transparent 1px);
        background-size: 50px 50px;
        pointer-events: none;
        z-index: 0;
    }
    
    /* ==================== SIDEBAR ==================== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(10, 10, 26, 0.95) 0%, rgba(5, 5, 16, 0.98) 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-right: 1px solid var(--glass-border);
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
    }
    
    /* ==================== HEADERS ==================== */
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 900;
        letter-spacing: -2px;
        font-size: 3.5rem !important;
        margin-bottom: 0.5rem !important;
        text-align: center;
        animation: fadeInDown 0.8s ease-out;
    }
    
    h2 {
        color: var(--text-primary);
        font-weight: 700;
        letter-spacing: -1px;
        font-size: 1.8rem !important;
    }
    
    h3, h4 {
        color: var(--text-secondary);
        font-weight: 600;
        letter-spacing: -0.5px;
    }
    
    /* ==================== METRICS ==================== */
    [data-testid="metric-container"] {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
        border-radius: 20px;
        padding: 2rem 1.5rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    [data-testid="metric-container"]::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(102, 126, 234, 0.1) 0%, transparent 70%);
        opacity: 0;
        transition: opacity 0.4s;
    }
    
    [data-testid="metric-container"]:hover {
        transform: translateY(-8px);
        border-color: rgba(102, 126, 234, 0.4);
        box-shadow: 0 20px 60px rgba(102, 126, 234, 0.2);
    }
    
    [data-testid="metric-container"]:hover::before {
        opacity: 1;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 2.8rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: var(--text-secondary) !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }
    
    /* ==================== BUTTONS ==================== */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
        color: white;
        border: none;
        border-radius: 14px;
        padding: 0.85rem 2.5rem;
        font-weight: 600;
        font-size: 0.95rem;
        letter-spacing: 0.5px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.2);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }
    
    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 36px rgba(102, 126, 234, 0.5);
    }
    
    .stButton > button:hover::before {
        width: 300px;
        height: 300px;
    }
    
    /* ==================== INPUTS ==================== */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div,
    .stDateInput > div > div > input {
        background: var(--glass-bg) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        padding: 0.85rem 1.2rem !important;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div:focus-within,
    .stDateInput > div > div > input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15) !important;
        background: rgba(102, 126, 234, 0.05) !important;
    }
    
    /* ==================== DATAFRAMES ==================== */
    [data-testid="stDataFrame"] {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
    }
    
    [data-testid="stDataFrame"] table {
        color: var(--text-primary);
    }
    
    [data-testid="stDataFrame"] thead tr {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
    }
    
    [data-testid="stDataFrame"] tbody tr:hover {
        background: rgba(102, 126, 234, 0.1);
    }
    
    /* ==================== TABS ==================== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background: transparent;
        border-bottom: none;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        color: var(--text-secondary);
        font-weight: 600;
        padding: 1rem 2rem;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(102, 126, 234, 0.15);
        border-color: rgba(102, 126, 234, 0.4);
        color: var(--text-primary);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
        border-color: transparent;
        color: white;
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
    }
    
    /* ==================== EXPANDERS ==================== */
    .streamlit-expanderHeader {
        background: var(--glass-bg);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        color: var(--text-primary);
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: var(--primary);
        box-shadow: 0 4px 16px rgba(102, 126, 234, 0.2);
    }
    
    /* ==================== ALERTS ==================== */
    .stAlert {
        background: var(--glass-bg);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
    }
    
    /* ==================== CHECKBOX ==================== */
    .stCheckbox {
        background: var(--glass-bg);
        padding: 0.75rem 1rem;
        border-radius: 10px;
        border: 1px solid var(--glass-border);
        transition: all 0.3s ease;
    }
    
    .stCheckbox:hover {
        border-color: var(--primary);
        background: rgba(102, 126, 234, 0.05);
    }
    
    /* ==================== MULTISELECT ==================== */
    .stMultiSelect > div > div {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
    }
    
    /* ==================== SCROLLBAR ==================== */
    ::-webkit-scrollbar {
        width: 12px;
        height: 12px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-darker);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
        border-radius: 10px;
        border: 2px solid var(--bg-darker);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary) 100%);
    }
    
    /* ==================== TARJETAS DE ALERTA PERSONALIZADAS ==================== */
    .alert-card-high {
        background: linear-gradient(135deg, rgba(244, 67, 54, 0.1) 0%, rgba(244, 67, 54, 0.05) 100%);
        border-left: 4px solid #f44336;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(244, 67, 54, 0.2);
        box-shadow: 0 4px 16px rgba(244, 67, 54, 0.1);
        transition: all 0.3s ease;
    }
    
    .alert-card-high:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(244, 67, 54, 0.2);
    }
    
    .alert-card-medium {
        background: linear-gradient(135deg, rgba(255, 152, 0, 0.1) 0%, rgba(255, 152, 0, 0.05) 100%);
        border-left: 4px solid #ff9800;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 152, 0, 0.2);
        box-shadow: 0 4px 16px rgba(255, 152, 0, 0.1);
        transition: all 0.3s ease;
    }
    
    .alert-card-medium:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(255, 152, 0, 0.2);
    }
    
    .alert-card-low {
        background: linear-gradient(135deg, rgba(76, 175, 80, 0.1) 0%, rgba(76, 175, 80, 0.05) 100%);
        border-left: 4px solid #4caf50;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(76, 175, 80, 0.2);
        box-shadow: 0 4px 16px rgba(76, 175, 80, 0.1);
        transition: all 0.3s ease;
    }
    
    .alert-card-low:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(76, 175, 80, 0.2);
    }
    
    /* ==================== ANIMACIONES ==================== */
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes pulse {
        0%, 100% {
            box-shadow: 0 0 0 0 rgba(244, 67, 54, 0.4);
        }
        50% {
            box-shadow: 0 0 0 10px rgba(244, 67, 54, 0);
        }
    }
    
    [data-testid="metric-container"],
    [data-testid="stDataFrame"],
    .stTabs {
        animation: fadeIn 0.6s ease-out;
    }
    
    /* ==================== OCULTAR BRANDING STREAMLIT ==================== */
    #MainMenu, footer, header {
        visibility: hidden;
    }
    
    /* ==================== RESPONSIVE ==================== */
    @media (max-width: 768px) {
        h1 {
            font-size: 2rem !important;
        }
        
        [data-testid="metric-container"] {
            padding: 1.5rem 1rem;
        }
        
        [data-testid="stMetricValue"] {
            font-size: 2rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def render_hero_section():
    """Renderiza el hero header ultra moderno"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0 3rem 0; position: relative;">
        <div style="font-size: 5rem; margin-bottom: 1rem; 
                    animation: fadeInDown 0.8s ease-out, pulse 2s infinite;
                    filter: drop-shadow(0 0 20px rgba(244, 67, 54, 0.5));">
            🚨
        </div>
        <p style="font-size: 1rem; color: rgba(255, 255, 255, 0.6); 
                  font-weight: 500; letter-spacing: 3px; text-transform: uppercase;
                  margin-bottom: 0.5rem;">
            Sistema Inteligente de Alertas
        </p>
        <p style="font-size: 1.2rem; color: rgba(255, 255, 255, 0.8); 
                  font-weight: 400; max-width: 700px; margin: 0 auto;">
            Monitorea campañas, configura alertas y mantente informado sobre cambios críticos
        </p>
        <div style="width: 100px; height: 3px; 
                    background: linear-gradient(90deg, transparent, #f44336, transparent);
                    margin: 2rem auto 0 auto;"></div>
    </div>
    """, unsafe_allow_html=True)

@require_auth
def main():
    """Función principal de la página de alertas"""
    
    # Inyectar CSS moderno
    inject_ultra_modern_css()
    
    # Hero header
    render_hero_section()
    
    # Verificar si los servicios están disponibles
    if not st.session_state.get('google_ads_client') or not st.session_state.get('services'):
        st.error("❌ Servicios de Google Ads no inicializados. Verifica tu configuración.")
        return
    
    # Obtener cliente seleccionado
    selected_customer = st.session_state.get('selected_customer')
    if not selected_customer:
        st.warning("⚠️ No hay cuenta de cliente seleccionada. Selecciona una cuenta en el sidebar.")
        return
    
    # Servicios
    alert_service = st.session_state.services['alert']
    
    # Tabs principales
    tab1, tab2, tab3, tab4 = st.tabs(["🚨 Alertas Activas", "⚙️ Reglas de Alerta", "📊 Historial", "📈 Monitoreo"])
    
    with tab1:
        st.markdown("## 🚨 Alertas Activas")
        st.markdown("<p style='color: rgba(255,255,255,0.5); font-size: 0.9rem;'>Alertas activas que requieren tu atención</p>", unsafe_allow_html=True)
        
        try:
            with st.spinner("⏳ Cargando alertas activas..."):
                active_alerts = obtener_alertas_activas_ejemplo()
            
            if active_alerts:
                col1, col2, col3, col4 = st.columns(4)
                
                high_priority = len([a for a in active_alerts if a['prioridad'] == 'Alta'])
                medium_priority = len([a for a in active_alerts if a['prioridad'] == 'Media'])
                low_priority = len([a for a in active_alerts if a['prioridad'] == 'Baja'])
                total_alerts = len(active_alerts)
                
                with col1:
                    st.metric("🔴 Prioridad Alta", high_priority, 
                             delta=f"+{high_priority}" if high_priority > 0 else None,
                             delta_color="inverse")
                
                with col2:
                    st.metric("🟡 Prioridad Media", medium_priority)
                
                with col3:
                    st.metric("🟢 Prioridad Baja", low_priority)
                
                with col4:
                    st.metric("📊 Total Activas", total_alerts)
                
                st.markdown("---")
                
                col_filter, col_sort, col_action = st.columns([2, 2, 1])
                
                with col_filter:
                    priority_filter = st.multiselect(
                        "Filtrar por Prioridad:",
                        options=["Alta", "Media", "Baja"],
                        default=["Alta", "Media", "Baja"]
                    )
                
                with col_sort:
                    sort_by = st.selectbox(
                        "Ordenar por:",
                        options=["Prioridad", "Fecha", "Campaña", "Tipo de Alerta"]
                    )
                
                with col_action:
                    if st.button("🔄 Actualizar"):
                        st.rerun()
                
                filtered_alerts = [a for a in active_alerts if a['prioridad'] in priority_filter]
                
                for alert in filtered_alerts:
                    priority_class = {
                        'Alta': 'alert-card-high',
                        'Media': 'alert-card-medium',
                        'Baja': 'alert-card-low'
                    }
                    
                    priority_icons = {
                        'Alta': '🔴',
                        'Media': '🟡',
                        'Baja': '🟢'
                    }
                    
                    st.markdown(f"""
                    <div class="{priority_class[alert['prioridad']]}">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div style="flex: 1;">
                                <h3 style="margin: 0 0 0.5rem 0; color: var(--text-primary);">
                                    {priority_icons[alert['prioridad']]} {alert['titulo']}
                                </h3>
                                <p style="margin: 0.3rem 0; color: var(--text-secondary); font-size: 0.9rem;">
                                    <strong>Campaña:</strong> {alert['campana']}
                                </p>
                                <p style="margin: 0.3rem 0; color: var(--text-secondary); font-size: 0.9rem;">
                                    {alert['descripcion']}
                                </p>
                                <p style="margin: 0.5rem 0 0 0; color: var(--text-muted); font-size: 0.85rem;">
                                    ⏰ {alert['activada_en']}
                                </p>
                            </div>
                            <div style="text-align: right; min-width: 150px; margin-left: 2rem;">
                                <p style="margin: 0.2rem 0; color: var(--text-secondary); font-size: 0.9rem;">
                                    <strong>Tipo:</strong> {alert['tipo']}
                                </p>
                                <p style="margin: 0.2rem 0; color: var(--text-secondary); font-size: 0.9rem;">
                                    <strong>Valor:</strong> {alert['valor_actual']}
                                </p>
                                <p style="margin: 0.2rem 0; color: var(--text-secondary); font-size: 0.9rem;">
                                    <strong>Umbral:</strong> {alert['umbral']}
                                </p>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_ack, col_resolve, col_snooze = st.columns(3)
                    
                    with col_ack:
                        if st.button(f"✅ Reconocer", key=f"ack_{alert['id']}", use_container_width=True):
                            st.success(f"¡Alerta reconocida!")
                    
                    with col_resolve:
                        if st.button(f"✔️ Resolver", key=f"resolve_{alert['id']}", use_container_width=True):
                            st.success(f"¡Alerta resuelta!")
                    
                    with col_snooze:
                        if st.button(f"😴 Posponer", key=f"snooze_{alert['id']}", use_container_width=True):
                            st.info(f"¡Alerta pospuesta por 1 hora!")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
            
            else:
                st.success("🎉 ¡No hay alertas activas! Tus campañas están funcionando bien.")
                
                if st.button("👀 Mostrar Alertas de Ejemplo"):
                    st.session_state['show_sample_alerts'] = True
                    st.rerun()
        
        except Exception as e:
            logger.error(f"Error cargando alertas activas: {e}")
            st.error(f"❌ Error cargando alertas: {e}")
    
    with tab2:
        st.markdown("## ⚙️ Configuración de Reglas de Alerta")
        st.markdown("<p style='color: rgba(255,255,255,0.5); font-size: 0.9rem;'>Configura reglas de alerta personalizadas para tus campañas</p>", unsafe_allow_html=True)
        
        with st.expander("➕ Crear Nueva Regla de Alerta", expanded=False):
            with st.form("new_alert_rule"):
                st.markdown("**Configurar Nueva Regla de Alerta**")
                
                col_name, col_type = st.columns(2)
                
                with col_name:
                    rule_name = st.text_input("Nombre de la Regla:", placeholder="ej. Alerta de CPC Alto")
                
                with col_type:
                    alert_type = st.selectbox(
                        "Tipo de Alerta:",
                        options=[
                            "Agotamiento de Presupuesto",
                            "CTR Bajo",
                            "CPC Alto",
                            "Tasa de Conversión Baja",
                            "Campaña Pausada",
                            "Anomalía de Gasto",
                            "Métrica Personalizada"
                        ]
                    )
                
                col_metric, col_condition, col_threshold = st.columns(3)
                
                with col_metric:
                    if alert_type == "Métrica Personalizada":
                        metric = st.selectbox(
                            "Métrica:",
                            options=["Costo", "Clics", "Impresiones", "Conversiones", "CTR", "CPC"]
                        )
                    else:
                        metric = st.text_input("Métrica:", value=obtener_metrica_predeterminada(alert_type), disabled=True)
                
                with col_condition:
                    condition = st.selectbox(
                        "Condición:",
                        options=["Mayor que", "Menor que", "Igual a", "Cambio porcentual"]
                    )
                
                with col_threshold:
                    threshold = st.number_input("Valor Umbral:", min_value=0.0, step=0.1)
                
                col_priority, col_campaigns = st.columns(2)
                
                with col_priority:
                    priority = st.selectbox("Prioridad:", options=["Alta", "Media", "Baja"])
                
                with col_campaigns:
                    campaigns = st.multiselect(
                        "Aplicar a Campañas:",
                        options=["Todas las Campañas", "Campaña A", "Campaña B", "Campaña C"],
                        default=["Todas las Campañas"]
                    )
                
                st.markdown("**Configuración de Notificaciones**")
                
                col_email, col_frequency = st.columns(2)
                
                with col_email:
                    email_notifications = st.checkbox("Notificaciones por Email", value=True)
                    if email_notifications:
                        email_addresses = st.text_input("Direcciones de Email (separadas por coma):")
                
                with col_frequency:
                    notification_frequency = st.selectbox(
                        "Frecuencia de Notificación:",
                        options=["Inmediata", "Cada hora", "Diaria", "Semanal"]
                    )
                
                if st.form_submit_button("✅ Crear Regla de Alerta", use_container_width=True):
                    st.success(f"✅ ¡Regla de alerta '{rule_name}' creada exitosamente!")
                    st.info("La regla estará activa en 5 minutos.")
        
        st.markdown("### 📋 Reglas de Alerta Existentes")
        
        existing_rules = obtener_reglas_alerta_ejemplo()
        
        if existing_rules:
            for rule in existing_rules:
                with st.expander(f"📏 {rule['nombre']} ({rule['estado']})"):
                    col_info, col_actions = st.columns([3, 1])
                    
                    with col_info:
                        st.markdown(f"**Tipo:** {rule['tipo']}")
                        st.markdown(f"**Condición:** {rule['condicion']}")
                        st.markdown(f"**Umbral:** {rule['umbral']}")
                        st.markdown(f"**Prioridad:** {rule['prioridad']}")
                        st.markdown(f"**Campañas:** {', '.join(rule['campanas'])}")
                        st.markdown(f"**Creada:** {rule['creada_en']}")
                        st.markdown(f"**Última Activación:** {rule['ultima_activacion']}")
                    
                    with col_actions:
                        if rule['estado'] == 'Activa':
                            if st.button(f"⏸️ Desactivar", key=f"disable_{rule['id']}", use_container_width=True):
                                st.info(f"¡Regla desactivada!")
                        else:
                            if st.button(f"▶️ Activar", key=f"enable_{rule['id']}", use_container_width=True):
                                st.success(f"¡Regla activada!")
                        
                        if st.button(f"✏️ Editar", key=f"edit_{rule['id']}", use_container_width=True):
                            st.info(f"Editando regla...")
                        
                        if st.button(f"🗑️ Eliminar", key=f"delete_{rule['id']}", use_container_width=True):
                            st.warning(f"¡Regla eliminada!")
        
        else:
            st.info("📋 No hay reglas de alerta configuradas. ¡Crea tu primera regla arriba!")
    
    with tab3:
        st.markdown("## 📊 Historial de Alertas")
        st.markdown("<p style='color: rgba(255,255,255,0.5); font-size: 0.9rem;'>Datos históricos y tendencias</p>", unsafe_allow_html=True)
        
        col_date1, col_date2, col_filter_hist = st.columns(3)
        
        with col_date1:
            start_date = st.date_input("Fecha Inicio:", value=date.today() - timedelta(days=30))
        
        with col_date2:
            end_date = st.date_input("Fecha Fin:", value=date.today())
        
        with col_filter_hist:
            status_filter = st.multiselect(
                "Filtrar por Estado:",
                options=["Resuelta", "Reconocida", "Pospuesta", "Expirada"],
                default=["Resuelta", "Reconocida"]
            )
        
        alert_history = obtener_historial_alertas_ejemplo()
        
        if alert_history:
            st.markdown("### 📈 Tendencias de Alertas")
            
            trend_data = []
            for i in range(30):
                current_date = datetime.now() - timedelta(days=29-i)
                import random
                random.seed(i)
                trend_data.append({
                    'Fecha': current_date.strftime('%Y-%m-%d'),
                    'Prioridad Alta': random.randint(0, 5),
                    'Prioridad Media': random.randint(1, 8),
                    'Prioridad Baja': random.randint(2, 10)
                })
            
            df_trends = pd.DataFrame(trend_data)
            
            fig_trends = px.line(
                df_trends,
                x='Fecha',
                y=['Prioridad Alta', 'Prioridad Media', 'Prioridad Baja'],
                labels={'value': 'Número de Alertas', 'variable': 'Nivel de Prioridad'}
            )
            
            fig_trends.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='rgba(255,255,255,0.8)'),
                margin=dict(l=0, r=0, t=0, b=0)
            )
            
            st.plotly_chart(fig_trends, use_container_width=True)
            
            col_dist1, col_dist2 = st.columns(2)
            
            with col_dist1:
                priority_counts = {'Alta': 15, 'Media': 32, 'Baja': 28}
                
                fig_priority = px.pie(
                    values=list(priority_counts.values()),
                    names=list(priority_counts.keys()),
                    color_discrete_map={'Alta': '#f44336', 'Media': '#ff9800', 'Baja': '#4caf50'}
                )
                
                fig_priority.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='rgba(255,255,255,0.8)'),
                    margin=dict(l=0, r=0, t=20, b=0)
                )
                
                st.plotly_chart(fig_priority, use_container_width=True)
            
            with col_dist2:
                type_counts = {
                    'Agotamiento Presupuesto': 12,
                    'CTR Bajo': 18,
                    'CPC Alto': 15,
                    'Campaña Pausada': 8,
                    'Anomalía Gasto': 10,
                    'Otro': 12
                }
                
                fig_types = px.bar(
                    x=list(type_counts.keys()),
                    y=list(type_counts.values()),
                    labels={'x': 'Tipo de Alerta', 'y': 'Cantidad'}
                )
                
                fig_types.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='rgba(255,255,255,0.8)'),
                    xaxis=dict(tickangle=45),
                    margin=dict(l=0, r=0, t=20, b=0)
                )
                
                st.plotly_chart(fig_types, use_container_width=True)
            
            st.markdown("### 📋 Detalles del Historial de Alertas")
            
            filtered_history = [a for a in alert_history if a['estado'] in status_filter]
            
            if filtered_history:
                df_history = pd.DataFrame(filtered_history)
                
                st.dataframe(
                    df_history[['activada_en', 'titulo', 'tipo', 'prioridad', 'estado', 'resuelta_en']],
                    use_container_width=True,
                    hide_index=True
                )
                
                if st.button("📊 Exportar Historial de Alertas"):
                    csv_data = df_history.to_csv(index=False)
                    st.download_button(
                        label="💾 Descargar CSV",
                        data=csv_data,
                        file_name=f"historial_alertas_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
            
            else:
                st.info("📊 No se encontró historial de alertas con los filtros seleccionados.")
        
        else:
            st.info("📊 No hay historial de alertas disponible.")
    
    with tab4:
        st.markdown("## 📈 Monitoreo en Tiempo Real")
        st.markdown("<p style='color: rgba(255,255,255,0.5); font-size: 0.9rem;'>Monitorea la salud de las campañas en tiempo real</p>", unsafe_allow_html=True)
        
        col_mon1, col_mon2 = st.columns(2)
        
        with col_mon1:
            st.markdown("### 🎯 Puntuación de Salud de Campaña")
            
            health_score = 85
            
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=health_score,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Puntuación General de Salud", 'font': {'color': 'rgba(255,255,255,0.8)'}},
                delta={'reference': 80},
                gauge={
                    'axis': {'range': [None, 100], 'tickcolor': 'rgba(255,255,255,0.5)'},
                    'bar': {'color': "#667eea"},
                    'steps': [
                        {'range': [0, 50], 'color': "rgba(244, 67, 54, 0.3)"},
                        {'range': [50, 80], 'color': "rgba(255, 152, 0, 0.3)"}
                    ],
                    'threshold': {
                        'line': {'color': "#38ef7d", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            
            fig_gauge.update_layout(
                height=300,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='rgba(255,255,255,0.8)'),
                margin=dict(l=20, r=20, t=50, b=20)
            )
            
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        with col_mon2:
            st.markdown("### 📊 Estado de Métricas Clave")
            
            metrics_status = [
                {'metrica': 'Utilización de Presupuesto', 'valor': '78%', 'estado': 'Bueno', 'color': '#38ef7d'},
                {'metrica': 'CTR Promedio', 'valor': '3.2%', 'estado': 'Bueno', 'color': '#38ef7d'},
                {'metrica': 'Costo por Clic', 'valor': '$2.45', 'estado': 'Advertencia', 'color': '#ff9800'},
                {'metrica': 'Tasa de Conversión', 'valor': '4.8%', 'estado': 'Excelente', 'color': '#38ef7d'},
                {'metrica': 'Quality Score', 'valor': '7.2/10', 'estado': 'Bueno', 'color': '#38ef7d'}
            ]
            
            for metric in metrics_status:
                status_icons = {'Bueno': '✅', 'Advertencia': '⚠️', 'Excelente': '🎉', 'Crítico': '🚨'}
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(102, 126, 234, 0.02) 100%);
                            padding: 1rem; border-radius: 10px; margin-bottom: 0.75rem;
                            border-left: 3px solid {metric['color']};
                            backdrop-filter: blur(10px);
                            border: 1px solid rgba(255, 255, 255, 0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong style="color: var(--text-primary);">
                                {status_icons.get(metric['estado'], '📊')} {metric['metrica']}
                            </strong>
                        </div>
                        <div style="text-align: right;">
                            <span style="font-size: 1.3em; color: {metric['color']}; font-weight: 700;">
                                {metric['valor']}
                            </span><br>
                            <span style="font-size: 0.85em; color: var(--text-muted);">
                                {metric['estado']}
                            </span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("### 🔔 Feed de Alertas en Tiempo Real")
        
        if 'alert_feed' not in st.session_state:
            st.session_state.alert_feed = []
        
        if st.button("🔄 Actualizar Feed", use_container_width=False):
            import random
            new_alert = {
                'hora': datetime.now().strftime('%H:%M:%S'),
                'mensaje': random.choice([
                    "El CTR de la campaña 'Búsqueda de Marca' cayó por debajo del 2%",
                    "El presupuesto de 'Campaña de Producto' está agotado al 80%",
                    "Se detectó nueva keyword de alto rendimiento en 'Campaña Shopping'",
                    "El CPC aumentó un 15% en 'Campaña de Retargeting'"
                ]),
                'tipo': random.choice(['advertencia', 'info', 'exito'])
            }
            st.session_state.alert_feed.insert(0, new_alert)
            st.session_state.alert_feed = st.session_state.alert_feed[:10]
        
        if st.session_state.alert_feed:
            for alert in st.session_state.alert_feed:
                type_colors = {
                    'advertencia': 'rgba(255, 152, 0, 0.1)',
                    'info': 'rgba(79, 172, 254, 0.1)',
                    'exito': 'rgba(56, 239, 125, 0.1)'
                }
                
                type_borders = {
                    'advertencia': '#ff9800',
                    'info': '#4facfe',
                    'exito': '#38ef7d'
                }
                
                type_icons = {
                    'advertencia': '⚠️',
                    'info': 'ℹ️',
                    'exito': '✅'
                }
                
                st.markdown(f"""
                <div style="background: {type_colors.get(alert['tipo'], 'rgba(255,255,255,0.05)')}; 
                            padding: 1rem; border-radius: 10px; margin-bottom: 0.75rem;
                            border-left: 3px solid {type_borders.get(alert['tipo'], '#667eea')};
                            backdrop-filter: blur(10px);
                            border: 1px solid rgba(255, 255, 255, 0.05);">
                    <strong style="color: var(--text-primary);">
                        {type_icons.get(alert['tipo'], '📊')} {alert['hora']}
                    </strong><br>
                    <span style="color: var(--text-secondary);">
                        {alert['mensaje']}
                    </span>
                </div>
                """, unsafe_allow_html=True)
        
        else:
            st.info("🔔 No hay alertas recientes. Haz clic en 'Actualizar Feed' para buscar actualizaciones.")
        
        with st.expander("⚙️ Configuración de Monitoreo"):
            st.markdown("**Configurar Monitoreo en Tiempo Real**")
            
            col_refresh, col_notifications = st.columns(2)
            
            with col_refresh:
                auto_refresh = st.checkbox("Actualización automática cada 30 segundos", value=False)
                refresh_interval = st.selectbox("Intervalo de Actualización:", ["30 segundos", "1 minuto", "5 minutos"])
            
            with col_notifications:
                browser_notifications = st.checkbox("Notificaciones del navegador", value=True)
                sound_alerts = st.checkbox("Alertas sonoras", value=False)
            
            if st.button("💾 Guardar Configuración de Monitoreo", use_container_width=True):
                st.success("✅ ¡Configuración de monitoreo guardada!")

def obtener_alertas_activas_ejemplo():
    """Genera alertas activas de ejemplo"""
    return [
        {
            'id': 1,
            'titulo': 'Advertencia de Agotamiento de Presupuesto',
            'campana': 'Campaña de Marca A',
            'descripcion': 'El presupuesto de la campaña está agotado al 85% y quedan 5 días en el mes',
            'tipo': 'Agotamiento de Presupuesto',
            'prioridad': 'Alta',
            'valor_actual': '85%',
            'umbral': '80%',
            'activada_en': '2024-01-20 14:30:00'
        },
        {
            'id': 2,
            'titulo': 'Alerta de CTR Bajo',
            'campana': 'Campaña de Producto B',
            'descripcion': 'La tasa de clics ha caído por debajo del umbral',
            'tipo': 'CTR Bajo',
            'prioridad': 'Media',
            'valor_actual': '1.8%',
            'umbral': '2.0%',
            'activada_en': '2024-01-20 12:15:00'
        },
        {
            'id': 3,
            'titulo': 'Alerta de CPC Alto',
            'campana': 'Campaña de Búsqueda D',
            'descripcion': 'El costo por clic ha aumentado significativamente',
            'tipo': 'CPC Alto',
            'prioridad': 'Media',
            'valor_actual': '$4.50',
            'umbral': '$4.00',
            'activada_en': '2024-01-20 10:45:00'
        },
        {
            'id': 4,
            'titulo': 'Campaña Pausada',
            'campana': 'Campaña Display E',
            'descripcion': 'La campaña fue pausada automáticamente debido al agotamiento del presupuesto',
            'tipo': 'Campaña Pausada',
            'prioridad': 'Alta',
            'valor_actual': 'Pausada',
            'umbral': 'Activa',
            'activada_en': '2024-01-20 09:20:00'
        }
    ]

def obtener_reglas_alerta_ejemplo():
    """Genera reglas de alerta de ejemplo"""
    return [
        {
            'id': 1,
            'nombre': 'Alerta de Agotamiento de Presupuesto',
            'tipo': 'Agotamiento de Presupuesto',
            'condicion': 'Mayor que 80%',
            'umbral': '80%',
            'prioridad': 'Alta',
            'campanas': ['Todas las Campañas'],
            'estado': 'Activa',
            'creada_en': '2024-01-15',
            'ultima_activacion': '2024-01-20 14:30:00'
        },
        {
            'id': 2,
            'nombre': 'Advertencia de CTR Bajo',
            'tipo': 'CTR Bajo',
            'condicion': 'Menor que 2%',
            'umbral': '2%',
            'prioridad': 'Media',
            'campanas': ['Campaña A', 'Campaña B'],
            'estado': 'Activa',
            'creada_en': '2024-01-10',
            'ultima_activacion': '2024-01-20 12:15:00'
        },
        {
            'id': 3,
            'nombre': 'Alerta de CPC Alto',
            'tipo': 'CPC Alto',
            'condicion': 'Mayor que $4.00',
            'umbral': '$4.00',
            'prioridad': 'Media',
            'campanas': ['Campaña de Búsqueda D'],
            'estado': 'Inactiva',
            'creada_en': '2024-01-08',
            'ultima_activacion': '2024-01-18 16:20:00'
        }
    ]

def obtener_historial_alertas_ejemplo():
    """Genera historial de alertas de ejemplo"""
    return [
        {
            'activada_en': '2024-01-20 14:30:00',
            'titulo': 'Advertencia de Agotamiento de Presupuesto',
            'tipo': 'Agotamiento de Presupuesto',
            'prioridad': 'Alta',
            'estado': 'Reconocida',
            'resuelta_en': None
        },
        {
            'activada_en': '2024-01-19 16:45:00',
            'titulo': 'Tasa de Conversión Baja',
            'tipo': 'Tasa de Conversión Baja',
            'prioridad': 'Media',
            'estado': 'Resuelta',
            'resuelta_en': '2024-01-20 09:15:00'
        },
        {
            'activada_en': '2024-01-18 11:20:00',
            'titulo': 'Caída en Rendimiento de Campaña',
            'tipo': 'Rendimiento',
            'prioridad': 'Alta',
            'estado': 'Resuelta',
            'resuelta_en': '2024-01-19 14:30:00'
        }
    ]

def obtener_metrica_predeterminada(tipo_alerta):
    """Obtiene la métrica predeterminada para el tipo de alerta"""
    defaults = {
        "Agotamiento de Presupuesto": "% de Utilización de Presupuesto",
        "CTR Bajo": "Tasa de Clics",
        "CPC Alto": "Costo por Clic",
        "Tasa de Conversión Baja": "Tasa de Conversión",
        "Campaña Pausada": "Estado de Campaña",
        "Anomalía de Gasto": "Gasto Diario"
    }
    return defaults.get(tipo_alerta, "Métrica Personalizada")

if __name__ == "__main__":
    main()