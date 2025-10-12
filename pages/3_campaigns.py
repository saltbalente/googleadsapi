"""
Página de Rendimiento de Campañas - Diseño Ultra Moderno 2030
Sistema completo de gestión con modales anidados para edición
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta, date
import logging
import time
from typing import List, Dict, Optional
import json
from utils.ai_ad_manager import AIAdManager
from modules.auth import require_auth
from utils.logger import get_logger
from utils.formatters import format_currency, format_percentage, format_number, format_date
from services.campaign_actions import CampaignActionsService
from services.report_service import ReportService
from modules.models import ReportConfig


# ========== AGREGAR DESPUÉS DE LOS IMPORTS ==========

def mark_ad_as_used(ad_id: str, campaign_id: str = None, ad_group_id: str = None):
    """
    Marca un anuncio generado por IA como usado en una campaña
    
    Args:
        ad_id: ID del anuncio
        campaign_id: ID de la campaña (opcional)
        ad_group_id: ID del grupo de anuncios (opcional)
    """
    if 'pending_ai_ads' not in st.session_state:
        logger.warning("⚠️ No hay anuncios pendientes en session state")
        return
    
    for ad in st.session_state.pending_ai_ads:
        if ad['id'] == ad_id:
            ad['used'] = True
            ad['campaign_id'] = campaign_id
            ad['ad_group_id'] = ad_group_id
            ad['used_at'] = datetime.now().isoformat()
            logger.info(f"✅ Anuncio {ad_id} marcado como usado")
            return
    
    logger.warning(f"⚠️ Anuncio {ad_id} no encontrado en pendientes")


def get_pending_ads_count() -> int:
    """Obtiene el número de anuncios de IA disponibles"""
    if 'pending_ai_ads' not in st.session_state:
        return 0
    
    return len([ad for ad in st.session_state.pending_ai_ads if not ad.get('used', False)])

# ========== FIN DE FUNCIONES AGREGADAS ==========


logger = get_logger(__name__)

# Configuración de página
st.set_page_config(
    page_title="Campañas - Dashboard Google Ads",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== MODELOS DE DATOS ====================

class AdCreative:
    """Modelo para un anuncio creativo"""
    def __init__(self):
        self.headlines = [""] * 15  # 15 títulos max 30 caracteres
        self.descriptions = [""] * 4  # 4 descripciones max 90 caracteres
        self.final_url = ""
        self.path1 = ""
        self.path2 = ""
    
    def to_dict(self):
        return {
            'headlines': [h for h in self.headlines if h],
            'descriptions': [d for d in self.descriptions if d],
            'final_url': self.final_url,
            'path1': self.path1,
            'path2': self.path2
        }
    
    def is_valid(self):
        """Valida que el anuncio tenga al menos 3 títulos y 2 descripciones"""
        valid_headlines = [h for h in self.headlines if h.strip()]
        valid_descriptions = [d for d in self.descriptions if d.strip()]
        return len(valid_headlines) >= 3 and len(valid_descriptions) >= 2 and self.final_url

class AdGroup:
    """Modelo para un grupo de anuncios"""
    def __init__(self, name: str = ""):
        self.name = name
        self.cpc_bid_micros = 1000000  # $1.00 USD default
        self.ads: List[AdCreative] = []
        self.keywords: List[Dict] = []  # [{'text': 'keyword', 'match_type': 'BROAD'}]
        self.status = "ENABLED"
    
    def to_dict(self):
        return {
            'name': self.name,
            'cpc_bid_micros': self.cpc_bid_micros,
            'ads': [ad.to_dict() for ad in self.ads],
            'keywords': self.keywords,
            'status': self.status
        }
    
    def is_valid(self):
        """Valida que el grupo tenga nombre, al menos 1 anuncio válido y keywords"""
        return (self.name.strip() and 
                len(self.ads) > 0 and 
                all(ad.is_valid() for ad in self.ads) and
                len(self.keywords) > 0)

# ==================== ESTADO DE SESIÓN ====================

def init_session_state():
    """Inicializa variables de estado de sesión"""
    if 'show_edit_modal' not in st.session_state:
        st.session_state.show_edit_modal = False
    if 'selected_campaign_for_edit' not in st.session_state:
        st.session_state.selected_campaign_for_edit = None
    if 'show_create_ad_group_modal' not in st.session_state:
        st.session_state.show_create_ad_group_modal = False
    if 'current_ad_group' not in st.session_state:
        st.session_state.current_ad_group = None
    if 'show_ad_editor_modal' not in st.session_state:
        st.session_state.show_ad_editor_modal = False
    if 'current_ad_index' not in st.session_state:
        st.session_state.current_ad_index = 0
    if 'pending_ad_groups' not in st.session_state:
        st.session_state.pending_ad_groups = []
    # Variables para el modal de generador de IA para grupos existentes
    if 'show_ai_generator_modal_for_group' not in st.session_state:
        st.session_state.show_ai_generator_modal_for_group = False
    if 'ai_gen_ad_group_id' not in st.session_state:
        st.session_state.ai_gen_ad_group_id = None
    if 'ai_gen_ad_group_name' not in st.session_state:
        st.session_state.ai_gen_ad_group_name = None
    if 'ai_gen_keywords' not in st.session_state:
        st.session_state.ai_gen_keywords = []

init_session_state()

# ==================== CSS PERSONALIZADO - ULTRA MODERNO 2030 ====================
def inject_ultra_modern_css():
    """Inyecta CSS ultra moderno con glassmorphism y modales"""
    st.markdown("""
    <style>
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
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(10, 10, 26, 0.95) 0%, rgba(5, 5, 16, 0.98) 100%);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-right: 1px solid var(--glass-border);
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
    }
    
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
    
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div,
    .stTextArea > div > div > textarea {
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
    .stTextArea > div > div > textarea:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15) !important;
        background: rgba(102, 126, 234, 0.05) !important;
    }
    
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
    
    .stMultiSelect > div > div {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
    }
    
    /* Modal Styles */
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.8);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        z-index: 9998;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: fadeIn 0.3s ease-out;
    }
    
    .modal-container {
        background: linear-gradient(135deg, rgba(10, 10, 26, 0.95) 0%, rgba(5, 5, 16, 0.98) 100%);
        border: 1px solid var(--glass-border);
        border-radius: 20px;
        padding: 2rem;
        max-width: 90vw;
        max-height: 90vh;
        overflow-y: auto;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8);
        z-index: 9999;
        animation: slideUp 0.3s ease-out;
    }
    
    .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--glass-border);
    }
    
    .modal-title {
        font-size: 1.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .modal-close {
        background: rgba(244, 67, 54, 0.2);
        border: 1px solid rgba(244, 67, 54, 0.4);
        border-radius: 50%;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .modal-close:hover {
        background: rgba(244, 67, 54, 0.4);
        transform: rotate(90deg);
    }
    
    /* Insight Cards */
    .insight-card-warning {
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
    
    .insight-card-warning:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(255, 152, 0, 0.2);
    }
    
    .insight-card-success {
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
    
    .insight-card-success:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(76, 175, 80, 0.2);
    }
    
    .insight-card-info {
        background: linear-gradient(135deg, rgba(79, 172, 254, 0.1) 0%, rgba(79, 172, 254, 0.05) 100%);
        border-left: 4px solid #4facfe;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(79, 172, 254, 0.2);
        box-shadow: 0 4px 16px rgba(79, 172, 254, 0.1);
        transition: all 0.3s ease;
    }
    
    .insight-card-info:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(79, 172, 254, 0.2);
    }
    
    .insight-card-danger {
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
    
    .insight-card-danger:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 24px rgba(244, 67, 54, 0.2);
    }
    
    /* Character Counter */
    .char-counter {
        font-size: 0.75rem;
        color: var(--text-muted);
        text-align: right;
        margin-top: 0.25rem;
    }
    
    .char-counter.warning {
        color: var(--warning);
    }
    
    .char-counter.danger {
        color: var(--danger);
    }
    
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
    
    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(50px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    [data-testid="metric-container"],
    [data-testid="stDataFrame"] {
        animation: fadeIn 0.6s ease-out;
    }
    
    #MainMenu, footer, header {
        visibility: hidden;
    }
    
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
        
        .modal-container {
            max-width: 95vw;
            padding: 1rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# ==================== FUNCIONES DE MODALES Y EDITORES ====================

def render_ad_editor_modal(ad_index: int = 0):
    """
    Renderiza modal para crear/editar un anuncio
    15 títulos (max 30 char) + 4 descripciones (max 90 char)
    """
    if not st.session_state.current_ad_group:
        return
    
    st.markdown("### 📝 Editor de Anuncio Responsivo de Búsqueda")
    st.markdown(f"<p style='color: rgba(255,255,255,0.5);'>Anuncio #{ad_index + 1} - Grupo: {st.session_state.current_ad_group.name}</p>", unsafe_allow_html=True)
    
    # Obtener o crear anuncio
    if ad_index < len(st.session_state.current_ad_group.ads):
        current_ad = st.session_state.current_ad_group.ads[ad_index]
    else:
        current_ad = AdCreative()
        st.session_state.current_ad_group.ads.append(current_ad)
    
    st.markdown("---")
    
    # ===== SECCIÓN: URL Final =====
    st.markdown("#### 🔗 URL de Destino")
    
    col_url1, col_url2 = st.columns([2, 1])
    
    with col_url1:
        final_url = st.text_input(
            "URL Final *",
            value=current_ad.final_url,
            placeholder="https://www.ejemplo.com/pagina-destino",
            help="URL a la que dirigirán los usuarios al hacer clic",
            key=f"final_url_{ad_index}"
        )
        current_ad.final_url = final_url
    
    with col_url2:
        col_path1, col_path2 = st.columns(2)
        with col_path1:
            path1 = st.text_input(
                "Ruta 1",
                value=current_ad.path1,
                max_chars=15,
                placeholder="producto",
                help="Aparece en la URL mostrada (max 15 caracteres)",
                key=f"path1_{ad_index}"
            )
            current_ad.path1 = path1
        
        with col_path2:
            path2 = st.text_input(
                "Ruta 2",
                value=current_ad.path2,
                max_chars=15,
                placeholder="oferta",
                help="Aparece en la URL mostrada (max 15 caracteres)",
                key=f"path2_{ad_index}"
            )
            current_ad.path2 = path2
    
    if final_url and path1 and path2:
        st.caption(f"Vista previa URL: {final_url.split('//')[1].split('/')[0]}/{path1}/{path2}")
    
    st.markdown("---")
    
    # ===== SECCIÓN: Títulos (15 espacios) =====
    st.markdown("#### 📰 Títulos (Máx 30 caracteres cada uno)")
    st.caption("⭐ Mínimo 3 títulos requeridos | Se mostrarán hasta 3 títulos en cada anuncio")
    
    # Dividir en 3 columnas de 5 títulos cada una
    for row in range(5):
        cols = st.columns(3)
        for col_idx, col in enumerate(cols):
            headline_idx = row * 3 + col_idx
            with col:
                headline = st.text_input(
                    f"Título {headline_idx + 1}",
                    value=current_ad.headlines[headline_idx],
                    max_chars=30,
                    placeholder=f"Título {headline_idx + 1}...",
                    key=f"headline_{ad_index}_{headline_idx}"
                )
                current_ad.headlines[headline_idx] = headline
                
                # Contador de caracteres
                char_count = len(headline)
                char_class = "danger" if char_count > 30 else ("warning" if char_count > 25 else "")
                st.markdown(f"<div class='char-counter {char_class}'>{char_count}/30</div>", unsafe_allow_html=True)
    
    # Mostrar resumen de títulos válidos
    valid_headlines = [h for h in current_ad.headlines if h.strip()]
    if len(valid_headlines) < 3:
        st.warning(f"⚠️ Tienes {len(valid_headlines)} títulos. Mínimo 3 requeridos.")
    else:
        st.success(f"✅ {len(valid_headlines)} títulos válidos")
    
    st.markdown("---")
    
    # ===== SECCIÓN: Descripciones (4 espacios) =====
    st.markdown("#### 📝 Descripciones (Máx 90 caracteres cada una)")
    st.caption("⭐ Mínimo 2 descripciones requeridas | Se mostrarán hasta 2 descripciones en cada anuncio")
    
    for desc_idx in range(4):
        description = st.text_area(
            f"Descripción {desc_idx + 1}",
            value=current_ad.descriptions[desc_idx],
            max_chars=90,
            height=80,
            placeholder=f"Descripción {desc_idx + 1}...",
            key=f"description_{ad_index}_{desc_idx}"
        )
        current_ad.descriptions[desc_idx] = description
        
        # Contador de caracteres
        char_count = len(description)
        char_class = "danger" if char_count > 90 else ("warning" if char_count > 80 else "")
        st.markdown(f"<div class='char-counter {char_class}'>{char_count}/90</div>", unsafe_allow_html=True)
    
    # Mostrar resumen de descripciones válidas
    valid_descriptions = [d for d in current_ad.descriptions if d.strip()]
    if len(valid_descriptions) < 2:
        st.warning(f"⚠️ Tienes {len(valid_descriptions)} descripciones. Mínimo 2 requeridas.")
    else:
        st.success(f"✅ {len(valid_descriptions)} descripciones válidas")
    
    st.markdown("---")
    
    # ===== VISTA PREVIA DEL ANUNCIO =====
    st.markdown("#### 👁️ Vista Previa del Anuncio")
    
    if current_ad.is_valid():
        preview_headlines = [h for h in current_ad.headlines if h.strip()][:3]
        preview_descriptions = [d for d in current_ad.descriptions if d.strip()][:2]
        
        st.markdown(f"""
        <div class="insight-card-success">
            <div style="margin-bottom: 0.5rem;">
                <span style="color: #38ef7d; font-size: 0.75rem;">Anuncio</span>
            </div>
            <div style="font-size: 1.2rem; font-weight: 600; color: #667eea; margin-bottom: 0.5rem;">
                {' | '.join(preview_headlines)}
            </div>
            <div style="font-size: 0.85rem; color: #38ef7d; margin-bottom: 0.5rem;">
                {final_url.split('//')[1] if '//' in final_url else final_url}
            </div>
            <div style="font-size: 0.9rem; color: rgba(255,255,255,0.8);">
                {' '.join(preview_descriptions)}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("💡 Completa los campos requeridos para ver la vista previa")
    
    # Botones de acción
    col_save, col_cancel = st.columns(2)
    
    with col_save:
        if st.button("✅ Guardar Anuncio", use_container_width=True, type="primary", disabled=not current_ad.is_valid(), key=f"save_ad_{ad_index}_btn"):
            st.session_state.show_ad_editor_modal = False
            st.success("✅ Anuncio guardado correctamente")
            time.sleep(1)
            st.rerun()

    with col_cancel:
        if st.button("❌ Cancelar", use_container_width=True, key=f"cancel_ad_{ad_index}_btn"):  # ✅ KEY AGREGADO
            st.session_state.show_ad_editor_modal = False
            st.rerun()


def render_keywords_editor():
    """Renderiza el editor de palabras clave"""
    if not st.session_state.current_ad_group:
        st.error("❌ No hay grupo de anuncios activo")
        return
    
    st.markdown("### 🔑 Editor de Palabras Clave")
    
    st.markdown("""
    <div class="insight-card-info">
        <strong>💡 Consejos para Palabras Clave:</strong><br>
        • <strong>Concordancia amplia:</strong> Mayor alcance, menos control<br>
        • <strong>Concordancia de frase:</strong> Balance entre alcance y control<br>
        • <strong>Concordancia exacta:</strong> Máximo control, menor alcance
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========== AGREGAR PALABRA CLAVE INDIVIDUAL ==========
    st.markdown("#### ➕ Agregar Palabra Clave Individual")
    
    col_kw1, col_kw2, col_kw3 = st.columns([3, 2, 1])
    
    with col_kw1:
        new_keyword = st.text_input(
            "Nueva Palabra Clave",
            placeholder="Ej: zapatos deportivos",
            key="new_keyword_input",
            help="Ingresa una palabra clave y presiona Enter o click en Agregar"
        )
    
    with col_kw2:
        match_type = st.selectbox(
            "Tipo de Concordancia",
            options=["BROAD", "PHRASE", "EXACT"],
            format_func=lambda x: {
                "BROAD": "🌐 Amplia",
                "PHRASE": "📝 Frase",
                "EXACT": "🎯 Exacta"
            }[x],
            key="new_keyword_match_type"
        )
    
    with col_kw3:
        st.markdown("<br>", unsafe_allow_html=True)  # Espaciado
        if st.button("➕ Agregar", use_container_width=True, type="primary", key="add_single_keyword_btn"):
            if new_keyword and new_keyword.strip():
                # ✅ Agregar directamente al objeto en session_state
                st.session_state.current_ad_group.keywords.append({
                    'text': new_keyword.strip(),
                    'match_type': match_type
                })
                st.success(f"✅ Palabra clave agregada: {new_keyword}")
                logger.info(f"Keyword agregada: {new_keyword} ({match_type})")
                time.sleep(0.5)
                st.rerun()
            else:
                st.warning("⚠️ Ingresa una palabra clave válida")
    
    st.markdown("---")
    
    # ========== AGREGAR MÚLTIPLES KEYWORDS ==========
    st.markdown("#### 📋 Agregar Múltiples Palabras Clave")
    st.caption("Ingresa una palabra clave por línea")
    
    col_bulk1, col_bulk2 = st.columns([3, 1])
    
    with col_bulk1:
        bulk_keywords = st.text_area(
            "Palabras Clave (una por línea)",
            height=150,
            placeholder="zapatos deportivos\nzapatillas running\ntenis para correr",
            key="bulk_keywords",
            help="Escribe cada palabra clave en una línea nueva"
        )
    
    with col_bulk2:
        bulk_match_type = st.selectbox(
            "Tipo para todas",
            options=["BROAD", "PHRASE", "EXACT"],
            format_func=lambda x: {
                "BROAD": "🌐 Amplia",
                "PHRASE": "📝 Frase",
                "EXACT": "🎯 Exacta"
            }[x],
            key="bulk_match_type"
        )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("➕ Agregar Todas", use_container_width=True, key="add_bulk_keywords_btn"):
            if bulk_keywords and bulk_keywords.strip():
                keywords_list = [kw.strip() for kw in bulk_keywords.strip().split('\n') if kw.strip()]
                
                if keywords_list:
                    # ✅ Agregar todas directamente
                    for kw in keywords_list:
                        st.session_state.current_ad_group.keywords.append({
                            'text': kw,
                            'match_type': bulk_match_type
                        })
                    
                    st.success(f"✅ {len(keywords_list)} palabras clave agregadas")
                    logger.info(f"{len(keywords_list)} keywords agregadas en bulk")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.warning("⚠️ No se encontraron palabras clave válidas")
            else:
                st.warning("⚠️ Escribe al menos una palabra clave")
    
    st.markdown("---")
    
    # ========== LISTA DE KEYWORDS ACTUALES ==========
    st.markdown("#### 📝 Palabras Clave del Grupo")
    
    current_keywords = st.session_state.current_ad_group.keywords
    
    if current_keywords and len(current_keywords) > 0:
        st.success(f"✅ Total: {len(current_keywords)} palabras clave")
        
        # Mostrar cada keyword con opción de eliminar
        for idx, kw in enumerate(current_keywords):
            col_kw_text, col_kw_type, col_kw_actions = st.columns([3, 2, 1])
            
            with col_kw_text:
                match_icon = {
                    "BROAD": "🌐",
                    "PHRASE": "📝",
                    "EXACT": "🎯"
                }.get(kw['match_type'], "🔑")
                st.text(f"{match_icon} {kw['text']}")
            
            with col_kw_type:
                st.caption(f"Concordancia: {kw['match_type']}")
            
            with col_kw_actions:
                # ✅ Key único usando índice + hash del texto
                unique_key = f"delete_kw_{idx}_{hash(kw['text']) % 10000}"
                if st.button("🗑️", key=unique_key, help="Eliminar palabra clave"):
                    # ✅ Eliminar directamente
                    st.session_state.current_ad_group.keywords.pop(idx)
                    st.success("✅ Palabra clave eliminada")
                    logger.info(f"Keyword eliminada: {kw['text']}")
                    time.sleep(0.3)
                    st.rerun()
        
        st.markdown("---")
        
        # Opciones de exportación
        col_export, col_clear = st.columns(2)
        
        with col_export:
            # Crear CSV de keywords
            keywords_csv = "Palabra Clave,Tipo de Concordancia\n"
            for kw in current_keywords:
                keywords_csv += f"{kw['text']},{kw['match_type']}\n"
            
            st.download_button(
                "📥 Exportar Keywords (CSV)",
                keywords_csv,
                f"keywords_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv",
                use_container_width=True
            )
        
        with col_clear:
            if st.button("🗑️ Limpiar Todas", use_container_width=True, key="clear_all_keywords_btn"):
                # Confirmación
                if 'confirm_clear_keywords' not in st.session_state:
                    st.session_state.confirm_clear_keywords = False
                
                if not st.session_state.confirm_clear_keywords:
                    st.session_state.confirm_clear_keywords = True
                    st.warning("⚠️ Haz clic de nuevo para confirmar")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.session_state.current_ad_group.keywords = []
                    st.session_state.confirm_clear_keywords = False
                    st.success("✅ Todas las palabras clave eliminadas")
                    logger.info("Todas las keywords eliminadas")
                    time.sleep(0.5)
                    st.rerun()
    
    else:
        st.info("💡 Agrega al menos una palabra clave para este grupo de anuncios")
        st.caption("Las palabras clave determinan cuándo se mostrarán tus anuncios")

def render_ad_group_editor_modal():
    """
    Modal principal para crear/editar un grupo de anuncios
    Incluye: nombre, CPC, anuncios (max 3) y palabras clave
    """
    st.markdown("## 🧩 Editor de Grupo de Anuncios")
    
    if not st.session_state.current_ad_group:
        st.session_state.current_ad_group = AdGroup()
    
    current_group = st.session_state.current_ad_group
    
    # Tabs para organizar el contenido
    tab_general, tab_ads, tab_keywords = st.tabs([
        "⚙️ General",
        f"🪧 Anuncios ({len(current_group.ads)}/3)",
        f"🔑 Palabras Clave ({len(current_group.keywords)})"
    ])
    
    with tab_general:
        st.markdown("### ⚙️ Configuración General")
        
        col_name, col_cpc = st.columns([2, 1])
        
        with col_name:
            group_name = st.text_input(
                "Nombre del Grupo de Anuncios *",
                value=current_group.name,
                placeholder="Ej: Zapatos Deportivos - Ofertas",
                help="Nombre descriptivo para identificar el grupo",
                key="ad_group_name"
            )
            current_group.name = group_name
        
        with col_cpc:
            cpc_bid = st.number_input(
                "CPC Máximo (USD) *",
                min_value=0.01,
                max_value=1000.0,
                value=current_group.cpc_bid_micros / 1_000_000,
                step=0.10,
                help="Costo por clic máximo que estás dispuesto a pagar",
                key="ad_group_cpc"
            )
            current_group.cpc_bid_micros = int(cpc_bid * 1_000_000)
        
        col_status = st.columns(1)[0]
        with col_status:
            status = st.selectbox(
                "Estado del Grupo",
                options=["ENABLED", "PAUSED"],
                index=0 if current_group.status == "ENABLED" else 1,
                format_func=lambda x: "✅ Activo" if x == "ENABLED" else "⏸️ Pausado",
                key="ad_group_status"
            )
            current_group.status = status
        
        st.markdown("---")
        
        # Resumen del grupo
        st.markdown("### 📊 Resumen del Grupo")
        
        col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
        
        with col_sum1:
            st.metric("📝 Nombre", "✅ Válido" if group_name.strip() else "❌ Requerido")
        
        with col_sum2:
            st.metric("🪧 Anuncios", f"{len(current_group.ads)}/3")
        
        with col_sum3:
            st.metric("🔑 Keywords", len(current_group.keywords))
        
        with col_sum4:
            st.metric("💰 CPC Máx", f"${cpc_bid:.2f}")
    
    with tab_ads:
        st.markdown("### 🪧 Gestión de Anuncios")
        st.caption("⭐ Máximo 3 anuncios por grupo de anuncios")
        
        # ========== SECCIÓN: ANUNCIOS DE IA DISPONIBLES ==========
        # ✅ CORRECCIÓN: Mostrar SIEMPRE (excepto cuando el editor modal esté activo)
        
        # Inicializar variable si no existe
        if 'show_ad_editor_modal' not in st.session_state:
            st.session_state.show_ad_editor_modal = False
        
        # Solo ocultar cuando el modal de edición esté activo
        show_ai_section = not st.session_state.show_ad_editor_modal
        
        if show_ai_section:
            # Obtener anuncios disponibles
            pending_ai_ads = st.session_state.get('pending_ai_ads', [])
            available_ads = [ad for ad in pending_ai_ads if not ad.get('used', False)]
            
            # Debug info (temporal - puedes eliminarlo después)
            logger.info(f"🔍 DEBUG: Total pending_ai_ads: {len(pending_ai_ads)}")
            logger.info(f"🔍 DEBUG: Available ads: {len(available_ads)}")
            
            if available_ads:
                st.markdown("---")
                st.markdown("#### 🤖 Anuncios Generados con IA (Disponibles)")
                st.caption(f"💡 Tienes {len(available_ads)} anuncio(s) generado(s) con IA listo(s) para importar")
                
                # ✅ CORRECCIÓN: expanded=True por defecto
                with st.expander(f"📥 Ver y Usar Anuncios de IA ({len(available_ads)})", expanded=True):
                    
                    for idx, ai_ad in enumerate(available_ads):
                        # Verificar que el anuncio tenga datos válidos
                        if not ai_ad.get('headlines') or not ai_ad.get('descriptions'):
                            logger.warning(f"⚠️ Anuncio {ai_ad.get('id', 'unknown')} sin datos válidos")
                            continue
                        
                        # Crear contenedor para cada anuncio
                        with st.container():
                            col_info, col_action = st.columns([3, 1])
                            
                            with col_info:
                                # ID y metadata
                                st.markdown(f"**🆔 ID:** `{ai_ad.get('id', 'N/A')}`")
                                
                                # Información del proveedor
                                provider = ai_ad.get('provider', 'N/A')
                                model = ai_ad.get('model', 'N/A')
                                tone = ai_ad.get('tone', 'N/A')
                                timestamp = ai_ad.get('timestamp', 'N/A')
                                
                                st.caption(f"🤖 **Proveedor:** {provider} ({model}) | "
                                        f"🎭 **Tono:** {tone}")
                                st.caption(f"⏰ **Generado:** {timestamp[:19] if len(timestamp) > 19 else timestamp}")
                                
                                # Resumen de contenido
                                num_headlines = len(ai_ad.get('headlines', []))
                                num_descriptions = len(ai_ad.get('descriptions', []))
                                st.caption(f"📝 **Contenido:** {num_headlines} títulos | {num_descriptions} descripciones")
                                
                                # Keywords
                                keywords = ai_ad.get('keywords', [])
                                if keywords:
                                    keywords_str = ', '.join(keywords[:5])
                                    if len(keywords) > 5:
                                        keywords_str += f" (+{len(keywords) - 5} más)"
                                    st.caption(f"🔑 **Keywords:** {keywords_str}")
                                
                                # Estado de validación
                                validation = ai_ad.get('validation_result', {})
                                if validation:
                                    is_valid = validation.get('valid', False)
                                    summary = validation.get('summary', {})
                                    
                                    if is_valid:
                                        st.success(f"✅ Validado: {summary.get('valid_headlines', 0)} títulos válidos, "
                                                f"{summary.get('valid_descriptions', 0)} descripciones válidas")
                                    else:
                                        invalid_h = summary.get('invalid_headlines', 0)
                                        invalid_d = summary.get('invalid_descriptions', 0)
                                        st.warning(f"⚠️ Con advertencias: {invalid_h} títulos y {invalid_d} descripciones necesitan revisión")
                                
                                # Preview de primeros títulos
                                with st.expander("👁️ Vista Previa", expanded=False):
                                    st.markdown("**Primeros 3 Títulos:**")
                                    for i, h in enumerate(ai_ad.get('headlines', [])[:3], 1):
                                        st.text(f"{i}. {h}")
                                    
                                    st.markdown("**Primeras 2 Descripciones:**")
                                    for i, d in enumerate(ai_ad.get('descriptions', [])[:2], 1):
                                        st.text(f"{i}. {d}")
                            
                            with col_action:
                                # Verificar límite de anuncios
                                can_import = len(current_group.ads) < 3
                                
                                if can_import:
                                    import_button = st.button(
                                        "📥 Importar",
                                        key=f"import_ai_ad_{ai_ad['id']}_{idx}",
                                        use_container_width=True,
                                        type="primary",
                                        help="Importar este anuncio al grupo actual"
                                    )
                                    
                                    if import_button:
                                        try:
                                            # Crear nuevo anuncio
                                            new_ad = AdCreative()
                                            
                                            # Importar títulos (máximo 15)
                                            headlines_imported = 0
                                            for i, headline in enumerate(ai_ad['headlines'][:15]):
                                                if headline and headline.strip():
                                                    new_ad.headlines[i] = headline.strip()
                                                    headlines_imported += 1
                                            
                                            # Importar descripciones (máximo 4)
                                            descriptions_imported = 0
                                            for i, description in enumerate(ai_ad['descriptions'][:4]):
                                                if description and description.strip():
                                                    new_ad.descriptions[i] = description.strip()
                                                    descriptions_imported += 1
                                            
                                            # Agregar al grupo
                                            current_group.ads.append(new_ad)
                                            
                                            # Marcar como usado
                                            mark_ad_as_used(ai_ad['id'])
                                            
                                            # Mensaje de éxito
                                            st.success(f"✅ Anuncio importado exitosamente!")
                                            st.info(f"📝 {headlines_imported} títulos y {descriptions_imported} descripciones importadas. "
                                                f"Ahora agrega la URL de destino.")
                                            
                                            logger.info(f"✅ Anuncio {ai_ad['id']} importado al grupo '{current_group.name}'")
                                            
                                            time.sleep(1.5)
                                            st.rerun()
                                            
                                        except Exception as e:
                                            st.error(f"❌ Error importando anuncio: {e}")
                                            logger.error(f"Error importando anuncio {ai_ad['id']}: {e}", exc_info=True)
                                else:
                                    st.warning("Máx. 3 anuncios")
                                    st.caption("Elimina un anuncio existente para importar otro")
                            
                            # Separador entre anuncios
                            st.markdown("---")
                
                # Información adicional
                st.info("💡 **Tip:** Después de importar, recuerda agregar la URL final y las rutas de visualización antes de publicar.")
            
            else:
                # No hay anuncios disponibles
                st.info("""
                💡 **No hay anuncios de IA disponibles**
                
                **Pasos para generar anuncios:**
                1. Ve a **🤖 Generador de Anuncios IA** en el menú lateral
                2. Configura tu proveedor (OpenAI o Gemini)
                3. Ingresa palabras clave y genera anuncios
                4. Haz clic en **"📤 Guardar para Usar en Campañas"**
                5. Regresa aquí para importarlos
                
                O usa el **generador inline** abajo ⬇️
                """)
            
            st.markdown("---")
        
        # ========== GENERADOR IA INLINE (si lo tienes implementado) ==========
        # ... código del generador inline si existe ...
        
        # ========== BOTÓN CREAR MANUAL ==========
        if not st.session_state.show_ad_editor_modal:
            col_manual_btn = st.columns([1])[0]
            with col_manual_btn:
                if len(current_group.ads) < 3:
                    if st.button("➕ Crear Anuncio Manualmente", use_container_width=True, key="create_manual_ad_btn"):
                        st.session_state.show_ad_editor_modal = True
                        st.session_state.current_ad_index = len(current_group.ads)
                        st.rerun()
                else:
                    st.warning("⚠️ Has alcanzado el límite de 3 anuncios por grupo")
            
            st.markdown("---")
        
        # ========== EDITOR DE ANUNCIO MODAL ==========
        if st.session_state.show_ad_editor_modal:
            with st.container():
                render_ad_editor_modal(st.session_state.current_ad_index)
        
        # ========== LISTA DE ANUNCIOS EXISTENTES ==========
        else:
            if current_group.ads:
                st.markdown("#### 📋 Anuncios en este Grupo")
                
                for idx, ad in enumerate(current_group.ads):
                    valid_headlines = [h for h in ad.headlines if h.strip()]
                    valid_descriptions = [d for d in ad.descriptions if d.strip()]
                    
                    # Determinar si el anuncio está completo
                    is_complete = ad.is_valid()
                    
                    # Card del anuncio
                    with st.expander(
                        f"{'✅' if is_complete else '⚠️'} Anuncio #{idx + 1} - "
                        f"{len(valid_headlines)} títulos, {len(valid_descriptions)} descripciones",
                        expanded=not is_complete
                    ):
                        col_preview, col_actions = st.columns([3, 1])
                        
                        with col_preview:
                            # Preview del anuncio
                            if valid_headlines:
                                st.markdown("**📝 Primeros 3 títulos:**")
                                for h in valid_headlines[:3]:
                                    st.caption(f"• {h}")
                            
                            if valid_descriptions:
                                st.markdown("**📄 Primera descripción:**")
                                st.caption(valid_descriptions[0])
                            
                            if ad.final_url:
                                st.markdown(f"**🔗 URL:** `{ad.final_url}`")
                            else:
                                st.warning("⚠️ Falta URL de destino")
                        
                        with col_actions:
                            if st.button("✏️ Editar", key=f"edit_ad_{idx}", use_container_width=True):
                                st.session_state.show_ad_editor_modal = True
                                st.session_state.current_ad_index = idx
                                st.rerun()
                            
                            if st.button("🗑️ Eliminar", key=f"delete_ad_{idx}", use_container_width=True):
                                current_group.ads.pop(idx)
                                st.success("✅ Anuncio eliminado")
                                time.sleep(0.5)
                                st.rerun()
            else:
                st.info("📭 No hay anuncios en este grupo todavía. Crea uno usando los botones de arriba.")

    with tab_keywords:
        st.markdown("### 🔑 Gestión de Palabras Clave")
        render_keywords_editor()
    
    # Botones de acción finales
    col_action1, col_action2, col_action3 = st.columns([1, 1, 1])

    with col_action1:
        if st.button("✅ Guardar Grupo de Anuncios", use_container_width=True, type="primary", disabled=not current_group.is_valid(), key="save_ad_group_btn"):
            # Agregar a la lista de grupos pendientes
            st.session_state.pending_ad_groups.append(current_group.to_dict())
            st.session_state.show_create_ad_group_modal = False
            st.session_state.current_ad_group = None
            st.success(f"✅ Grupo '{current_group.name}' guardado")
            time.sleep(1)
            st.rerun()

    with col_action2:
        if st.button("💾 Guardar y Crear Otro", use_container_width=True, disabled=not current_group.is_valid(), key="save_and_create_another_btn"):
            st.session_state.pending_ad_groups.append(current_group.to_dict())
            st.session_state.current_ad_group = AdGroup()
            st.success(f"✅ Grupo guardado. Crea otro.")
            time.sleep(1)
            st.rerun()

    with col_action3:
        if st.button("❌ Cancelar", use_container_width=True, key="cancel_ad_group_btn"):  # ✅ KEY AGREGADO
            st.session_state.show_create_ad_group_modal = False
            st.session_state.current_ad_group = None
            st.rerun()
    
    # Validación visual
    if not current_group.is_valid():
        issues = []
        if not current_group.name.strip():
            issues.append("❌ Falta nombre del grupo")
        if len(current_group.ads) == 0:
            issues.append("❌ Falta al menos 1 anuncio")
        elif not all(ad.is_valid() for ad in current_group.ads):
            issues.append("❌ Hay anuncios incompletos")
        if len(current_group.keywords) == 0:
            issues.append("❌ Falta al menos 1 palabra clave")
        
        st.warning(" | ".join(issues))

# ==================== FUNCIONES DE PUBLICACIÓN ====================

def publish_ad_groups_to_campaign(customer_id: str, campaign_id: str, ad_groups: List[Dict]) -> Dict:
    """
    Publica grupos de anuncios a una campaña en Google Ads
    Compatible con Google Ads API v17 usando el wrapper
    
    Args:
        customer_id: ID del cliente
        campaign_id: ID de la campaña
        ad_groups: Lista de grupos de anuncios a publicar
    
    Returns:
        Dict con resultado de la operación
    """
    try:
        st.write("🔍 DEBUG 1: Iniciando publicación...")
        
        # Obtener el cliente real del wrapper
        wrapper = st.session_state.google_ads_client
        client = wrapper.get_client()
        
        if not client:
            return {
                'success': False,
                'error': 'No se pudo obtener el cliente de Google Ads',
                'ad_groups_created': 0,
                'ads_created': 0,
                'keywords_created': 0,
                'errors': ['No se pudo obtener el cliente de Google Ads'],
                'details': ['❌ Error: Cliente no inicializado']
            }
        
        st.write(f"🔍 DEBUG 2: Cliente obtenido correctamente")
        st.write(f"🔍 DEBUG 3: Customer ID: {customer_id}")
        st.write(f"🔍 DEBUG 4: Campaign ID: {campaign_id}")
        st.write(f"🔍 DEBUG 5: Número de grupos a crear: {len(ad_groups)}")
        
        # Servicios usando el cliente real
        try:
            st.write("🔍 DEBUG 6: Obteniendo servicios...")
            ad_group_service = client.get_service("AdGroupService")
            st.write("🔍 DEBUG 6.1: AdGroupService obtenido ✅")
            
            ad_group_ad_service = client.get_service("AdGroupAdService")
            st.write("🔍 DEBUG 6.2: AdGroupAdService obtenido ✅")
            
            ad_group_criterion_service = client.get_service("AdGroupCriterionService")
            st.write("🔍 DEBUG 6.3: AdGroupCriterionService obtenido ✅")
            
            campaign_service = client.get_service("CampaignService")
            st.write("🔍 DEBUG 6.4: CampaignService obtenido ✅")
        except Exception as service_error:
            error_msg = f"Error obteniendo servicios: {str(service_error)}"
            st.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'ad_groups_created': 0,
                'ads_created': 0,
                'keywords_created': 0,
                'errors': [error_msg],
                'details': [f"❌ {error_msg}"]
            }
        
        results = {
            'success': True,
            'ad_groups_created': 0,
            'ads_created': 0,
            'keywords_created': 0,
            'errors': [],
            'details': []
        }
        
        for group_idx, group_data in enumerate(ad_groups):
            st.write(f"🔍 DEBUG 7.{group_idx}: Procesando grupo '{group_data['name']}'...")
            
            try:
                # ========== 1. CREAR AD GROUP ==========
                st.write(f"🔍 DEBUG 8.{group_idx}: Creando operación de grupo...")
                
                ad_group_operation = client.get_type("AdGroupOperation")
                ad_group = ad_group_operation.create
                
                ad_group.name = group_data['name']
                ad_group.campaign = campaign_service.campaign_path(customer_id, campaign_id)
                ad_group.status = client.enums.AdGroupStatusEnum[group_data['status']].value
                ad_group.cpc_bid_micros = group_data['cpc_bid_micros']
                ad_group.type_ = client.enums.AdGroupTypeEnum.SEARCH_STANDARD.value
                
                st.write(f"🔍 DEBUG 9.{group_idx}: Operación configurada, ejecutando mutate...")
                st.write(f"  - Nombre: {ad_group.name}")
                st.write(f"  - Campaign path: {ad_group.campaign}")
                st.write(f"  - Status: {ad_group.status}")
                st.write(f"  - CPC: {ad_group.cpc_bid_micros}")
                st.write(f"  - Type: {ad_group.type_}")
                
                # Ejecutar creación del grupo
                ad_group_response = ad_group_service.mutate_ad_groups(
                    customer_id=customer_id,
                    operations=[ad_group_operation]
                )
                
                ad_group_resource_name = ad_group_response.results[0].resource_name
                ad_group_id = ad_group_resource_name.split('/')[-1]
                
                st.write(f"🔍 DEBUG 10.{group_idx}: ✅ Grupo creado! ID: {ad_group_id}")
                
                results['ad_groups_created'] += 1
                results['details'].append(f"✅ Grupo '{group_data['name']}' creado (ID: {ad_group_id})")
                
                # ========== 2. CREAR ANUNCIOS ==========
                st.write(f"🔍 DEBUG 11.{group_idx}: Creando {len(group_data['ads'])} anuncios...")
                
                for ad_idx, ad_data in enumerate(group_data['ads']):
                    try:
                        st.write(f"🔍 DEBUG 12.{group_idx}.{ad_idx}: Configurando anuncio #{ad_idx + 1}...")
                        
                        ad_group_ad_operation = client.get_type("AdGroupAdOperation")
                        ad_group_ad = ad_group_ad_operation.create
                        
                        ad_group_ad.ad_group = ad_group_resource_name
                        ad_group_ad.status = client.enums.AdGroupAdStatusEnum.ENABLED.value
                        
                        # Configurar Responsive Search Ad
                        ad = ad_group_ad.ad
                        ad.final_urls.append(ad_data['final_url'])
                        
                        st.write(f"  - URL: {ad_data['final_url']}")
                        st.write(f"  - Headlines: {len(ad_data['headlines'])}")
                        st.write(f"  - Descriptions: {len(ad_data['descriptions'])}")
                        
                        # Agregar títulos (Headlines)
                        for headline_text in ad_data['headlines']:
                            headline = client.get_type("AdTextAsset")
                            headline.text = headline_text
                            ad.responsive_search_ad.headlines.append(headline)
                        
                        # Agregar descripciones
                        for description_text in ad_data['descriptions']:
                            description = client.get_type("AdTextAsset")
                            description.text = description_text
                            ad.responsive_search_ad.descriptions.append(description)
                        
                        # Agregar rutas de visualización (paths)
                        if ad_data.get('path1'):
                            ad.responsive_search_ad.path1 = ad_data['path1']
                        if ad_data.get('path2'):
                            ad.responsive_search_ad.path2 = ad_data['path2']
                        
                        st.write(f"🔍 DEBUG 13.{group_idx}.{ad_idx}: Ejecutando mutate de anuncio...")
                        
                        # Ejecutar creación del anuncio
                        ad_response = ad_group_ad_service.mutate_ad_group_ads(
                            customer_id=customer_id,
                            operations=[ad_group_ad_operation]
                        )
                        
                        st.write(f"🔍 DEBUG 14.{group_idx}.{ad_idx}: ✅ Anuncio creado!")
                        
                        results['ads_created'] += 1
                        results['details'].append(f"  ✅ Anuncio #{ad_idx + 1} creado en grupo '{group_data['name']}'")
                    
                    except Exception as ad_error:
                        error_msg = f"  ❌ Error creando anuncio #{ad_idx + 1}: {str(ad_error)}"
                        st.error(error_msg)
                        results['errors'].append(error_msg)
                        results['details'].append(error_msg)
                        logger.error(error_msg)
                        
                        # Mostrar detalles del error si están disponibles
                        if hasattr(ad_error, 'failure'):
                            for error in ad_error.failure.errors:
                                st.error(f"    → {error.message}")
                
                # ========== 3. CREAR KEYWORDS ==========
                st.write(f"🔍 DEBUG 15.{group_idx}: Creando {len(group_data['keywords'])} keywords...")
                
                keyword_operations = []
                for kw_idx, keyword_data in enumerate(group_data['keywords']):
                    try:
                        criterion_operation = client.get_type("AdGroupCriterionOperation")
                        criterion = criterion_operation.create
                        
                        criterion.ad_group = ad_group_resource_name
                        criterion.status = client.enums.AdGroupCriterionStatusEnum.ENABLED.value
                        criterion.keyword.text = keyword_data['text']
                        criterion.keyword.match_type = client.enums.KeywordMatchTypeEnum[keyword_data['match_type']].value
                        
                        keyword_operations.append(criterion_operation)
                    
                    except Exception as kw_error:
                        error_msg = f"  ❌ Error preparando keyword '{keyword_data['text']}': {str(kw_error)}"
                        st.error(error_msg)
                        results['errors'].append(error_msg)
                        logger.error(error_msg)
                
                # Ejecutar creación de keywords en batch
                if keyword_operations:
                    try:
                        st.write(f"🔍 DEBUG 16.{group_idx}: Ejecutando mutate de {len(keyword_operations)} keywords...")
                        
                        keyword_response = ad_group_criterion_service.mutate_ad_group_criteria(
                            customer_id=customer_id,
                            operations=keyword_operations
                        )
                        
                        st.write(f"🔍 DEBUG 17.{group_idx}: ✅ Keywords creadas!")
                        
                        results['keywords_created'] += len(keyword_response.results)
                        results['details'].append(f"  ✅ {len(keyword_response.results)} palabras clave creadas en grupo '{group_data['name']}'")
                    
                    except Exception as kw_batch_error:
                        error_msg = f"  ❌ Error creando keywords en batch: {str(kw_batch_error)}"
                        st.error(error_msg)
                        results['errors'].append(error_msg)
                        results['details'].append(error_msg)
                        logger.error(error_msg)
                        
                        # Mostrar detalles del error
                        if hasattr(kw_batch_error, 'failure'):
                            for error in kw_batch_error.failure.errors:
                                st.error(f"    → {error.message}")
            
            except Exception as group_error:
                error_msg = f"❌ Error creando grupo '{group_data['name']}': {str(group_error)}"
                st.error(error_msg)
                results['errors'].append(error_msg)
                results['details'].append(error_msg)
                results['success'] = False
                logger.error(error_msg)
                
                # Agregar detalles del error si están disponibles
                if hasattr(group_error, 'failure'):
                    for error in group_error.failure.errors:
                        error_detail = f"  → {error.message}"
                        st.error(error_detail)
                        results['errors'].append(error_detail)
                        results['details'].append(error_detail)
        
        st.write(f"🔍 DEBUG 18: Publicación completada!")
        st.write(f"  - Grupos creados: {results['ad_groups_created']}")
        st.write(f"  - Anuncios creados: {results['ads_created']}")
        st.write(f"  - Keywords creadas: {results['keywords_created']}")
        st.write(f"  - Errores: {len(results['errors'])}")
        
        # Si hubo errores pero se crearon algunos elementos, marcar como éxito parcial
        if results['errors'] and (results['ad_groups_created'] > 0 or results['ads_created'] > 0):
            results['success'] = False
            results['details'].insert(0, "⚠️ Publicación parcial: Algunos elementos se crearon pero hubo errores")
        
        return results
    
    except Exception as e:
        error_message = str(e)
        st.error(f"❌ ERROR GENERAL: {error_message}")
        logger.error(f"Error general publicando grupos de anuncios: {error_message}")
        
        # Intentar obtener más detalles del error
        error_details = [f"❌ Error general: {error_message}"]
        
        if hasattr(e, 'failure'):
            try:
                for error in e.failure.errors:
                    error_detail = f"  → {error.message}"
                    st.error(error_detail)
                    error_details.append(error_detail)
            except:
                pass
        
        # Mostrar traceback completo
        import traceback
        st.code(traceback.format_exc())
        
        return {
            'success': False,
            'error': error_message,
            'ad_groups_created': 0,
            'ads_created': 0,
            'keywords_created': 0,
            'errors': error_details,
            'details': error_details
        }

def render_campaign_edit_modal(campaign):
    """
    Modal principal para editar una campaña
    Permite agregar nuevos grupos de anuncios
    """
    
    # ========== DEBUG TEMPORAL (ELIMINAR DESPUÉS) ==========
    st.sidebar.markdown("### 🐛 Debug Estado")
    st.sidebar.write({
        'show_ai_modal': st.session_state.get('show_ai_generator_modal_for_group', False),
        'show_create_group': st.session_state.get('show_create_ad_group_modal', False),
        'ai_group_id': st.session_state.get('ai_gen_ad_group_id'),
        'ai_group_name': st.session_state.get('ai_gen_ad_group_name'),
        'pending_groups': len(st.session_state.pending_ad_groups)
    })
    # ========== FIN DEBUG ==========
    
    st.markdown("## ✏️ Editor de Campaña")
    st.markdown(f"<h3 style='color: #667eea;'>{campaign.campaign_name}</h3>", unsafe_allow_html=True)
    st.caption(f"ID: {campaign.campaign_id} | Estado: {campaign.campaign_status.value}")
    
    st.markdown("---")
    
    # ========== PRIORIDAD 1: MODAL DE IA PARA GRUPO EXISTENTE ==========
    if st.session_state.get('show_ai_generator_modal_for_group', False):
        st.markdown("### 🤖 Generador de Anuncios con IA")
        
        # ✅ Obtener valores con validación
        selected_customer = st.session_state.get('selected_customer')
        ai_group_id = st.session_state.get('ai_gen_ad_group_id')
        ai_group_name = st.session_state.get('ai_gen_ad_group_name')
        ai_keywords = st.session_state.get('ai_gen_keywords', [])
        
        # Debug info
        st.caption(f"Grupo: {ai_group_name} (ID: {ai_group_id})")
        
        # ✅ Validar que tenemos todos los datos necesarios
        if not selected_customer:
            st.error("❌ No hay cliente seleccionado")
            if st.button("🔙 Volver", key="back_no_customer"):
                st.session_state.show_ai_generator_modal_for_group = False
                st.rerun()
            return
        
        if not ai_group_id or not ai_group_name:
            st.error("❌ No hay datos del grupo. Intenta de nuevo.")
            if st.button("🔙 Volver", key="back_no_group_data"):
                st.session_state.show_ai_generator_modal_for_group = False
                st.rerun()
            return
        
        st.markdown("---")
        
        try:
            # ✅ Llamada con argumentos validados
            render_ai_ad_generator_modal_for_group(
                customer_id=str(selected_customer),
                ad_group_id=str(ai_group_id),
                ad_group_name=str(ai_group_name),
                existing_keywords=ai_keywords if isinstance(ai_keywords, list) else []
            )
            
        except Exception as e:
            st.error(f"❌ Error en modal de IA: {e}")
            logger.error(f"Error modal IA: {e}", exc_info=True)
            
            # Mostrar más detalles
            with st.expander("🔧 Detalles del Error"):
                st.code(f"""
            Error: {str(e)}
            
            Datos disponibles:
            - Customer ID: {selected_customer}
            - Ad Group ID: {ai_group_id}
            - Ad Group Name: {ai_group_name}
            - Keywords: {len(ai_keywords) if ai_keywords else 0}
            """)
            
            if st.button("🔙 Volver", key="back_error"):
                st.session_state.show_ai_generator_modal_for_group = False
                st.rerun()
        
        return  # ✅ NO renderizar nada más
    
    # ========== PRIORIDAD 2: MODAL DE CREAR GRUPO ==========
    if st.session_state.get('show_create_ad_group_modal', False):
        render_ad_group_editor_modal()
        return  # ✅ NO renderizar nada más
    
    # Tabs para organizar contenido
    tab_info, tab_groups, tab_pending = st.tabs([
        "ℹ️ Información",
        f"🧩 Grupos Existentes",
        f"📋 Pendientes de Publicar ({len(st.session_state.pending_ad_groups)})"
    ])
    
    with tab_info:
        st.markdown("### 📊 Información de la Campaña")
        
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            st.markdown(f"""
            **Detalles Básicos:**
            - **Nombre:** {campaign.campaign_name}
            - **ID:** {campaign.campaign_id}
            - **Estado:** {campaign.campaign_status.value}
            - **Tipo:** Campaña de Búsqueda
            """)
        
        with col_info2:
            st.markdown("""
            **Acciones Disponibles:**
            - ✅ Agregar nuevos grupos de anuncios
            - ✅ Crear anuncios responsivos
            - ✅ Gestionar palabras clave
            - ✅ Publicar cambios directamente
            """)
        
        st.markdown("---")
        
        # ✅ CORRECCIÓN: Checkbox FUERA del botón
        st.markdown("""
        <div class="insight-card-warning">
            <h4 style="margin: 0 0 0.5rem 0;">⚠️ Importante</h4>
            <p style="margin: 0; font-size: 0.9rem;">
                Al presionar "Publicar Ahora", estos grupos de anuncios se crearán directamente en Google Ads.
                Esta acción no se puede deshacer. Verifica que toda la información sea correcta antes de continuar.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # ✅ CHECKBOX FUERA DEL BOTÓN (clave para que funcione)
        confirm_publish = st.checkbox(
            "✅ Confirmo que deseo publicar estos cambios en Google Ads",
            value=False,
            key="confirm_publish_tab_info"
        )
        
        st.markdown("---")
        
        col_publish, col_clear = st.columns([2, 1])
        
        with col_publish:
            # ✅ Botón deshabilitado si no hay confirmación O no hay grupos pendientes
            can_publish = confirm_publish and len(st.session_state.pending_ad_groups) > 0
            
            if st.button(
                "🚀 PUBLICAR AHORA",
                use_container_width=True,
                type="primary",
                disabled=not can_publish,
                key="publish_now_tab_info_btn"
            ):
                selected_customer = st.session_state.get('selected_customer')
                
                with st.spinner("⏳ Publicando en Google Ads..."):
                    result = publish_ad_groups_to_campaign(
                        selected_customer,
                        str(campaign.campaign_id),
                        st.session_state.pending_ad_groups
                    )
                
                # Mostrar resultados
                st.markdown("---")
                st.markdown("### 📊 Resultado de la Publicación")
                
                if result['success']:
                    st.success("✅ Publicación completada exitosamente")
                    
                    col_res1, col_res2, col_res3 = st.columns(3)
                    
                    with col_res1:
                        st.metric("🧩 Grupos Creados", result['ad_groups_created'])
                    
                    with col_res2:
                        st.metric("🪧 Anuncios Creados", result['ads_created'])
                    
                    with col_res3:
                        st.metric("🔑 Keywords Creadas", result['keywords_created'])
                    
                    # Mostrar detalles
                    with st.expander("📋 Ver Detalles", expanded=True):
                        for detail in result['details']:
                            st.markdown(detail)
                    
                    # Limpiar pendientes
                    st.session_state.pending_ad_groups = []
                    
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
                
                else:
                    st.error("❌ Hubo errores durante la publicación")
                    
                    if result['ad_groups_created'] > 0:
                        st.warning(f"⚠️ Se crearon {result['ad_groups_created']} grupos parcialmente")
                    
                    with st.expander("⚠️ Ver Errores", expanded=True):
                        for error in result['errors']:
                            st.error(error)
                    
                    if result['details']:
                        with st.expander("📋 Ver Detalles"):
                            for detail in result['details']:
                                st.markdown(detail)
            
            # Mensaje si no puede publicar
            if not confirm_publish:
                st.caption("⚠️ Marca la casilla de confirmación para habilitar")
            elif len(st.session_state.pending_ad_groups) == 0:
                st.caption("⚠️ No hay grupos pendientes para publicar")
        
        with col_clear:
            if st.button("🗑️ Limpiar Todo", use_container_width=True, key="clear_pending_tab_info_btn"):
                if len(st.session_state.pending_ad_groups) > 0:
                    # Inicializar confirmación
                    if 'confirm_clear_tab_info' not in st.session_state:
                        st.session_state.confirm_clear_tab_info = False
                    
                    if not st.session_state.confirm_clear_tab_info:
                        st.session_state.confirm_clear_tab_info = True
                        st.warning("⚠️ Haz clic de nuevo para confirmar")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.session_state.pending_ad_groups = []
                        st.session_state.confirm_clear_tab_info = False
                        st.success("✅ Grupos pendientes eliminados")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.info("No hay grupos para limpiar")

    with tab_groups:
        st.markdown("### 🧩 Grupos de Anuncios Existentes")
        
        # Botón de actualizar
        col_refresh, col_info = st.columns([1, 3])
        
        with col_refresh:
            if st.button("🔄 Actualizar", use_container_width=True, key="refresh_ad_groups_btn"):
                st.cache_data.clear()
                st.rerun()
        
        with col_info:
            st.caption(f"📊 Mostrando grupos existentes en: {campaign.campaign_name}")
        
        st.markdown("---")
        
        # Cargar grupos de anuncios existentes
        with st.spinner("⏳ Cargando grupos de anuncios..."):
            try:
                # Inicializar servicio de grupos de anuncios
                if 'ad_group_service' not in st.session_state:
                    from services.ad_group_service import AdGroupService
                    st.session_state.ad_group_service = AdGroupService(st.session_state.google_ads_client)
                
                ad_group_service = st.session_state.ad_group_service
                selected_customer = st.session_state.get('selected_customer')
                
                # Obtener grupos existentes
                existing_groups = ad_group_service.get_ad_groups_by_campaign(
                    customer_id=selected_customer,
                    campaign_id=str(campaign.campaign_id),
                    include_metrics=True
                )
                
                if existing_groups:
                    # Métricas totales
                    col_total1, col_total2, col_total3, col_total4 = st.columns(4)
                    
                    total_groups = len(existing_groups)
                    active_groups = len([g for g in existing_groups if g['status'] == 'ENABLED'])
                    
                    # Calcular métricas totales
                    total_clicks = sum(g.get('metrics', {}).get('clicks', 0) for g in existing_groups)
                    total_impressions = sum(g.get('metrics', {}).get('impressions', 0) for g in existing_groups)
                    total_cost = sum(g.get('metrics', {}).get('cost_micros', 0) for g in existing_groups) / 1_000_000
                    total_conversions = sum(g.get('metrics', {}).get('conversions', 0) for g in existing_groups)
                    
                    with col_total1:
                        st.metric("🧩 Total Grupos", total_groups)
                    
                    with col_total2:
                        st.metric("✅ Activos", active_groups)
                    
                    with col_total3:
                        st.metric("💰 Gasto Total", f"${total_cost:,.2f}")
                    
                    with col_total4:
                        st.metric("🎯 Conversiones", int(total_conversions))
                    
                    st.markdown("---")
                    
                    # Mostrar cada grupo de anuncios
                    for idx, group in enumerate(existing_groups):
                        # Calcular métricas del grupo
                        metrics = group.get('metrics', {})
                        impressions = metrics.get('impressions', 0)
                        clicks = metrics.get('clicks', 0)
                        cost = metrics.get('cost_micros', 0) / 1_000_000
                        conversions = metrics.get('conversions', 0)
                        ctr = (clicks / impressions * 100) if impressions > 0 else 0
                        cpc = cost / clicks if clicks > 0 else 0
                        
                        # Status icon
                        status_icon = {
                            'ENABLED': '✅',
                            'PAUSED': '⏸️',
                            'REMOVED': '🗑️'
                        }.get(group['status'], '❓')
                        
                        # Expander para cada grupo
                        with st.expander(
                            f"{status_icon} {group['name']} - "
                            f"💰 ${cost:,.2f} | 👆 {clicks:,} clics | 🎯 {int(conversions)} conversiones",
                            expanded=False
                        ):
                            # Información general del grupo
                            col_group_info, col_group_metrics = st.columns([1, 1])
                            
                            with col_group_info:
                                st.markdown("**📊 Información General:**")
                                st.markdown(f"- **ID:** `{group['id']}`")
                                st.markdown(f"- **Estado:** {status_icon} {group['status']}")
                                st.markdown(f"- **Tipo:** {group['type']}")
                                st.markdown(f"- **CPC Máximo:** ${group['cpc_bid_micros'] / 1_000_000:.2f}")
                                
                                if group.get('target_cpa_micros'):
                                    st.markdown(f"- **CPA Objetivo:** ${group['target_cpa_micros'] / 1_000_000:.2f}")
                                
                                if group.get('target_roas'):
                                    st.markdown(f"- **ROAS Objetivo:** {group['target_roas']:.2f}")
                            
                            with col_group_metrics:
                                st.markdown("**📈 Métricas de Rendimiento:**")
                                st.markdown(f"- **Impresiones:** {impressions:,}")
                                st.markdown(f"- **Clics:** {clicks:,}")
                                st.markdown(f"- **CTR:** {ctr:.2f}%")
                                st.markdown(f"- **CPC Promedio:** ${cpc:.2f}")
                                st.markdown(f"- **Gasto:** ${cost:,.2f}")
                                st.markdown(f"- **Conversiones:** {int(conversions)}")
                            
                            st.markdown("---")
                            
                            # Tabs para anuncios y keywords
                            tab_ads_existing, tab_keywords_existing = st.tabs([
                                "🪧 Anuncios",
                                "🔑 Palabras Clave"
                            ])
                            
                            with tab_ads_existing:
                                with st.spinner("Cargando anuncios..."):
                                    ads = ad_group_service.get_ads_by_ad_group(
                                        customer_id=selected_customer,
                                        ad_group_id=group['id']
                                    )
                                    
                                    if ads:
                                        st.success(f"✅ {len(ads)} anuncio(s) encontrado(s)")
                                        
                                        for ad_idx, ad in enumerate(ads):
                                            ad_status_icon = {
                                                'ENABLED': '✅',
                                                'PAUSED': '⏸️',
                                                'REMOVED': '🗑️'
                                            }.get(ad['status'], '❓')
                                            
                                            approval_icon = {
                                                'APPROVED': '✅',
                                                'DISAPPROVED': '❌',
                                                'PENDING_REVIEW': '⏳',
                                                'UNDER_APPEAL': '⚖️'
                                            }.get(ad['approval_status'], '❓')
                                            
                                            with st.expander(
                                                f"{ad_status_icon} {ad['name']} - {approval_icon} {ad['approval_status']}",
                                                expanded=False
                                            ):
                                                col_ad_info, col_ad_content = st.columns([1, 1])
                                                
                                                with col_ad_info:
                                                    st.markdown("**📋 Información del Anuncio:**")
                                                    st.markdown(f"- **ID:** `{ad['id']}`")
                                                    st.markdown(f"- **Estado:** {ad_status_icon} {ad['status']}")
                                                    st.markdown(f"- **Tipo:** {ad['type']}")
                                                    st.markdown(f"- **Aprobación:** {approval_icon} {ad['approval_status']}")
                                                    
                                                    if ad['final_urls']:
                                                        st.markdown("**🔗 URLs Finales:**")
                                                        for url in ad['final_urls']:
                                                            st.markdown(f"- {url}")
                                                
                                                with col_ad_content:
                                                    st.markdown("**📝 Contenido del Anuncio:**")
                                                    
                                                    if ad['headlines']:
                                                        st.markdown("**Títulos:**")
                                                        for i, headline in enumerate(ad['headlines'], 1):
                                                            st.markdown(f"{i}. {headline}")
                                                    
                                                    if ad['descriptions']:
                                                        st.markdown("**Descripciones:**")
                                                        for i, desc in enumerate(ad['descriptions'], 1):
                                                            st.markdown(f"{i}. {desc}")
                                                    
                                                    if ad['path1'] or ad['path2']:
                                                        st.markdown("**Rutas de Visualización:**")
                                                        if ad['path1']:
                                                            st.markdown(f"- Ruta 1: {ad['path1']}")
                                                        if ad['path2']:
                                                            st.markdown(f"- Ruta 2: {ad['path2']}")
                                                
                                                # Botones de acción (pausar, métricas, editar)
                                                st.markdown("---")
                                                col_btn1, col_btn2, col_btn3 = st.columns(3)
                                                
                                                with col_btn1:
                                                    if ad['status'] == 'ENABLED':
                                                        if st.button("⏸️ Pausar", key=f"pause_ad_{ad['id']}", use_container_width=True):
                                                            st.info("Funcionalidad de pausar anuncio en desarrollo")
                                                    else:
                                                        if st.button("▶️ Activar", key=f"enable_ad_{ad['id']}", use_container_width=True):
                                                            st.info("Funcionalidad de activar anuncio en desarrollo")
                                                
                                                with col_btn2:
                                                    if st.button("📊 Métricas", key=f"metrics_ad_{ad['id']}", use_container_width=True):
                                                        st.info("Vista de métricas detalladas en desarrollo")
                                                
                                                with col_btn3:
                                                    if st.button("✏️ Editar", key=f"edit_ad_{ad['id']}", use_container_width=True):
                                                        st.info("Editor de anuncios en desarrollo")
                                    else:
                                        st.warning("No se encontraron anuncios en este grupo")
                            
                            with tab_keywords_existing:
                                with st.spinner("Cargando palabras clave..."):
                                    keywords = ad_group_service.get_keywords_by_ad_group(
                                        customer_id=selected_customer,
                                        ad_group_id=group['id']
                                    )
                                    
                                    if keywords:
                                        st.success(f"✅ {len(keywords)} palabra(s) clave encontrada(s)")
                                        
                                        # Crear DataFrame para mostrar keywords
                                        import pandas as pd
                                        
                                        keywords_df = pd.DataFrame(keywords)
                                        keywords_df['cpc_bid'] = keywords_df['cpc_bid_micros'] / 1_000_000
                                        keywords_df['quality_score'] = keywords_df['quality_score'].fillna('N/A')
                                        
                                        # Mostrar tabla de keywords
                                        st.dataframe(
                                            keywords_df[['text', 'match_type', 'status', 'quality_score', 'cpc_bid']],
                                            column_config={
                                                'text': 'Palabra Clave',
                                                'match_type': 'Tipo de Concordancia',
                                                'status': 'Estado',
                                                'quality_score': 'Quality Score',
                                                'cpc_bid': st.column_config.NumberColumn(
                                                    'CPC Máximo',
                                                    format='$%.2f'
                                                )
                                            },
                                            use_container_width=True
                                        )
                                        
                                        # Estadísticas de keywords
                                        col_kw_stats1, col_kw_stats2, col_kw_stats3 = st.columns(3)
                                        
                                        with col_kw_stats1:
                                            enabled_kw = len([k for k in keywords if k['status'] == 'ENABLED'])
                                            st.metric("✅ Activas", enabled_kw)
                                        
                                        with col_kw_stats2:
                                            avg_quality = keywords_df[keywords_df['quality_score'] != 'N/A']['quality_score'].mean()
                                            if not pd.isna(avg_quality):
                                                st.metric("📊 Quality Score Promedio", f"{avg_quality:.1f}")
                                            else:
                                                st.metric("📊 Quality Score Promedio", "N/A")
                                        
                                        with col_kw_stats3:
                                            avg_cpc = keywords_df['cpc_bid'].mean()
                                            st.metric("💰 CPC Promedio", f"${avg_cpc:.2f}")
                                    else:
                                        st.warning("No se encontraron palabras clave en este grupo")
                            
                            # Botones de acción para el grupo
                            st.markdown("---")
                            st.markdown("**🔧 Acciones del Grupo:**")
                            
                            col_group_btn1, col_group_btn2, col_group_btn3, col_group_btn4 = st.columns(4)
                            
                            with col_group_btn1:
                                if st.button(
                                    "🤖 Agregar Anuncio con IA",
                                    key=f"add_ai_ad_{group['id']}",
                                    use_container_width=True,
                                    type="primary"
                                ):
                                    # ✅ SOLO cambiar estados, NO renderizar modal aquí
                                    # Obtener keywords del grupo para usar como base
                                    keywords = ad_group_service.get_keywords_by_ad_group(
                                        customer_id=selected_customer,
                                        ad_group_id=group['id']
                                    )
                                    keyword_texts = [kw['text'] for kw in keywords]
                                    
                                    # Guardar contexto en session state
                                    st.session_state.ai_gen_ad_group_id = group['id']
                                    st.session_state.ai_gen_ad_group_name = group['name']
                                    st.session_state.ai_gen_keywords = keyword_texts
                                    st.session_state.show_ai_generator_modal_for_group = True
                                    logger.info(f"✅ Modal de IA activado para grupo: {group['name']}")
                                    st.rerun()
                            
                            with col_group_btn2:
                                if group['status'] == 'ENABLED':
                                    if st.button("⏸️ Pausar Grupo", key=f"pause_group_{group['id']}", use_container_width=True):
                                        st.info("Funcionalidad de pausar grupo en desarrollo")
                                else:
                                    if st.button("▶️ Activar Grupo", key=f"enable_group_{group['id']}", use_container_width=True):
                                        st.info("Funcionalidad de activar grupo en desarrollo")
                            
                            with col_group_btn3:
                                if st.button("📊 Métricas Detalladas", key=f"metrics_group_{group['id']}", use_container_width=True):
                                    st.info("Vista de métricas detalladas del grupo en desarrollo")
                            
                            with col_group_btn4:
                                if st.button("✏️ Editar Grupo", key=f"edit_group_{group['id']}", use_container_width=True):
                                    st.info("Editor de grupos de anuncios en desarrollo")
                
                else:
                    st.info("📭 No se encontraron grupos de anuncios en esta campaña")
                    st.markdown("""
                    💡 **Sugerencias:**
                    - Verifica que la campaña tenga grupos de anuncios creados
                    - Usa la pestaña "Pendientes de Publicar" para crear nuevos grupos
                    - Asegúrate de que los grupos no estén marcados como "REMOVED"
                    """)
            
            except Exception as e:
                st.error(f"❌ Error cargando grupos de anuncios: {str(e)}")
                logger.error(f"Error en tab_groups: {e}", exc_info=True)
    
    with tab_pending:
        st.markdown("### 📋 Grupos Pendientes de Publicar")
        
        # ✅ BOTÓN CREAR GRUPO (VERIFICAR QUE ESTÉ FUERA DE CONDICIONALES)
        col_create_btn = st.columns([1])[0]
        with col_create_btn:
            if st.button(
                "➕ Crear Nuevo Grupo de Anuncios",
                use_container_width=True,
                type="primary",
                key="create_new_ad_group_btn_pending"  # ✅ Key único
            ):
                # Activar modal
                st.session_state.show_create_ad_group_modal = True
                st.session_state.current_ad_group = AdGroup()
                logger.info("✅ Modal de crear grupo activado")
                st.rerun()
        
        st.markdown("---")
        
        # ✅ NO renderizar el modal aquí, se renderiza al inicio de la función
        
        # Mostrar grupos pendientes (solo si NO hay modal activo)
        if not st.session_state.show_create_ad_group_modal:
            if st.session_state.pending_ad_groups:
                st.markdown("#### 📦 Grupos Listos para Publicar")
                
                for idx, group in enumerate(st.session_state.pending_ad_groups):
                    with st.expander(f"🧩 {group['name']} - {len(group['ads'])} anuncios, {len(group['keywords'])} keywords", expanded=True):
                        col_group_info, col_group_actions = st.columns([3, 1])
                        
                        with col_group_info:
                            st.markdown(f"**Nombre:** {group['name']}")
                            st.markdown(f"**CPC Máximo:** ${group['cpc_bid_micros'] / 1_000_000:.2f} USD")
                            st.markdown(f"**Estado:** {group['status']}")
                            st.markdown(f"**Anuncios:** {len(group['ads'])}")
                            st.markdown(f"**Palabras Clave:** {len(group['keywords'])}")
                            
                            # Mostrar preview de anuncios
                            with st.expander("👁️ Ver Anuncios", expanded=False):
                                for ad_idx, ad in enumerate(group['ads']):
                                    st.markdown(f"**Anuncio #{ad_idx + 1}:**")
                                    st.markdown(f"- Títulos: {len(ad['headlines'])}")
                                    st.markdown(f"- Descripciones: {len(ad['descriptions'])}")
                                    st.markdown(f"- URL: {ad['final_url']}")
                                    st.markdown("---")
                            
                            # Mostrar preview de keywords
                            with st.expander("👁️ Ver Palabras Clave", expanded=False):
                                for kw in group['keywords'][:10]:  # Mostrar primeras 10
                                    match_icon = {
                                        "BROAD": "🌐",
                                        "PHRASE": "📝",
                                        "EXACT": "🎯"
                                    }.get(kw['match_type'], "🔑")
                                    st.markdown(f"{match_icon} {kw['text']} ({kw['match_type']})")
                                if len(group['keywords']) > 10:
                                    st.caption(f"... y {len(group['keywords']) - 10} más")
                        
                        with col_group_actions:
                            if st.button("🗑️ Eliminar", key=f"delete_pending_group_{idx}", use_container_width=True):
                                st.session_state.pending_ad_groups.pop(idx)
                                st.success("✅ Grupo eliminado de pendientes")
                                time.sleep(0.5)
                                st.rerun()
                
                st.markdown("---")
                
                # Resumen de publicación
                total_ads = sum(len(g['ads']) for g in st.session_state.pending_ad_groups)
                total_keywords = sum(len(g['keywords']) for g in st.session_state.pending_ad_groups)
                
                st.markdown("### 📊 Resumen de Publicación")
                
                col_sum1, col_sum2, col_sum3 = st.columns(3)
                
                with col_sum1:
                    st.metric("🧩 Grupos", len(st.session_state.pending_ad_groups))
                
                with col_sum2:
                    st.metric("🪧 Anuncios", total_ads)
                
                with col_sum3:
                    st.metric("🔑 Keywords", total_keywords)
                
                st.markdown("---")
                
                # Botón de publicación
                st.markdown("""
                <div class="insight-card-warning">
                    <h4 style="margin: 0 0 0.5rem 0;">⚠️ Importante</h4>
                    <p style="margin: 0; font-size: 0.9rem;">
                        Al presionar "Publicar Ahora", estos grupos de anuncios se crearán directamente en Google Ads.
                        Esta acción no se puede deshacer. Verifica que toda la información sea correcta antes de continuar.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                col_publish, col_clear = st.columns([2, 1])
                
                with col_publish:
                    if st.button("🚀 PUBLICAR AHORA", use_container_width=True, type="primary"):
                        # Confirmar con checkbox
                        confirm = st.checkbox("✅ Confirmo que deseo publicar estos cambios en Google Ads", key="confirm_publish")
                        
                        if confirm:
                            selected_customer = st.session_state.get('selected_customer')
                            
                            with st.spinner("⏳ Publicando en Google Ads..."):
                                result = publish_ad_groups_to_campaign(
                                    selected_customer,
                                    str(campaign.campaign_id),
                                    st.session_state.pending_ad_groups
                                )
                            
                            # Mostrar resultados
                            st.markdown("---")
                            st.markdown("### 📊 Resultado de la Publicación")
                            
                            if result['success']:
                                st.success("✅ Publicación completada exitosamente")
                                
                                col_res1, col_res2, col_res3 = st.columns(3)
                                
                                with col_res1:
                                    st.metric("🧩 Grupos Creados", result['ad_groups_created'])
                                
                                with col_res2:
                                    st.metric("🪧 Anuncios Creados", result['ads_created'])
                                
                                with col_res3:
                                    st.metric("🔑 Keywords Creadas", result['keywords_created'])
                                
                                # Mostrar detalles
                                with st.expander("📋 Ver Detalles", expanded=True):
                                    for detail in result['details']:
                                        st.markdown(detail)
                                
                                # Limpiar pendientes
                                st.session_state.pending_ad_groups = []
                                
                                st.balloons()
                                
                                time.sleep(3)
                                st.cache_data.clear()
                                st.rerun()
                            
                            else:
                                st.error("❌ Hubo errores durante la publicación")
                                
                                # Mostrar lo que sí se creó
                                if result['ad_groups_created'] > 0:
                                    st.warning(f"⚠️ Se crearon {result['ad_groups_created']} grupos parcialmente")
                                
                                # Mostrar errores
                                with st.expander("⚠️ Ver Errores", expanded=True):
                                    for error in result['errors']:
                                        st.error(error)
                                
                                # Mostrar detalles
                                if result['details']:
                                    with st.expander("📋 Ver Detalles"):
                                        for detail in result['details']:
                                            st.markdown(detail)
                        
                        else:
                            st.warning("⚠️ Marca la casilla de confirmación para continuar")
                
                with col_clear:
                    if st.button("🗑️ Limpiar Todo", use_container_width=True):
                        if st.checkbox("⚠️ ¿Seguro? Esto eliminará todos los grupos pendientes", key="confirm_clear"):
                            st.session_state.pending_ad_groups = []
                            st.success("✅ Grupos pendientes eliminados")
                            time.sleep(1)
                            st.rerun()
            
            else:
                st.info("""
                💡 **No hay grupos pendientes de publicar**
                
                Haz clic en "Crear Nuevo Grupo de Anuncios" para comenzar.
                Puedes crear varios grupos antes de publicarlos todos juntos.
                """)
    
    st.markdown("---")
    
    # Botón para cerrar modal
    if st.button("❌ Cerrar Editor", use_container_width=True):
        st.session_state.show_edit_modal = False
        st.session_state.selected_campaign_for_edit = None
        st.rerun()


def render_hero_section():
    """Renderiza el hero header ultra moderno"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0 3rem 0; position: relative;">
        <div style="font-size: 5rem; margin-bottom: 1rem; 
                    animation: fadeInDown 0.8s ease-out;
                    filter: drop-shadow(0 0 20px rgba(102, 126, 234, 0.5));">
            🎯
        </div>
        <p style="font-size: 1rem; color: rgba(255, 255, 255, 0.6); 
                  font-weight: 500; letter-spacing: 3px; text-transform: uppercase;
                  margin-bottom: 0.5rem;">
            Sistema de Rendimiento de Campañas
        </p>
        <p style="font-size: 1.2rem; color: rgba(255, 255, 255, 0.8); 
                  font-weight: 400; max-width: 800px; margin: 0 auto;">
            Analiza rendimiento, identifica oportunidades y optimiza tu estrategia publicitaria
        </p>
        <div style="width: 100px; height: 3px; 
                    background: linear-gradient(90deg, transparent, #667eea, transparent);
                    margin: 2rem auto 0 auto;"></div>
    </div>
    """, unsafe_allow_html=True)

# ==================== FUNCIÓN PRINCIPAL ====================

# ==================== FUNCIÓN PRINCIPAL (CORREGIDA) ====================

@require_auth
def main():
    """Función principal de la página de campañas con sistema de edición completo"""
    
    # Inyectar CSS moderno
    inject_ultra_modern_css()
    
    # Hero header
    render_hero_section()
    
    # ==================== SIDEBAR CON INDICADOR DE ANUNCIOS DE IA ====================
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🤖 Anuncios de IA")
        
        try:
            from utils.ai_ad_manager import AIAdManager
            stats = AIAdManager.get_statistics()
        except (ImportError, AttributeError):
            # Fallback si no existe AIAdManager
            stats = {
                'total': 0,
                'available': len([ad for ad in st.session_state.get('pending_ai_ads', []) if not ad.get('used', False)]),
                'used': len([ad for ad in st.session_state.get('pending_ai_ads', []) if ad.get('used', False)])
            }
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Disponibles", stats['available'])
        with col2:
            st.metric("Usados", stats['used'])
        
        if stats['available'] > 0:
            st.success(f"✅ {stats['available']} anuncio(s) listo(s) para importar")
        
        # Botón para limpiar usados
        if stats['used'] > 0:
            if st.button("🗑️ Limpiar Usados", use_container_width=True):
                AIAdManager.clear_used_ads()
                st.success("✅ Anuncios usados eliminados")
                st.rerun()
    
    # Verificar servicios
    if not st.session_state.get('google_ads_client') or not st.session_state.get('services'):
        st.error("❌ Servicios de Google Ads no inicializados. Verifica tu configuración.")
        return
    
    # Obtener cliente seleccionado
    selected_customer = st.session_state.get('selected_customer')
    if not selected_customer:
        st.warning("⚠️ No hay cuenta de cliente seleccionada. Selecciona una cuenta en el sidebar.")
        return
    
    # Servicios
    campaign_service = st.session_state.services['campaign']
    
    # Inicializar servicio de acciones
    if 'campaign_actions' not in st.session_state:
        st.session_state.campaign_actions = CampaignActionsService(st.session_state.google_ads_client)
    
    campaign_actions = st.session_state.campaign_actions
    
    # ==================== SI HAY MODAL ACTIVO, MOSTRAR SOLO EL MODAL ====================
    if st.session_state.show_edit_modal and st.session_state.selected_campaign_for_edit:
        render_campaign_edit_modal(st.session_state.selected_campaign_for_edit)
        return  # No renderizar nada más
    
    # Modal de generador de IA para grupos existentes
    if st.session_state.get('show_ai_generator_modal_for_group', False):
        render_ai_ad_generator_modal_for_group()
        return  # No renderizar nada más
    
    # ==================== SI NO HAY MODAL, MOSTRAR CONTENIDO NORMAL ====================
    
    # Panel de control
    st.markdown("## ⚙️ Panel de Control")
    st.markdown("<p style='color: rgba(255,255,255,0.5); font-size: 0.9rem;'>Configura parámetros de análisis</p>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
    
    with col1:
        date_range = st.selectbox(
            "📅 Rango de Fechas",
            options=["Últimos 7 días", "Últimos 30 días", "Últimos 90 días", "Este mes", "Mes pasado"],
            index=1
        )
    
    with col2:
        campaign_status = st.multiselect(
            "📊 Estado de Campaña",
            options=["ENABLED", "PAUSED", "REMOVED"],
            default=["ENABLED"]
        )
    
    with col3:
        sort_by = st.selectbox(
            "🔄 Ordenar Por",
            options=["Gasto", "Clics", "Impresiones", "CTR", "Conversiones"],
            index=0
        )
    
    with col4:
        if st.button("🔄 Actualizar"):
            st.cache_data.clear()
            st.rerun()
    
    try:
        # Cargar datos de campaña
        with st.spinner("⏳ Cargando datos de campañas..."):
            
            campaigns = campaign_service.get_campaigns(selected_customer)
            
            # Calcular fechas
            today = date.today()
            if date_range == "Últimos 7 días":
                start_date = today - timedelta(days=7)
                end_date = today
            elif date_range == "Últimos 30 días":
                start_date = today - timedelta(days=30)
                end_date = today
            elif date_range == "Últimos 90 días":
                start_date = today - timedelta(days=90)
                end_date = today
            elif date_range == "Este mes":
                start_date = today.replace(day=1)
                end_date = today
            elif date_range == "Mes pasado":
                first_this = today.replace(day=1)
                last_month_end = first_this - timedelta(days=1)
                start_date = last_month_end.replace(day=1)
                end_date = last_month_end
            else:
                start_date = today - timedelta(days=30)
                end_date = today
            
            campaign_metrics = campaign_service.get_campaign_metrics(selected_customer, start_date, end_date)
            underperforming = campaign_service.get_underperforming_campaigns(selected_customer)
            
            # Agregar métricas por campaña
            metrics_by_campaign = {}
            for m in (campaign_metrics or []):
                agg = metrics_by_campaign.get(m.campaign_id, {
                    'impressions': 0,
                    'clicks': 0,
                    'cost_micros': 0,
                    'conversions': 0.0
                })
                agg['impressions'] += int(m.impressions)
                agg['clicks'] += int(m.clicks)
                agg['cost_micros'] += int(m.cost_micros)
                agg['conversions'] += float(m.conversions)
                metrics_by_campaign[m.campaign_id] = agg
        
        # Vista general de campañas
        st.markdown("---")
        st.markdown("## 📊 Vista General de Campañas")
        st.markdown(f"<p style='color: rgba(255,255,255,0.5); font-size: 0.9rem;'>Período: {date_range}</p>", unsafe_allow_html=True)
        
        if campaigns:
            total_campaigns = len(campaigns)
            active_campaigns = len([c for c in campaigns if c.campaign_status.value == 'ENABLED'])
            paused_campaigns = len([c for c in campaigns if c.campaign_status.value == 'PAUSED'])
            
            total_impressions = sum(v['impressions'] for v in metrics_by_campaign.values())
            total_clicks = sum(v['clicks'] for v in metrics_by_campaign.values())
            total_spend = sum(v['cost_micros'] for v in metrics_by_campaign.values()) / 1_000_000
            avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("📈 Total Campañas", total_campaigns, help="Número total de campañas en la cuenta")
            
            with col2:
                st.metric("✅ Activas", active_campaigns,
                         delta=f"+{active_campaigns - paused_campaigns}" if active_campaigns > paused_campaigns else None,
                         help="Número de campañas activas")
            
            with col3:
                st.metric("⏸️ Pausadas", paused_campaigns, help="Número de campañas pausadas")
            
            with col4:
                st.metric("💰 Gasto Total", format_currency(total_spend), help="Gasto total en todas las campañas")
            
            with col5:
                st.metric("📊 CTR Promedio", f"{avg_ctr:.2f}%", help="Tasa de clics promedio")
        
        else:
            st.info("📊 No hay datos de campañas disponibles.")
        
        st.markdown("---")
        
        # Layout principal
        col_left, col_right = st.columns([2.5, 1.5])
        
        with col_left:
            st.markdown("### 📈 Análisis de Rendimiento de Campañas")
            
            if campaigns:
                campaign_data = []
                
                for i, campaign in enumerate(campaigns[:10]):
                    cm = metrics_by_campaign.get(campaign.campaign_id, {
                        'impressions': 0,
                        'clicks': 0,
                        'cost_micros': 0,
                        'conversions': 0.0
                    })
                    cost_micros = float(cm['cost_micros'])
                    clicks = int(cm['clicks'])
                    impressions = int(cm['impressions'])
                    conversions = float(cm['conversions'])
                    
                    spend = cost_micros / 1_000_000
                    ctr = (clicks / impressions * 100) if impressions > 0 else 0
                    cpc = spend / clicks if clicks > 0 else 0
                    
                    campaign_name = campaign.campaign_name
                    campaign_status = campaign.campaign_status.value
                    
                    campaign_data.append({
                        'Campaña': campaign_name[:20] + "..." if len(campaign_name) > 20 else campaign_name,
                        'Gasto': spend,
                        'Clics': clicks,
                        'Impresiones': impressions,
                        'Conversiones': conversions,  # ✅ CORREGIDO
                        'CTR': ctr,
                        'CPC': cpc,
                        'Estado': str(campaign_status).upper()
                    })
                
                df_campaigns = pd.DataFrame(campaign_data)
                
                # Gráfico de dispersión
                fig_scatter = px.scatter(
                    df_campaigns,
                    x='Clics',
                    y='Conversiones',
                    size='Gasto',
                    color='CTR',
                    hover_name='Campaña',
                    hover_data=['Gasto', 'CPC'],
                    color_continuous_scale='viridis'
                )
                
                fig_scatter.update_layout(
                    height=400,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='rgba(255,255,255,0.8)'),
                    margin=dict(l=0, r=0, t=20, b=0)
                )
                
                st.plotly_chart(fig_scatter, use_container_width=True, config={"displayModeBar": False})
                
                # Comparación de rendimiento
                st.markdown("### 📊 Comparación de Rendimiento")
                
                metrics_to_compare = st.multiselect(
                    "Selecciona métricas para comparar:",
                    options=['Gasto', 'Clics', 'Impresiones', 'Conversiones', 'CTR', 'CPC'],
                    default=['Gasto', 'Clics', 'Conversiones']
                )
                
                if metrics_to_compare:
                    df_normalized = df_campaigns.copy()
                    for metric in metrics_to_compare:
                        if metric in df_normalized.columns:
                            max_val = df_normalized[metric].max()
                            if max_val > 0:
                                df_normalized[f'{metric}_normalized'] = df_normalized[metric] / max_val * 100
                    
                    fig_comparison = go.Figure()
                    
                    for metric in metrics_to_compare:
                        if f'{metric}_normalized' in df_normalized.columns:
                            fig_comparison.add_trace(go.Bar(
                                name=metric,
                                x=df_normalized['Campaña'],
                                y=df_normalized[f'{metric}_normalized'],
                                text=df_normalized[metric].round(2),
                                textposition='auto'
                            ))
                    
                    fig_comparison.update_layout(
                        xaxis_title="Campaña",
                        yaxis_title="Rendimiento Normalizado (%)",
                        barmode='group',
                        height=400,
                        xaxis={'tickangle': 45},
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='rgba(255,255,255,0.8)'),
                        margin=dict(l=0, r=0, t=0, b=0)
                    )
                    
                    st.plotly_chart(fig_comparison, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.info("💡 Selecciona métricas para comparar (opcional).")
            
            # ✅ GESTIÓN DE CAMPAÑAS COMPLETA CON EDITOR
            st.markdown("### 📋 Gestión de Campañas")
            
            if campaigns:
                detailed_data = []
                campaign_objects = {}  # Guardar objetos de campaña por ID
                
                for c in campaigns:
                    cm = metrics_by_campaign.get(c.campaign_id, {
                        'impressions': 0,
                        'clicks': 0,
                        'cost_micros': 0,
                        'conversions': 0.0
                    })
                    impressions = cm['impressions']
                    clicks = cm['clicks']
                    cost_micros = cm['cost_micros']
                    conversions = cm['conversions']
                    
                    spend = cost_micros / 1_000_000
                    ctr = (clicks / impressions * 100) if impressions > 0 else 0
                    cpc = spend / clicks if clicks > 0 else 0
                    conv_rate = (conversions / clicks * 100) if clicks > 0 else 0
                    cost_per_conv = spend / conversions if conversions > 0 else 0
                    
                    campaign_id = str(c.campaign_id)
                    campaign_objects[campaign_id] = c  # Guardar objeto completo
                    
                    detailed_data.append({
                        'ID Campaña': campaign_id,
                        'Nombre': c.campaign_name,
                        'Estado': c.campaign_status.value,
                        'Impresiones': format_number(impressions),
                        'Clics': format_number(clicks),
                        'CTR': f"{ctr:.2f}%",
                        'CPC': format_currency(cpc),
                        'Gasto': format_currency(spend),
                        'Conversiones': int(conversions),
                        'Tasa Conv.': f"{conv_rate:.2f}%",
                        'Costo/Conv.': format_currency(cost_per_conv)
                    })
                
                df_detailed = pd.DataFrame(detailed_data)
                
                # Filtros
                col_f1, col_f2, col_f3 = st.columns(3)
                
                with col_f1:
                    status_filter = st.multiselect(
                        "Filtrar por Estado:",
                        options=df_detailed['Estado'].unique(),
                        default=list(df_detailed['Estado'].unique())
                    )
                
                with col_f2:
                    search_term = st.text_input("🔍 Buscar campañas:")
                
                with col_f3:
                    show_rows = st.selectbox("Mostrar filas:", [10, 25, 50, 100], index=1)
                
                # Aplicar filtros
                filtered_df = df_detailed[df_detailed['Estado'].isin(status_filter)]
                
                if search_term:
                    filtered_df = filtered_df[
                        filtered_df['Nombre'].str.contains(search_term, case=False, na=False)
                    ]
                
                # Mostrar tabla filtrada
                st.dataframe(filtered_df.head(show_rows), use_container_width=True)
                
                # ✅ SECCIÓN DE ACCIONES DE CAMPAÑA CON EDITOR
                st.markdown("### ⚡ Acciones de Campaña")
                
                # Acciones masivas
                col_bulk1, col_bulk2, col_bulk3 = st.columns(3)
                
                with col_bulk1:
                    selected_campaigns_bulk = st.multiselect(
                        "Seleccionar campañas para acciones masivas:",
                        options=[(row['ID Campaña'], row['Nombre']) for _, row in filtered_df.iterrows()],
                        format_func=lambda x: f"{x[1]} (ID: {x[0]})"
                    )
                
                with col_bulk2:
                    if st.button("⏸️ Pausar en Masa", disabled=not selected_campaigns_bulk, use_container_width=True):
                        if selected_campaigns_bulk:
                            campaign_ids = [campaign[0] for campaign in selected_campaigns_bulk]
                            with st.spinner("Pausando campañas..."):
                                result = campaign_actions.bulk_pause_campaigns(selected_customer, campaign_ids)
                                if result['success']:
                                    st.success(f"✅ {result['message']}")
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error(f"❌ {result['message']}")
                
                with col_bulk3:
                    if st.button("▶️ Reanudar en Masa", disabled=not selected_campaigns_bulk, use_container_width=True):
                        if selected_campaigns_bulk:
                            campaign_ids = [campaign[0] for campaign in selected_campaigns_bulk]
                            with st.spinner("Reanudando campañas..."):
                                result = campaign_actions.bulk_resume_campaigns(selected_customer, campaign_ids)
                                if result['success']:
                                    st.success(f"✅ {result['message']}")
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error(f"❌ {result['message']}")
                
                # Acciones individuales de campaña con EDITOR
                st.markdown("#### Acciones Individuales de Campaña")
                
                # Mostrar tabla con botones de acción
                for idx, row in filtered_df.head(show_rows).iterrows():
                    with st.expander(f"🎯 {row['Nombre']} - {row['Estado']}", expanded=False):
                        col_info, col_actions = st.columns([2, 1])
                        
                        with col_info:
                            st.markdown(f"""
                            **Detalles de la Campaña:**
                            - **ID:** {row['ID Campaña']}
                            - **Estado:** {row['Estado']}
                            - **Gasto:** {row['Gasto']}
                            - **Clics:** {row['Clics']}
                            - **CTR:** {row['CTR']}
                            - **Conversiones:** {row['Conversiones']}
                            """)
                        
                        with col_actions:
                            campaign_id = row['ID Campaña']
                            current_status = row['Estado']
                            
                            # ✅ BOTÓN DE EDITAR (CORREGIDO)
                            if st.button(f"✏️ Editar Campaña", key=f"edit_{campaign_id}", use_container_width=True, type="primary"):
                                st.session_state.show_edit_modal = True
                                st.session_state.selected_campaign_for_edit = campaign_objects[campaign_id]
                                st.rerun()
                            
                            st.markdown("---")
                            
                            # Botones de Pausar/Reanudar
                            if current_status == 'ENABLED':
                                if st.button(f"⏸️ Pausar", key=f"pause_{campaign_id}", use_container_width=True):
                                    with st.spinner("Pausando campaña..."):
                                        result = campaign_actions.pause_campaign(selected_customer, campaign_id)
                                        if result['success']:
                                            st.success(f"✅ {result['message']}")
                                            st.cache_data.clear()
                                            st.rerun()
                                        else:
                                            st.error(f"❌ {result['message']}")
                            
                            elif current_status == 'PAUSED':
                                if st.button(f"▶️ Reanudar", key=f"resume_{campaign_id}", use_container_width=True):
                                    with st.spinner("Reanudando campaña..."):
                                        result = campaign_actions.resume_campaign(selected_customer, campaign_id)
                                        if result['success']:
                                            st.success(f"✅ {result['message']}")
                                            st.cache_data.clear()
                                            st.rerun()
                                        else:
                                            st.error(f"❌ {result['message']}")
                            
                            # Gestión de presupuesto
                            st.markdown("**Gestión de Presupuesto:**")
                            new_budget = st.number_input(
                                "Nuevo presupuesto diario ($):",
                                min_value=1.0,
                                max_value=10000.0,
                                value=100.0,
                                step=10.0,
                                key=f"budget_{campaign_id}"
                            )
                            
                            if st.button(f"💰 Actualizar Presupuesto", key=f"budget_update_{campaign_id}", use_container_width=True):
                                budget_micros = int(new_budget * 1_000_000)
                                with st.spinner("Actualizando presupuesto..."):
                                    result = campaign_actions.update_campaign_budget(
                                        selected_customer, campaign_id, budget_micros
                                    )
                                    if result['success']:
                                        st.success(f"✅ {result['message']}")
                                        st.cache_data.clear()
                                        st.rerun()
                                    else:
                                        st.error(f"❌ {result['message']}")
                
                # Opciones de exportación
                st.markdown("---")
                col_export1, col_export2 = st.columns(2)
                
                with col_export1:
                    csv_data = filtered_df.to_csv(index=False)
                    st.download_button(
                        label="📊 Exportar Datos de Campañas",
                        data=csv_data,
                        file_name=f"campaigns_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col_export2:
                    if st.button("🔄 Actualizar Todos los Datos", use_container_width=True):
                        st.cache_data.clear()
                        st.rerun()
            
            else:
                st.info("📋 No hay datos detallados de campañas disponibles.")
        
        # ✅ COLUMNA DERECHA - INSIGHTS Y ACCIONES RÁPIDAS
        with col_right:
            # Insights de rendimiento
            st.markdown("### 💡 Insights de Rendimiento")
            
            if underperforming:
                st.markdown("""
                <div class="insight-card-warning">
                    <h4 style="margin: 0 0 0.5rem 0; color: var(--text-primary);">
                        ⚠️ Campañas de Bajo Rendimiento Detectadas
                    </h4>
                    <p style="margin: 0; color: var(--text-secondary); font-size: 0.9rem;">
                        Se detectaron campañas que necesitan optimización
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                for campaign in underperforming[:3]:  # Mostrar top 3
                    st.markdown(f"""
                    <div class="insight-card-danger">
                        <strong>🎯 {campaign.get('campaign_name', 'Campaña Desconocida')}</strong><br>
                        <small><strong>Problema:</strong> {campaign.get('issue', 'Rendimiento por debajo del umbral')}</small><br>
                        <small><strong>Recomendación:</strong> {campaign.get('recommendation', 'Revisar y optimizar')}</small>
                    </div>
                    """, unsafe_allow_html=True)
            
            else:
                st.markdown("""
                <div class="insight-card-success">
                    <h4 style="margin: 0 0 0.5rem 0; color: var(--text-primary);">
                        ✅ Todas las campañas funcionando bien
                    </h4>
                    <p style="margin: 0; color: var(--text-secondary); font-size: 0.9rem;">
                        No se detectaron problemas de rendimiento
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            # Top performers
            st.markdown("### 🏆 Mejores Campañas")
            
            if campaigns:
                # Calcular top performers reales
                top_campaigns_by_conversions = sorted(
                    [(c, metrics_by_campaign.get(c.campaign_id, {'conversions': 0})['conversions']) 
                     for c in campaigns],
                    key=lambda x: x[1],
                    reverse=True
                )[:3]
                
                for campaign, conversions in top_campaigns_by_conversions:
                    cm = metrics_by_campaign.get(campaign.campaign_id, {})
                    ctr = (cm.get('clicks', 0) / cm.get('impressions', 1) * 100) if cm.get('impressions', 0) > 0 else 0
                    
                    st.markdown(f"""
                    <div class="insight-card-success">
                        <strong>📈 {campaign.campaign_name[:30]}</strong><br>
                        <small>CTR: {ctr:.2f}% | Conversiones: {int(conversions)}</small>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Acciones rápidas
            st.markdown("### ⚡ Acciones Rápidas")
            
            st.markdown("""
            <div class="insight-card-info">
                <h4 style="margin: 0 0 0.5rem 0;">✏️ Editor de Campañas</h4>
                <p style="margin: 0; font-size: 0.9rem;">
                    Usa el botón "Editar Campaña" en cualquier campaña para:
                    <br>• Crear nuevos grupos de anuncios
                    <br>• Agregar anuncios responsivos (max 3 por grupo)
                    <br>• Gestionar palabras clave
                    <br>• Publicar cambios directamente
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Estadísticas de campaña
            st.markdown("### 📊 Estadísticas")
            
            if campaigns:
                stats = {
                    'Total Campañas': len(campaigns),
                    'Campañas Activas': len([c for c in campaigns if c.campaign_status.value == 'ENABLED']),
                    'Grupos Pendientes': len(st.session_state.pending_ad_groups)
                }
                
                for stat_name, stat_value in stats.items():
                    st.metric(stat_name, stat_value)
    
    except Exception as e:
        logger.error(f"Error cargando página de campañas: {e}")
        st.error(f"❌ Error cargando datos de campaña: {e}")
        
        with st.expander("🔧 Solución de Problemas"):
            st.markdown("""
            **Problemas Comunes:**
            
            1. **Acceso a Campañas**: Asegúrate de tener acceso a los datos de campaña para la cuenta seleccionada
            2. **Frescura de Datos**: Los datos de campaña pueden tener un retraso de 3-24 horas
            3. **Filtros de Estado**: Verifica que los estados de campaña correctos estén seleccionados
            4. **Rango de Fechas**: Intenta ajustar el rango de fechas si no se muestran datos
            
            **Consejos de Optimización:**
            - Enfócate en campañas con altas impresiones pero CTR bajo
            - Revisa campañas con CPC alto pero bajas tasas de conversión
            - Considera pausar campañas con rendimiento consistentemente pobre
            """)

def render_ai_ad_generator_modal_for_group(
    customer_id: str,
    ad_group_id: str,
    ad_group_name: str,
    existing_keywords: List[str]
):
    """
    Modal inline para generar anuncio con IA y publicarlo directamente al grupo
    
    Args:
        customer_id: ID del cliente
        ad_group_id: ID del grupo donde crear el anuncio
        ad_group_name: Nombre del grupo (para mostrar)
        existing_keywords: Keywords del grupo para usar como base
    """
    st.markdown("## 🤖 Generar Anuncio con IA")
    st.markdown(f"<p style='color: rgba(255,255,255,0.5);'>Grupo: {ad_group_name}</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Configuración del proveedor
    col_provider, col_model = st.columns(2)
    
    with col_provider:
        ai_provider = st.selectbox(
            "🤖 Proveedor de IA",
            options=["OpenAI", "Gemini"],
            key="modal_ai_provider"
        )
    
    with col_model:
        if ai_provider == "OpenAI":
            ai_models = {
                "gpt-4o": "GPT-4o (2025) - Más rápido y eficiente",
                "gpt-4-turbo": "GPT-4 Turbo - Modelo avanzado",
                "gpt-4": "GPT-4 - Modelo estándar",
                "gpt-3.5-turbo": "GPT-3.5 Turbo - Económico"
            }
        else:
            ai_models = {
                "gemini-2.0-flash-exp": "Gemini 2.0 Flash (2025) - Experimental",
                "gemini-1.5-pro": "Gemini 1.5 Pro - Modelo avanzado",
                "gemini-pro": "Gemini Pro - Modelo estándar"
            }
        
        ai_model = st.selectbox(
            "🧠 Modelo",
            options=list(ai_models.keys()),
            format_func=lambda x: ai_models[x],
            key="modal_ai_model"
        )
    
    # API Key
    col_api_key, col_test = st.columns([3, 1])
    
    with col_api_key:
        ai_api_key = st.text_input(
            "🔑 API Key",
            type="password",
            key="modal_ai_api_key",
            help=f"Ingresa tu API key de {ai_provider}"
        )
    
    with col_test:
        st.markdown("<br>", unsafe_allow_html=True)  # Espaciado
        test_connection_btn = st.button(
            "🔍 Probar",
            key="modal_test_connection",
            help="Probar conexión con la API"
        )
    
    # Probar conexión si se presiona el botón
    if test_connection_btn and ai_api_key:
        # Crear contenedor para logs de prueba de conexión
        test_log_container = st.empty()
        test_progress = st.progress(0)
        
        # Lista de logs para la prueba
        test_logs = []
        
        def add_test_log(message):
            timestamp = datetime.now().strftime("%H:%M:%S")
            test_logs.append(f"[{timestamp}] {message}")
            log_text = "\n".join(test_logs[-5:])  # Mostrar últimos 5 logs
            test_log_container.code(log_text, language="text")
        
        try:
            add_test_log(f"🔍 Iniciando prueba de conexión con {ai_provider}")
            add_test_log(f"🔧 Modelo seleccionado: {ai_model}")
            test_progress.progress(20)
            
            # Inicializar generador si no existe
            if 'ai_generator' not in st.session_state:
                add_test_log("🚀 Inicializando generador de IA...")
                from modules.ai_ad_generator import AIAdGenerator
                st.session_state.ai_generator = AIAdGenerator()
            
            ai_generator = st.session_state.ai_generator
            test_progress.progress(40)
            
            # Configurar proveedor
            add_test_log("🔌 Configurando proveedor...")
            success = ai_generator.set_provider(
                provider_type=ai_provider.lower(),
                api_key=ai_api_key,
                model=ai_model
            )
            
            if not success:
                add_test_log("❌ Error: No se pudo configurar el proveedor")
                st.error(f"❌ Error configurando {ai_provider}")
                
                with st.expander("🔍 Detalles del Error de Configuración", expanded=True):
                    st.write("**🚨 Posibles Causas:**")
                    st.write("• API key inválida o expirada")
                    st.write("• Modelo no disponible para tu cuenta")
                    st.write("• Problemas de conectividad")
                    st.write("• Límites de cuota excedidos")
                    
                    st.write("**📋 Log de la Prueba:**")
                    st.code("\n".join(test_logs), language="text")
                return
            
            add_test_log("✅ Proveedor configurado correctamente")
            test_progress.progress(60)
            
            # Probar conexión específica
            add_test_log("🌐 Probando conexión con la API...")
            provider = ai_generator.provider
            
            if provider and hasattr(provider, 'test_connection'):
                connection_result = provider.test_connection()
                test_progress.progress(80)
                
                if connection_result:
                    add_test_log("✅ Conexión exitosa!")
                    test_progress.progress(100)
                    
                    # Mostrar información detallada del éxito
                    st.success(f"✅ Conexión exitosa con {ai_provider} ({ai_model})")
                    
                    with st.expander("📊 Detalles de la Conexión", expanded=False):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**🔧 Configuración:**")
                            st.write(f"• **Proveedor:** {ai_provider}")
                            st.write(f"• **Modelo:** {ai_model}")
                            st.write(f"• **Estado:** Conectado ✅")
                            
                        with col2:
                            st.write("**⚡ Capacidades:**")
                            st.write("• Generación de anuncios ✅")
                            st.write("• Validación de contenido ✅")
                            st.write("• Respuesta en tiempo real ✅")
                        
                        st.write("**📋 Log de la Prueba:**")
                        st.code("\n".join(test_logs), language="text")
                    
                    # Limpiar logs después del éxito
                    time.sleep(2)
                    test_log_container.empty()
                    test_progress.empty()
                    
                else:
                    add_test_log("❌ Error: Conexión fallida")
                    st.error(f"❌ No se pudo conectar con {ai_provider}. Verifica tu API key.")
                    
                    with st.expander("🔍 Diagnóstico de Conexión", expanded=True):
                        st.write("**🚨 Problemas Detectados:**")
                        st.write("• La API key no es válida o ha expirado")
                        st.write("• El modelo especificado no está disponible")
                        st.write("• Problemas de red o conectividad")
                        st.write("• Límites de cuota o facturación")
                        
                        st.write("**💡 Soluciones Sugeridas:**")
                        st.info("1. Verifica que tu API key sea correcta y esté activa")
                        st.info("2. Confirma que tienes acceso al modelo seleccionado")
                        st.info("3. Revisa tu saldo o límites de cuota")
                        st.info("4. Intenta con un modelo diferente")
                        
                        st.write("**📋 Log Completo:**")
                        st.code("\n".join(test_logs), language="text")
            else:
                add_test_log("⚠️ Advertencia: Método test_connection no disponible")
                st.warning(f"⚠️ {ai_provider} configurado, pero no se puede probar la conexión directamente")
                
                with st.expander("ℹ️ Información", expanded=False):
                    st.write("**📝 Nota:**")
                    st.write("Este proveedor no soporta pruebas de conexión directas.")
                    st.write("La conexión se verificará durante la generación del anuncio.")
                    
                    st.write("**📋 Log de Configuración:**")
                    st.code("\n".join(test_logs), language="text")
                
        except Exception as e:
            add_test_log(f"💥 Excepción crítica: {str(e)}")
            st.error(f"❌ Error probando conexión: {str(e)}")
            logger.error(f"Error en test de conexión: {e}", exc_info=True)
            
            with st.expander("🔍 Debug de Error de Conexión", expanded=True):
                st.write("**🚨 Error Técnico:**")
                st.code(str(e), language='text')
                
                st.write("**📋 Log Completo:**")
                st.code("\n".join(test_logs), language="text")
                
                import traceback
                st.write("**🔍 Traceback:**")
                st.code(traceback.format_exc(), language='text')
    
    elif test_connection_btn and not ai_api_key:
        st.warning("⚠️ Ingresa tu API key primero")
    
    # Keywords (usar las del grupo por defecto)
    st.markdown("### 🔑 Palabras Clave")
    
    if existing_keywords:
        st.info(f"📋 Usando {len(existing_keywords)} palabras clave del grupo: {', '.join(existing_keywords[:5])}{'...' if len(existing_keywords) > 5 else ''}")
        use_group_keywords = st.checkbox(
            "Usar palabras clave del grupo",
            value=True,
            key="modal_use_group_keywords"
        )
    else:
        use_group_keywords = False
        st.warning("⚠️ Este grupo no tiene palabras clave. Ingresa algunas manualmente.")
    
    # Keywords personalizadas
    if not use_group_keywords or not existing_keywords:
        custom_keywords_text = st.text_area(
            "Palabras Clave Personalizadas (una por línea)",
            height=100,
            placeholder="zapatos deportivos\nzapatillas running\ncalzado deportivo",
            key="modal_custom_keywords"
        )
    
    # Configuración de generación
    col_tone, col_headlines, col_business = st.columns(3)
    
    with col_tone:
        tone = st.selectbox(
            "🎭 Tono del Anuncio",
            options=["profesional", "casual", "urgente", "informativo", "emocional", "técnico", "juvenil"],
            index=0,
            key="modal_tone"
        )
    
    with col_headlines:
        num_headlines = st.slider(
            "📝 Número de Títulos",
            min_value=3,
            max_value=15,
            value=15,
            key="modal_num_headlines"
        )
    
    with col_business:
        business_type = st.selectbox(
            "🏢 Tipo de Negocio",
            options=["auto", "esoteric", "generic"],
            index=0,
            key="modal_business_type",
            help="Auto: Detección automática basada en keywords\nEsoteric: Servicios esotéricos (tarot, hechizos, etc.)\nGeneric: Negocios generales"
        )
    
    st.markdown("---")
    
    # Botón de generación
    col_gen, col_cancel = st.columns([2, 1])
    
    with col_gen:
        generate_btn = st.button(
            "🚀 GENERAR ANUNCIO CON IA",
            use_container_width=True,
            type="primary",
            key="modal_generate_btn"
        )
    
    with col_cancel:
        if st.button("❌ Cancelar", use_container_width=True, key="modal_cancel_gen_btn"):
            st.session_state.show_ai_generator_modal_for_group = False
            st.rerun()
    
    # PROCESO DE GENERACIÓN
    if generate_btn:
        if not ai_api_key:
            st.error("❌ Ingresa tu API key")
        else:
            # Preparar keywords
            if use_group_keywords and existing_keywords:
                keywords_to_use = existing_keywords
            else:
                if not custom_keywords_text:
                    st.error("❌ Ingresa palabras clave personalizadas")
                    return
                keywords_to_use = [kw.strip() for kw in custom_keywords_text.strip().split('\n') if kw.strip()]
            
            if not keywords_to_use:
                st.error("❌ No hay palabras clave para generar el anuncio")
                return
            
            # Crear contenedor para logs en tiempo real
            log_container = st.empty()
            progress_bar = st.progress(0)
            
            # Inicializar lista de logs
            logs = []
            
            def add_log(message, level="info"):
                timestamp = datetime.now().strftime("%H:%M:%S")
                logs.append(f"[{timestamp}] {message}")
                # Mostrar últimos 10 logs
                log_text = "\n".join(logs[-10:])
                log_container.code(log_text, language="text")
            
            try:
                add_log(f"🚀 Iniciando generación de anuncio con {ai_provider}")
                add_log(f"📝 Keywords: {', '.join(keywords_to_use[:3])}{'...' if len(keywords_to_use) > 3 else ''}")
                add_log(f"🎯 Tipo de negocio: {business_type}")
                add_log(f"🎨 Tono: {tone}")
                progress_bar.progress(10)
                
                # Inicializar generador si no existe
                if 'ai_generator' not in st.session_state:
                    add_log("🔧 Inicializando generador de IA...")
                    from modules.ai_ad_generator import AIAdGenerator
                    st.session_state.ai_generator = AIAdGenerator()
                
                ai_generator = st.session_state.ai_generator
                progress_bar.progress(20)
                
                # Configurar proveedor
                add_log(f"🔌 Configurando proveedor {ai_provider} con modelo {ai_model}")
                success = ai_generator.set_provider(
                    provider_type=ai_provider.lower(),
                    api_key=ai_api_key,
                    model=ai_model
                )
                
                if not success:
                    add_log("❌ Error: No se pudo configurar el proveedor")
                    st.error(f"❌ No se pudo conectar con {ai_provider}. Verifica tu API key.")
                    return
                
                add_log("✅ Proveedor configurado correctamente")
                progress_bar.progress(40)
                
                # Generar anuncio
                add_log("🤖 Enviando solicitud a la IA...")
                generated = ai_generator.generate_ad(
                    keywords=keywords_to_use,
                    num_ads=1,
                    num_headlines=num_headlines,
                    num_descriptions=4,
                    tone=tone,
                    user=st.session_state.get('user_login', 'saltbalente'),
                    validate=True,
                    business_type=business_type
                )
                
                progress_bar.progress(80)
                
                # ✅ LOG DETALLADO
                add_log(f"🔍 Resultado de generate_ad:")
                add_log(f"   - Tipo: {type(generated)}")
                add_log(f"   - Es None: {generated is None}")
                add_log(f"   - Longitud: {len(generated) if generated else 'N/A'}")
                logger.info(f"🔍 Resultado de generate_ad:")
                logger.info(f"   - Tipo: {type(generated)}")
                logger.info(f"   - Es None: {generated is None}")
                logger.info(f"   - Longitud: {len(generated) if generated else 'N/A'}")

                if generated:
                    add_log(f"   - Primer elemento: {type(generated[0]) if len(generated) > 0 else 'lista vacía'}")
                    logger.info(f"   - Primer elemento: {type(generated[0]) if len(generated) > 0 else 'lista vacía'}")

                # ✅ VERIFICACIÓN DETALLADA
                if not generated:
                    add_log("❌ `generated` es None")
                    st.error("❌ `generated` es None")
                    st.write("La función generate_ad() retornó None")
                    return

                if len(generated) == 0:
                    add_log("❌ `generated` es una lista vacía")
                    st.error("❌ `generated` es una lista vacía")
                    st.write("La función retornó [] (lista sin elementos)")
                    return
                
                # Obtener anuncio generado
                ad_data = generated[0]
                add_log("📦 Procesando respuesta de la IA...")
                progress_bar.progress(90)
                
                # ✅ MOSTRAR SI HAY ERROR
                if 'error' in ad_data and ad_data['error']:
                    add_log(f"❌ Error del generador: {ad_data['error']}")
                    st.error(f"❌ Error del generador: {ad_data['error']}")
                    
                    with st.expander("📋 Detalles Completos", expanded=True):
                        st.json(ad_data)
                    
                    return
                
                # ✅ VERIFICAR CONTENIDO
                if not ad_data.get('headlines') or len(ad_data.get('headlines', [])) == 0:
                    add_log("❌ No se generaron títulos")
                    st.error("❌ No se generaron títulos")
                    st.json(ad_data)
                    return

                if not ad_data.get('descriptions') or len(ad_data.get('descriptions', [])) == 0:
                    add_log("❌ No se generaron descripciones")
                    st.error("❌ No se generaron descripciones")
                    st.json(ad_data)
                    return
                
                if 'error' in ad_data:
                    add_log(f"❌ Error en generación: {ad_data['error']}")
                    st.error(f"❌ Error: {ad_data['error']}")
                    
                    # Mostrar información de debug si está disponible
                    if 'debug_info' in ad_data:
                        debug_info = ad_data['debug_info']
                        
                        with st.expander("🔍 Información de Debug Detallada", expanded=True):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write("**📊 Información del Error:**")
                                st.write(f"• **Tipo:** {debug_info.get('error_type', 'Desconocido')}")
                                st.write(f"• **Proveedor:** {ai_provider}")
                                st.write(f"• **Modelo:** {ai_model}")
                                st.write(f"• **Keywords:** {len(keywords_to_use)} palabras")
                                
                                if 'suggestion' in debug_info:
                                    st.info(f"💡 **Sugerencia:** {debug_info['suggestion']}")
                            
                            with col2:
                                st.write("**🔧 Parámetros de Generación:**")
                                st.write(f"• **Títulos solicitados:** {num_headlines}")
                                st.write(f"• **Descripciones:** 4")
                                st.write(f"• **Tono:** {tone}")
                                st.write(f"• **Tipo de negocio:** {business_type}")
                            
                            if 'raw_content' in debug_info and debug_info['raw_content']:
                                st.write("**📄 Contenido Raw Recibido:**")
                                st.code(debug_info['raw_content'], language='json')
                            
                            if 'keywords' in debug_info:
                                st.write("**🔑 Keywords Utilizadas:**")
                                st.write(', '.join(debug_info['keywords']))
                            
                            if 'full_error' in debug_info:
                                st.write("**🚨 Error Técnico Completo:**")
                                st.code(debug_info['full_error'], language='text')
                            
                            # Mostrar logs completos
                            st.write("**📋 Log Completo de la Sesión:**")
                            st.code("\n".join(logs), language="text")
                    
                    return
                
                add_log("✅ Anuncio generado exitosamente!")
                progress_bar.progress(100)
                
                # ✅ TODO OK - Guardar en session state para mostrarlo
                st.session_state.generated_ad_for_group = ad_data
                st.success(f"✅ Anuncio generado!")
                st.balloons()
                
                # Limpiar logs después del éxito
                time.sleep(1)
                log_container.empty()
                progress_bar.empty()
                st.rerun()
                
            except Exception as e:
                add_log(f"💥 Excepción crítica: {str(e)}")
                st.error(f"❌ Error generando anuncio: {e}")
                logger.error(f"Error en modal de generación: {e}", exc_info=True)
                
                # Mostrar debug completo en caso de excepción
                with st.expander("🔍 Debug de Excepción", expanded=True):
                    st.write("**🚨 Información de la Excepción:**")
                    st.code(str(e), language='text')
                    st.write("**📋 Log Completo:**")
                    st.code("\n".join(logs), language="text")
                    
                    import traceback
                    st.write("**🔍 Traceback Completo:**")
                    st.code(traceback.format_exc(), language='text')
    
    # Mostrar anuncio generado si existe
    if 'generated_ad_for_group' in st.session_state and st.session_state.generated_ad_for_group:
        st.markdown("---")
        st.markdown("### 📊 Anuncio Generado")
        
        ad = st.session_state.generated_ad_for_group
        validation = ad.get('validation_result', {})
        
        # Resumen de validación
        if validation:
            summary = validation.get('summary', {})
            
            col_val1, col_val2, col_val3 = st.columns(3)
            
            with col_val1:
                st.metric("✅ Títulos Válidos", summary.get('valid_headlines', 0))
            
            with col_val2:
                st.metric("✅ Desc. Válidas", summary.get('valid_descriptions', 0))
            
            with col_val3:
                is_valid = validation.get('valid', False)
                st.metric("Estado", "✅ Válido" if is_valid else "⚠️ Con advertencias")
        
        st.markdown("---")
        
        # Mostrar títulos
        st.markdown("#### 📝 Títulos Generados")
        
        # VALIDACIÓN VISUAL DE TÍTULOS
        titles_with_issues = []
        for i, headline in enumerate(ad['headlines'][:10], 1):
            char_count = len(headline)
            
            # Determinar color según longitud
            if char_count > 30:
                color = "🔴"  # Rojo - excede límite
                titles_with_issues.append(f"Título {i}: {char_count} caracteres (excede 30)")
            elif char_count > 25:
                color = "🟡"  # Amarillo - cerca del límite
            else:
                color = "🟢"  # Verde - dentro del límite
            
            st.markdown(f"{color} **{i}.** {headline} `({char_count}/30 chars)`")
        
        if len(ad['headlines']) > 10:
            st.caption(f"... y {len(ad['headlines']) - 10} títulos más")
        
        # Mostrar advertencias de títulos si las hay
        if titles_with_issues:
            with st.expander("⚠️ Advertencias de Títulos", expanded=True):
                st.warning("Los siguientes títulos exceden el límite de 30 caracteres:")
                for issue in titles_with_issues:
                    st.text(f"• {issue}")
        
        st.markdown("---")
        
        # Mostrar descripciones
        st.markdown("#### 📄 Descripciones Generadas")
        
        # VALIDACIÓN VISUAL DE DESCRIPCIONES
        descriptions_with_issues = []
        for i, description in enumerate(ad['descriptions'], 1):
            char_count = len(description)
            
            # Determinar color según longitud
            if char_count > 90:
                color = "🔴"  # Rojo - excede límite
                descriptions_with_issues.append(f"Descripción {i}: {char_count} caracteres (excede 90)")
            elif char_count > 80:
                color = "🟡"  # Amarillo - cerca del límite
            else:
                color = "🟢"  # Verde - dentro del límite
            
            st.markdown(f"{color} **{i}.** {description} `({char_count}/90 chars)`")
        
        # Mostrar advertencias de descripciones si las hay
        if descriptions_with_issues:
            with st.expander("⚠️ Advertencias de Descripciones", expanded=True):
                st.warning("Las siguientes descripciones exceden el límite de 90 caracteres:")
                for issue in descriptions_with_issues:
                    st.text(f"• {issue}")
        
        # Resumen visual de validación
        total_issues = len(titles_with_issues) + len(descriptions_with_issues)
        if total_issues > 0:
            st.error(f"⚠️ Se encontraron {total_issues} elementos que exceden los límites de caracteres. Estos elementos pueden ser rechazados por Google Ads.")
        else:
            st.success("✅ Todos los elementos cumplen con los límites de caracteres de Google Ads.")
        
        st.markdown("---")
        
        # URL de destino
        st.markdown("### 🔗 URL de Destino")
        
        col_url, col_paths = st.columns([2, 1])
        
        with col_url:
            final_url = st.text_input(
                "URL Final *",
                placeholder="https://www.ejemplo.com/producto",
                key="modal_final_url"
            )
        
        with col_paths:
            path1 = st.text_input("Ruta 1 (max 15)", max_chars=15, key="modal_path1")
            path2 = st.text_input("Ruta 2 (max 15)", max_chars=15, key="modal_path2")
        
        st.markdown("---")
        
        # Botones de acción
        col_pub, col_cancel_pub = st.columns([2, 1])
        
        with col_pub:
            if st.button(
                "🚀 PUBLICAR AL GRUPO",
                use_container_width=True,
                type="primary",
                disabled=not final_url,
                key="modal_publish_btn"
            ):
                if not final_url:
                    st.error("❌ Ingresa una URL de destino")
                else:
                    with st.spinner("⏳ Publicando anuncio a Google Ads..."):
                        try:
                            # Obtener servicio
                            ad_group_service = st.session_state.ad_group_service
                            
                            # Crear anuncio
                            result = ad_group_service.create_ad_in_ad_group(
                                customer_id=customer_id,
                                ad_group_id=ad_group_id,
                                headlines=ad['headlines'],
                                descriptions=ad['descriptions'],
                                final_url=final_url,
                                path1=path1,
                                path2=path2
                            )
                            
                            if result['success']:
                                st.success(f"✅ {result['message']}")
                                
                                # Limpiar estado
                                del st.session_state.generated_ad_for_group
                                st.session_state.show_ai_generator_modal_for_group = False
                                
                                st.balloons()
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error(f"❌ Error: {result['error']}")
                                
                                if 'details' in result:
                                    with st.expander("Ver detalles del error"):
                                        for detail in result['details']:
                                            st.error(detail)
                        
                        except Exception as e:
                            st.error(f"❌ Error publicando anuncio: {e}")
                            logger.error(f"Error publicando: {e}", exc_info=True)
        
        with col_cancel_pub:
            if st.button("🗑️ Descartar", use_container_width=True, key="modal_discard_btn"):
                del st.session_state.generated_ad_for_group
                st.session_state.show_ai_generator_modal_for_group = False
                st.rerun()

if __name__ == "__main__":
    main()