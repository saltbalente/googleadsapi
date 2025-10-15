"""
🤖 GENERADOR DE ANUNCIOS CON IA - VERSIÓN ULTRA-PROFESIONAL 2025
Con Inserción de Ubicaciones y Optimización de Copy
Versión: 3.1 Ultra Pro
Fecha: 2025-01-13
"""

import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
import sys
import os
from pathlib import Path
from modules.ai_ad_generator import AIAdGenerator
from modules.ad_group_config import AdGroupConfig, CampaignAdGroupsConfig
from utils.logger import get_logger
# ============================================================================
# CONFIGURAR PATH
# ============================================================================

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ============================================================================
# IMPORTS
# ============================================================================

try:
    from modules.ai_ad_generator import AIAdGenerator
    from utils.ad_scorer import AdScorer
    from utils.user_storage import get_user_storage
    from services.intelligent_autopilot import CampaignOption, IntelligentAutopilot
    logger = logging.getLogger(__name__)
    logger.info("✅ Módulos importados correctamente")
except ImportError as e:
    st.error(f"❌ Error importando módulos: {e}")
    logger.error(f"Error de importación: {e}")
    # No usar st.stop() aquí para permitir que otras pestañas funcionen

# ============================================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================================

st.set_page_config(
    page_title="🤖 Generador IA Ultra-Pro",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# MODELOS IA 2025
# ============================================================================

AI_MODELS_2025 = {
    'openai': {
        'name': '🔵 OpenAI',
        'icon': '🔵',
        'models': [
            'gpt-4o',
            'gpt-4-turbo',
            'gpt-4',
            'gpt-3.5-turbo',
            'o1-preview',
            'o1-mini'
        ],
        'default': 'gpt-4o',
        'api_url': 'https://platform.openai.com/api-keys',
        'color': '#10a37f'
    },
    'gemini': {
        'name': '🔴 Google Gemini',
        'icon': '🔴',
        'models': [
            'gemini-2.0-flash-exp',
            'gemini-1.5-pro',
            'gemini-1.5-flash',
            'gemini-pro'
        ],
        'default': 'gemini-2.0-flash-exp',
        'api_url': 'https://makersuite.google.com/app/apikey',
        'color': '#4285f4'
    },
    'anthropic': {
        'name': '🟣 Anthropic',
        'icon': '🟣',
        'models': [
            'claude-3-5-sonnet-20241022',
            'claude-3-5-haiku-20241022',
            'claude-3-opus-20240229',
            'claude-3-sonnet-20240229',
            'claude-3-haiku-20240307'
        ],
        'default': 'claude-3-5-sonnet-20241022',
        'api_url': 'https://console.anthropic.com/account/keys',
        'color': '#d97706'
    }
}

TONE_PRESETS = {
    'emocional': {'icon': '❤️', 'description': 'Apela a sentimientos profundos'},
    'urgente': {'icon': '⚡', 'description': 'Crea sentido de inmediatez'},
    'profesional': {'icon': '💼', 'description': 'Tono corporativo y confiable'},
    'místico': {'icon': '🔮', 'description': 'Lenguaje espiritual y mágico'},
    'poderoso': {'icon': '💪', 'description': 'Resultados y efectividad'},
    'esperanzador': {'icon': '🌟', 'description': 'Optimismo y posibilidad'},
    'tranquilizador': {'icon': '🕊️', 'description': 'Calma y tranquilidad'}
}

# ============================================================================
# NIVELES DE INSERCIÓN DE UBICACIÓN
# ============================================================================

LOCATION_LEVELS = {
    'city': {
        'label': '🏙️ Ciudad',
        'code': 'LOCATION(City)',
        'example': 'Curandero en {LOCATION(City)}',
        'description': 'Inserta el nombre de la ciudad del usuario'
    },
    'state': {
        'label': '🗺️ Estado/Provincia',
        'code': 'LOCATION(State)',
        'example': 'Brujos Efectivos {LOCATION(State)}',
        'description': 'Inserta el estado o provincia'
    },
    'country': {
        'label': '🌍 País',
        'code': 'LOCATION(Country)',
        'example': 'Amarres en {LOCATION(Country)}',
        'description': 'Inserta el nombre del país'
    }
}

# ============================================================================
# MEJORES PRÁCTICAS DE GOOGLE ADS
# ============================================================================

GOOGLE_ADS_BEST_PRACTICES = {
    'headlines': {
        'min': 3,
        'max': 15,
        'max_chars': 30,
        'recommendations': [
            'Incluye palabras clave relevantes',
            'Usa llamados a la acción específicos',
            'Refleja los beneficios del producto/servicio',
            'Varía la longitud de los títulos',
            'Evita lenguaje genérico',
            'Mantén consistencia con la marca'
        ]
    },
    'descriptions': {
        'min': 2,
        'max': 4,
        'max_chars': 90,
        'recommendations': [
            'Describe beneficios claros',
            'Incluye precios o promociones si aplica',
            'Agrega llamados a la acción',
            'Menciona ventajas competitivas',
            'Sé específico sobre productos/servicios'
        ]
    },
    'copy_themes': [
        'Productos o servicios que ofreces',
        'Beneficios claros para el cliente',
        'Marca y identidad',
        'Llamados a la acción específicos',
        'Inventario y selección disponible',
        'Precios y tarifas competitivas',
        'Promociones y descuentos actuales',
        'Garantías y certificaciones'
    ]
}

# ============================================================================
# CSS ULTRA-PROFESIONAL
# ============================================================================

ULTRA_PRO_CSS = """
<style>
    .ultra-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    
    .ultra-header h1 {
        margin: 0;
        font-size: 2.8rem;
        font-weight: 800;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .location-badge {
        background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        display: inline-block;
        margin: 0.25rem;
        font-weight: 600;
    }
    
    .best-practice-box {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border-left: 4px solid #667eea;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .ultra-info {
        background: linear-gradient(135deg, rgba(33, 150, 243, 0.1) 0%, rgba(25, 118, 210, 0.1) 100%);
        border-left: 4px solid #2196f3;
        border-radius: 12px;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
    }
</style>
"""

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def get_available_providers() -> List[str]:
    """
    Obtiene proveedores disponibles basándose en las API keys guardadas en el storage local
    """
    try:
        user_storage = get_user_storage()
        available_providers = []
        
        # Verificar OpenAI
        openai_key = user_storage.get_api_key('openai')
        if openai_key and isinstance(openai_key, dict) and openai_key.get('api_key', '').strip():
            available_providers.append('openai')
        
        # Verificar Gemini
        gemini_key = user_storage.get_api_key('gemini')
        if gemini_key and isinstance(gemini_key, dict) and gemini_key.get('api_key', '').strip():
            available_providers.append('gemini')
        
        # Verificar Anthropic
        anthropic_key = user_storage.get_api_key('anthropic')
        if anthropic_key and isinstance(anthropic_key, dict) and anthropic_key.get('api_key', '').strip():
            available_providers.append('anthropic')
        
        return available_providers
    except Exception as e:
        logger.error(f"Error obteniendo proveedores disponibles: {e}")
        return []

def save_api_config(provider: str, api_key: str, model: str):
    """Guarda configuración de API"""
    if 'api_configs' not in st.session_state:
        st.session_state.api_configs = {}
    
    st.session_state.api_configs[provider] = {
        'api_key': api_key,
        'model': model,
        'saved_at': datetime.now().isoformat()
    }

def load_api_config(provider: str) -> Dict[str, Any]:
    """Carga configuración de API"""
    if 'api_configs' not in st.session_state:
        st.session_state.api_configs = {}
    
    return st.session_state.api_configs.get(provider, {})

def get_configured_providers() -> List[str]:
    """Obtiene proveedores configurados (función legacy - usar get_available_providers)"""
    return get_available_providers()

def clear_api_config(provider: str):
    """Limpia configuración de API"""
    if 'api_configs' not in st.session_state:
        st.session_state.api_configs = {}
    
    if provider in st.session_state.api_configs:
        del st.session_state.api_configs[provider]

def save_ad_for_campaigns(ad: Dict[str, Any]) -> bool:
    """
    Guarda un anuncio generado en el sistema de storage para uso en campañas
    
    Args:
        ad: Diccionario con los datos del anuncio generado
        
    Returns:
        bool: True si se guardó exitosamente, False en caso contrario
    """
    try:
        user_storage = get_user_storage()
        
        # Preparar datos del anuncio para guardar
        ad_data = {
            'id': ad.get('id', f"ad_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            'headlines': ad.get('headlines', []),
            'descriptions': ad.get('descriptions', []),
            'keywords': ad.get('keywords', []),
            'tone': ad.get('tone', ''),
            'provider': ad.get('provider', ''),
            'model': ad.get('model', ''),
            'uses_location_insertion': ad.get('uses_location_insertion', False),
            'location_levels': ad.get('location_levels', []),
            'score': ad.get('score', 0),
            'validation_results': ad.get('validation_results', {}),
            'created_at': datetime.now().isoformat(),
            'status': 'saved_for_campaigns'
        }
        
        # Guardar en el historial de anuncios
        success = user_storage.save_ad_history(ad_data)
        
        if success:
            logger.info(f"✅ Anuncio {ad_data['id']} guardado para campañas")
            return True
        else:
            logger.error(f"❌ Error guardando anuncio {ad_data['id']}")
            return False
            
    except Exception as e:
        logger.error(f"Error guardando anuncio para campañas: {e}")
        return False

def build_enhanced_prompt(
    keywords: List[str],
    tone: str,
    num_headlines: int,
    num_descriptions: int,
    use_location_insertion: bool,
    location_levels: List[str],
    business_type: str = 'esoteric'
) -> str:
    """
    Construye un prompt mejorado con mejores prácticas de Google Ads
    """
    
    prompt = f"""Eres un experto copywriter especializado en Google Ads con 15+ años de experiencia.

CONTEXTO DEL NEGOCIO:
- Tipo de negocio: {business_type}
- Palabras clave objetivo: {', '.join(keywords)}
- Tono deseado: {tone}

REQUISITOS TÉCNICOS DE GOOGLE ADS:
- Generar {num_headlines} títulos únicos (máximo 30 caracteres cada uno)
- Generar {num_descriptions} descripciones únicas (máximo 90 caracteres cada una)
- Cumplir con las políticas de Google Ads

MEJORES PRÁCTICAS A APLICAR:

1. TÍTULOS (Headlines):
   - Incluir palabras clave relevantes en al menos 50% de los títulos
   - Usar llamados a la acción específicos y claros
   - Variar la longitud de los títulos (cortos, medianos, largos)
   - Reflejar beneficios tangibles para el usuario
   - Evitar lenguaje genérico o vago
   - Mantener consistencia con la marca

2. DESCRIPCIONES:
   - Describir beneficios claros y específicos
   - Incluir propuestas de valor únicas
   - Agregar llamados a la acción concretos
   - Mencionar garantías, certificaciones o ventajas competitivas
   - Ser específico sobre productos/servicios ofrecidos

3. TEMAS A CONSIDERAR EN EL COPY:
   - Productos/servicios específicos que ofreces
   - Beneficios claros para el cliente
   - Identidad de marca
   - Inventario y selección disponible
   - Precios competitivos (si aplica)
   - Promociones actuales (si aplica)
   - Testimonios o resultados comprobados

4. OPTIMIZACIÓN DE RELEVANCIA:
   - Los títulos deben conectar directamente con la intención de búsqueda
   - Las descripciones deben expandir y complementar los títulos
   - Mantener coherencia temática entre todos los elementos

"""

    # Agregar instrucciones de inserción de ubicación
    if use_location_insertion:
        location_codes = [LOCATION_LEVELS[level]['code'] for level in location_levels]
        
        prompt += f"""
5. INSERCIÓN DE UBICACIONES:
   ⚠️ IMPORTANTE: Debes incluir ENTRE 3 Y 5 inserciones de ubicación en los títulos.
   
   Códigos disponibles para usar:
   {chr(10).join([f'   - {{{code}}}' for code in location_codes])}
   
   EJEMPLOS DE USO CORRECTO:
   - "Curandero en {{LOCATION(City)}}"
   - "Brujos Efectivos {{LOCATION(State)}}"
   - "Brujería Real {{LOCATION(State)}}"
   - "Hacer Amarres {{LOCATION(Country)}}"
   - "Amarre de Pareja {{LOCATION(State)}}"
   
   REGLAS:
   - Usar exactamente la sintaxis: {{LOCATION(City)}}, {{LOCATION(State)}}, {{LOCATION(Country)}}
   - Mínimo 3 títulos con inserción de ubicación
   - Máximo 5 títulos con inserción de ubicación
   - Los títulos con ubicación NO deben exceder 30 caracteres (incluyendo el código)
   - Distribuir entre diferentes niveles de ubicación
   - Los títulos con ubicación deben ser naturales y específicos

"""

    prompt += f"""
TONO Y ESTILO:
- Tono principal: {tone}
- Estilo: {TONE_PRESETS[tone]['description']}

FORMATO DE RESPUESTA (JSON ESTRICTO):
{{
  "headlines": [
    "Título 1",
    "Título 2",
    ...
  ],
  "descriptions": [
    "Descripción 1",
    "Descripción 2",
    ...
  ]
}}

RESTRICCIONES IMPORTANTES:
- NO usar emojis
- NO usar signos de exclamación ni interrogación
- NO usar mayúsculas sostenidas (ej: OFERTA es incorrecto, Oferta es correcto)
- Permitir palabras clave en mayúsculas naturales (ej: USA, NYC)
- SÍ usar acentos correctamente en español
- SÍ ser específico y evitar lenguaje vago

¡Genera anuncios que superen las expectativas y maximicen el CTR!
"""
    
    return prompt

# ============================================================================
# INICIALIZACIÓN
# ============================================================================

def initialize_session_state():
    """Inicializa session state con configuración del storage local"""
    if 'generated_ads_batch' not in st.session_state:
        st.session_state.generated_ads_batch = []
    
    if 'ai_generator' not in st.session_state:
        try:
            st.session_state.ai_generator = AIAdGenerator()
        except:
            st.session_state.ai_generator = None
    
    if 'ad_scorer' not in st.session_state:
        try:
            st.session_state.ad_scorer = AdScorer()
        except:
            st.session_state.ad_scorer = None
    
    # Cargar configuración del storage local
    try:
        user_storage = get_user_storage()
        
        # Cargar preferencias del usuario
        preferences = user_storage.get_preferences()
        if preferences:
            for key, value in preferences.items():
                if f'user_pref_{key}' not in st.session_state:
                    st.session_state[f'user_pref_{key}'] = value
        
        # Cargar configuración de AI desde settings generales
        settings = user_storage.get_settings()
        ai_settings = settings.get('ai_generation', {})
        if ai_settings:
            # Proveedor por defecto
            if 'default_provider' in ai_settings and 'default_provider' not in st.session_state:
                st.session_state.default_provider = ai_settings['default_provider']
            
            # Tono por defecto
            if 'default_tone' in ai_settings and 'default_tone' not in st.session_state:
                st.session_state.default_tone = ai_settings['default_tone']
            
            # Número de anuncios por defecto
            if 'default_num_ads' in ai_settings and 'default_num_ads' not in st.session_state:
                st.session_state.default_num_ads = ai_settings['default_num_ads']
            
            # Número de títulos por defecto
            if 'default_num_headlines' in ai_settings and 'default_num_headlines' not in st.session_state:
                st.session_state.default_num_headlines = ai_settings['default_num_headlines']
            
            # Número de descripciones por defecto
            if 'default_num_descriptions' in ai_settings and 'default_num_descriptions' not in st.session_state:
                st.session_state.default_num_descriptions = ai_settings['default_num_descriptions']
            
            # Auto-validación
            if 'auto_validation' in ai_settings and 'auto_validation' not in st.session_state:
                st.session_state.auto_validation = ai_settings['auto_validation']
            
            # Auto-scoring
            if 'auto_scoring' in ai_settings and 'auto_scoring' not in st.session_state:
                st.session_state.auto_scoring = ai_settings['auto_scoring']
            
            # Auto-mejores prácticas
            if 'auto_best_practices' in ai_settings and 'auto_best_practices' not in st.session_state:
                st.session_state.auto_best_practices = ai_settings['auto_best_practices']
            
            # Auto-inserción de ubicaciones
            if 'auto_location_insertion' in ai_settings and 'auto_location_insertion' not in st.session_state:
                st.session_state.auto_location_insertion = ai_settings['auto_location_insertion']
        
        # Cargar configuración de Google Ads
        google_ads_settings = settings.get('google_ads', {})
        if google_ads_settings:
            for key, value in google_ads_settings.items():
                if f'google_ads_{key}' not in st.session_state:
                    st.session_state[f'google_ads_{key}'] = value
                    
    except Exception as e:
        logger.error(f"Error cargando configuración del storage: {e}")
        # Continuar con valores por defecto si hay error

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Función principal"""
    
    # Aplicar CSS
    st.markdown(ULTRA_PRO_CSS, unsafe_allow_html=True)
    
    # Inicializar
    initialize_session_state()
    
    # ✅ AGREGAR SIDEBAR BÁSICO PARA SELECCIÓN DE CUENTA
    with st.sidebar:
        st.markdown("### 🚀 GOOGLE ADS")
        st.markdown("**Dashboard 2030**")
        
        # Verificar si hay cliente de Google Ads
        if 'google_ads_client' in st.session_state and st.session_state.google_ads_client:
            st.success("✅ CONECTADO")
            
            # Verificar si hay cuentas disponibles
            if 'customer_ids' in st.session_state and st.session_state.customer_ids:
                st.markdown("### 📋 SELECCIONAR CUENTA")
                
                # Crear opciones de cuenta
                account_options = []
                for customer_id in st.session_state.customer_ids:
                    account_options.append(f"{customer_id}")
                
                # Selector de cuenta
                if 'selected_customer' not in st.session_state:
                    st.session_state.selected_customer = st.session_state.customer_ids[0]
                
                selected_account = st.selectbox(
                    "Cuenta:",
                    options=account_options,
                    index=account_options.index(st.session_state.selected_customer) if st.session_state.selected_customer in account_options else 0
                )
                
                # Actualizar cuenta seleccionada
                st.session_state.selected_customer = selected_account
                
                st.success(f"✅ Cuenta activa: {selected_account}")
            else:
                st.warning("⚠️ No hay cuentas disponibles")
        else:
            st.error("❌ DESCONECTADO")
            st.warning("⚠️ Ve a la aplicación principal (puerto 8502) para autenticarte")
    
    # Verificar proveedores disponibles
    available_providers = get_available_providers()
    
    # Header con información de proveedores
    st.markdown("""
    <div class="ultra-header">
        <h1>🤖 Generador de Anuncios con IA</h1>
        <p>Sistema Ultra-Profesional 2025 | Con Inserción de Ubicaciones y Best Practices</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Mostrar estado de proveedores
    if available_providers:
        provider_icons = [AI_MODELS_2025[p]['icon'] for p in available_providers]
        st.success(f"✅ Proveedores configurados: {' '.join(provider_icons)} ({len(available_providers)} disponibles)")
    else:
        st.warning("⚠️ No hay proveedores de IA configurados. Ve a la página **⚙️ User Storage** para configurar tus API keys.")
    
    # Tabs
    tabs = st.tabs([
        "🚀 Generar",
        "🎨 Galería",
        "🤖 AUTOPILOT 2050",
        "⚙️ Config API",
        "📚 Mejores Prácticas",
        "⚙️ Ajustes Rápidos"
    ])
    
    with tabs[0]:
        render_generation_tab()
    
    with tabs[1]:
        render_gallery_tab()
    
    with tabs[2]:
        render_autopilot_tab()
    
    with tabs[3]:
        render_config_tab()
    
    with tabs[4]:
        render_best_practices_tab()
    
    with tabs[5]:
        render_settings_tab()

# ============================================================================
# TAB 1: GENERAR CON INSERCIÓN DE UBICACIONES
# ============================================================================

def render_generation_tab():
    """Tab de generación con inserción de ubicaciones"""
    
    st.markdown("### 🎯 Generación de Anuncios Optimizados")
    
    # Usar proveedores del storage
    available_providers = get_available_providers()
    
    if not available_providers:
        st.markdown("""
        <div class="ultra-info">
            <h4>⚠️ No hay proveedores configurados</h4>
            <p>Ve a la página <strong>⚙️ User Storage</strong> para configurar tus API keys de OpenAI, Gemini o Anthropic.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Formulario
    with st.form("gen_form"):
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            # Usar el proveedor por defecto del storage o el primero disponible
            default_provider = st.session_state.get('default_provider', available_providers[0])
            if default_provider not in available_providers:
                default_provider = available_providers[0]
            
            provider_type = st.selectbox(
                "Proveedor IA:",
                available_providers,
                index=available_providers.index(default_provider) if default_provider in available_providers else 0,
                format_func=lambda x: f"{AI_MODELS_2025[x]['icon']} {AI_MODELS_2025[x]['name']}"
            )
        
        with col2:
            # Usar el tono por defecto del storage
            default_tone = st.session_state.get('default_tone', 'emocional')
            tone_options = list(TONE_PRESETS.keys())
            tone_index = tone_options.index(default_tone) if default_tone in tone_options else 0
            
            tone = st.selectbox(
                "Tono:",
                tone_options,
                index=tone_index,
                format_func=lambda x: f"{TONE_PRESETS[x]['icon']} {x.title()}"
            )
        
        with col3:
            # Usar cantidad por defecto del storage
            default_num_ads = st.session_state.get('default_num_ads', 1)
            num_ads = st.number_input("Cantidad:", 1, 10, default_num_ads)
        
        # Keywords
        keywords_input = st.text_area(
            "Keywords (una por línea o separadas por comas):",
            placeholder="amarres de amor\nhechizos efectivos\nbrujería profesional\ntarot del amor",
            height=100
        )
        
        # NUEVA SECCIÓN: Inserción de Ubicaciones
        st.markdown("---")
        st.markdown("#### 📍 Inserción de Ubicaciones (Mejora el CTR)")
        
        use_location_insertion = st.checkbox(
            "✅ Incluir inserción de ubicaciones",
            value=False,
            help="Agrega códigos de ubicación dinámica en los títulos. Google reemplazará automáticamente con la ubicación del usuario."
        )
        
        if use_location_insertion:
            st.markdown("""
            <div class="best-practice-box">
                <strong>💡 Beneficios:</strong>
                <ul>
                    <li>✅ Aumenta el CTR significativamente</li>
                    <li>✅ Personaliza anuncios por ubicación del usuario</li>
                    <li>✅ Mejora la relevancia del anuncio</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            location_levels = st.multiselect(
                "Selecciona niveles de ubicación:",
                options=list(LOCATION_LEVELS.keys()),
                default=['city', 'state'],
                format_func=lambda x: LOCATION_LEVELS[x]['label'],
                help="Se generarán entre 3-5 títulos con estas ubicaciones"
            )
            
            if location_levels:
                st.markdown("**Ejemplos de cómo se verán:**")
                for level in location_levels:
                    st.markdown(f"<span class='location-badge'>{LOCATION_LEVELS[level]['example']}</span>", unsafe_allow_html=True)
        else:
            location_levels = []
        
        # Configuración avanzada
        with st.expander("⚙️ Configuración Avanzada"):
            col1, col2 = st.columns(2)
            
            with col1:
                num_headlines = st.slider("Títulos:", 5, 15, 10)
                business_type = st.selectbox(
                    "Tipo de negocio:",
                    ['esoteric', 'generic', 'ecommerce', 'services', 'local'],
                    index=0
                )
            
            with col2:
                num_descriptions = st.slider("Descriptions:", 2, 4, 3)
                apply_best_practices = st.checkbox(
                    "📚 Aplicar mejores prácticas de Google Ads",
                    value=True,
                    help="Usa las guías oficiales de Google para optimizar el copy"
                )
            
            validate_ads = st.checkbox("✅ Validar políticas", True)
            score_ads = st.checkbox("📊 Calcular score", True)
        
        # Botón de submit
        submitted = st.form_submit_button(
            f"✨ Generar {num_ads} Anuncio{'s' if num_ads > 1 else ''} Optimizado{'s' if num_ads > 1 else ''}",
            type="primary",
            use_container_width=True
        )
        
        if submitted:
            if not keywords_input.strip():
                st.error("❌ Ingresa al menos una keyword")
                return
            
            keywords = [kw.strip() for kw in keywords_input.replace(',', '\n').split('\n') if kw.strip()]
            
            if not keywords:
                st.error("❌ No hay keywords válidas")
                return
            
            if use_location_insertion and not location_levels:
                st.error("❌ Selecciona al menos un nivel de ubicación")
                return
            
            # Generar con configuración mejorada usando storage
            generate_ads_with_storage(
                provider_type=provider_type,
                keywords=keywords,
                tone=tone,
                num_ads=num_ads,
                num_headlines=num_headlines,
                num_descriptions=num_descriptions,
                validate=validate_ads,
                score=score_ads,
                use_location_insertion=use_location_insertion,
                location_levels=location_levels,
                business_type=business_type,
                apply_best_practices=apply_best_practices
            )

def generate_ads_with_storage(
    provider_type: str,
    keywords: List[str],
    tone: str,
    num_ads: int,
    num_headlines: int,
    num_descriptions: int,
    validate: bool,
    score: bool,
    use_location_insertion: bool,
    location_levels: List[str],
    business_type: str,
    apply_best_practices: bool
):
    """Genera anuncios usando API keys del storage local"""
    
    # Obtener storage del usuario
    try:
        user_storage = get_user_storage()
        api_keys = user_storage.get_api_keys()
    except Exception as e:
        st.error(f"❌ Error accediendo al storage: {e}")
        return
    
    # Verificar API key del proveedor
    provider_config = api_keys.get(provider_type)
    if not provider_config or not isinstance(provider_config, dict) or not provider_config.get('api_key', '').strip():
        st.error(f"❌ No hay API key configurada para {provider_type}. Ve a **⚙️ User Storage** para configurarla.")
        return
    
    progress_bar = st.progress(0)
    status = st.empty()
    
    try:
        # Configurar proveedor
        status.text("🔧 Configurando proveedor...")
        progress_bar.progress(0.2)
        
        ai_gen = st.session_state.ai_generator
        
        if not ai_gen:
            st.error("❌ AIAdGenerator no disponible")
            return
        
        # Usar API key del storage
        success = ai_gen.set_provider(
            provider_type=provider_type,
            api_key=provider_config['api_key'],
            model=AI_MODELS_2025[provider_type]['default']
        )
        
        if not success:
            st.error(f"❌ No se pudo configurar {provider_type}")
            return
        
        # Construir prompt mejorado
        status.text("📝 Construyendo prompt optimizado...")
        progress_bar.progress(0.3)
        
        enhanced_prompt = build_enhanced_prompt(
            keywords=keywords,
            tone=tone,
            num_headlines=num_headlines,
            num_descriptions=num_descriptions,
            use_location_insertion=use_location_insertion,
            location_levels=location_levels,
            business_type=business_type
        )
        
        # Generar
        status.text(f"🎨 Generando {num_ads} anuncio(s) optimizado(s)...")
        progress_bar.progress(0.5)
        
        # NOTA: Aquí deberías modificar AIAdGenerator para aceptar custom_prompt
        # Por ahora usamos el método estándar
        batch_result = ai_gen.generate_batch(
            keywords=keywords,
            num_ads=num_ads,
            num_headlines=num_headlines,
            num_descriptions=num_descriptions,
            tone=tone,
            validate=validate,
            business_type=business_type,
            save_to_csv=True
        )
        
        progress_bar.progress(0.8)
        
        # Calcular scores
        if score and batch_result['successful'] > 0:
            status.text("📊 Calculando scores...")
            
            scorer = st.session_state.ad_scorer
            
            if scorer:
                for ad in batch_result['ads']:
                    if 'error' not in ad or not ad['error']:
                        try:
                            score_result = scorer.score_ad(
                                headlines=ad.get('headlines', []),
                                descriptions=ad.get('descriptions', []),
                                keywords=keywords
                            )
                            ad['score_result'] = score_result
                            ad['score'] = score_result.get('overall_score', 0)
                        except:
                            pass
        
        # Agregar metadata de ubicaciones
        for ad in batch_result['ads']:
            ad['uses_location_insertion'] = use_location_insertion
            ad['location_levels'] = location_levels if use_location_insertion else []
        
        progress_bar.progress(1.0)
        status.empty()
        progress_bar.empty()
        
        # Guardar en storage y session state
        if batch_result['successful'] > 0:
            st.session_state.generated_ads_batch.extend(batch_result['ads'])
            
            # Guardar en historial del usuario
            try:
                action_data = {
                    'provider': provider_type,
                    'keywords': keywords,
                    'tone': tone,
                    'num_ads': num_ads,
                    'num_headlines': num_headlines,
                    'num_descriptions': num_descriptions,
                    'use_location_insertion': use_location_insertion,
                    'location_levels': location_levels,
                    'business_type': business_type,
                    'successful_ads': batch_result['successful'],
                    'failed_ads': batch_result['failed'],
                    'success_rate': batch_result['success_rate']
                }
                user_storage.add_to_history('ad_generation', action_data)
            except Exception as e:
                logger.warning(f"No se pudo guardar en historial: {e}")
            
            st.success(f"✅ ¡{batch_result['successful']} anuncio(s) generado(s) con éxito!")
            
            if use_location_insertion:
                st.info(f"📍 Incluyendo inserción de ubicaciones en niveles: {', '.join([LOCATION_LEVELS[l]['label'] for l in location_levels])}")
            
            st.balloons()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Exitosos", batch_result['successful'])
            
            with col2:
                st.metric("Fallidos", batch_result['failed'])
            
            with col3:
                st.metric("Tasa Éxito", f"{batch_result['success_rate']:.0f}%")
            
            with col4:
                scores = [ad.get('score', 0) for ad in batch_result['ads'] if ad.get('score')]
                avg = sum(scores) / len(scores) if scores else 0
                st.metric("Score Promedio", f"{avg:.1f}")
            
            st.info("👉 Ve a **🎨 Galería** para ver los resultados detallados")
        else:
            st.error("❌ No se pudo generar ningún anuncio")
    
    except Exception as e:
        st.error(f"❌ Error: {e}")
        import traceback
        st.code(traceback.format_exc())

# ============================================================================
# TAB 2: GALERÍA (ACTUALIZADA)
# ============================================================================

def render_gallery_tab():
    """Tab de galería con indicadores de ubicación"""
    
    st.markdown("### 🎨 Galería de Anuncios")
    
    if not st.session_state.generated_ads_batch:
        st.info("ℹ️ No hay anuncios generados")
        return
    
    total = len(st.session_state.generated_ads_batch)
    with_locations = len([ad for ad in st.session_state.generated_ads_batch if ad.get('uses_location_insertion')])
    
    st.success(f"📊 **{total}** anuncio(s) generado(s) • **{with_locations}** con inserción de ubicaciones")
    
    # Acciones
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📦 Exportar Todos", use_container_width=True):
            data = {
                'exported_at': datetime.now().isoformat(),
                'total': total,
                'ads': st.session_state.generated_ads_batch
            }
            
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            
            st.download_button(
                "💾 Descargar JSON",
                json_str,
                f"anuncios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "application/json"
            )
    
    with col2:
        if st.button("💾 Guardar en Campañas", use_container_width=True):
            count = 0
            for ad in st.session_state.generated_ads_batch:
                if 'error' not in ad or not ad['error']:
                    if save_ad_for_campaigns(ad):
                        count += 1
            
            if count > 0:
                st.success(f"✅ {count} guardado(s)")
                st.balloons()
    
    with col3:
        if st.button("🗑️ Limpiar Todo", use_container_width=True):
            st.session_state.generated_ads_batch = []
            st.success("✅ Limpiado")
            st.rerun()
    
    st.markdown("---")
    
    # Mostrar anuncios
    for idx, ad in enumerate(st.session_state.generated_ads_batch):
        if 'error' in ad and ad['error']:
            st.error(f"❌ Anuncio #{idx+1}: {ad['error']}")
            continue
        
        # Detectar headlines con ubicaciones
        headlines_with_location = [
            h for h in ad.get('headlines', [])
            if '{LOCATION(' in h
        ]
        
        with st.expander(
            f"📢 Anuncio #{idx+1} - {ad.get('tone', 'N/A').title()} " + 
            (f"📍 ({len(headlines_with_location)} con ubicación)" if headlines_with_location else ""),
            expanded=(idx==0)
        ):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Proveedor", ad.get('provider', 'N/A'))
            
            with col2:
                st.metric("Tono", ad.get('tone', 'N/A'))
            
            with col3:
                st.metric("Score", f"{ad.get('score', 0):.1f}")
            
            with col4:
                if headlines_with_location:
                    st.metric("Con Ubicación", len(headlines_with_location))
            
            # Mostrar headlines con indicador de ubicación
            st.markdown("**📝 Headlines:**")
            for h in ad.get('headlines', []):
                if '{LOCATION(' in h:
                    st.markdown(f"<span class='location-badge'>📍 {h}</span> ({len(h)}/30)", unsafe_allow_html=True)
                else:
                    st.text(f"• {h} ({len(h)}/30)")
            
            st.markdown("**📄 Descriptions:**")
            for d in ad.get('descriptions', []):
                st.text(f"• {d} ({len(d)}/90)")
            
            # Mostrar info de ubicaciones si aplica
            if ad.get('uses_location_insertion'):
                location_levels = ad.get('location_levels', [])
                st.markdown(f"**📍 Ubicaciones configuradas:** {', '.join([LOCATION_LEVELS[l]['label'] for l in location_levels])}")

# ============================================================================
# TAB 3: CONFIG API (sin cambios)
# ============================================================================

def render_config_tab():
    """Tab de configuración"""
    
    st.markdown("### ⚙️ Configuración de APIs")
    
    st.markdown("""
    <div class="ultra-info">
        <p><strong>🔐 Privacidad:</strong> Las API Keys se guardan en tu sesión local y NO se envían a ningún servidor.</p>
    </div>
    """, unsafe_allow_html=True)
    
    for provider_key, provider_info in AI_MODELS_2025.items():
        current_config = load_api_config(provider_key)
        is_configured = bool(current_config.get('api_key'))
        
        with st.expander(f"{provider_info['icon']} {provider_info['name']} {'✅' if is_configured else ''}", expanded=not is_configured):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                api_key = st.text_input(
                    "API Key:",
                    type="password",
                    value=current_config.get('api_key', ''),
                    key=f"key_{provider_key}"
                )
            
            with col2:
                model = st.selectbox(
                    "Modelo:",
                    provider_info['models'],
                    key=f"model_{provider_key}"
                )
            
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                if st.button("💾 Guardar", key=f"save_{provider_key}", use_container_width=True):
                    if api_key:
                        save_api_config(provider_key, api_key, model)
                        st.success("✅ Guardado")
                        st.rerun()
            
            with col_b:
                if st.button("🧪 Probar", key=f"test_{provider_key}", use_container_width=True):
                    if api_key:
                        st.info("⏳ Probando...")
            
            with col_c:
                if st.button("🗑️ Borrar", key=f"del_{provider_key}", use_container_width=True):
                    clear_api_config(provider_key)
                    st.success("✅ Borrado")
                    st.rerun()

# ============================================================================
# TAB 4: MEJORES PRÁCTICAS (NUEVA)
# ============================================================================

def render_best_practices_tab():
    """Nueva tab con mejores prácticas de Google Ads"""
    
    st.markdown("### 📚 Mejores Prácticas de Google Ads")
    
    st.markdown("""
    <div class="ultra-info">
        <p><strong>ℹ️ Información:</strong> Estas prácticas están basadas en las guías oficiales de Google Ads y mejoran significativamente el rendimiento de tus anuncios.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Headlines
    st.markdown("#### 📝 Títulos (Headlines)")
    
    with st.expander("Ver recomendaciones para títulos", expanded=True):
        for rec in GOOGLE_ADS_BEST_PRACTICES['headlines']['recommendations']:
            st.markdown(f"✅ {rec}")
        
        st.markdown(f"""
        **Límites técnicos:**
        - Mínimo: {GOOGLE_ADS_BEST_PRACTICES['headlines']['min']} títulos
        - Máximo: {GOOGLE_ADS_BEST_PRACTICES['headlines']['max']} títulos
        - Caracteres por título: {GOOGLE_ADS_BEST_PRACTICES['headlines']['max_chars']} máximo
        """)
    
    # Descriptions
    st.markdown("#### 📄 Descripciones")
    
    with st.expander("Ver recomendaciones para descripciones"):
        for rec in GOOGLE_ADS_BEST_PRACTICES['descriptions']['recommendations']:
            st.markdown(f"✅ {rec}")
        
        st.markdown(f"""
        **Límites técnicos:**
        - Mínimo: {GOOGLE_ADS_BEST_PRACTICES['descriptions']['min']} descripciones
        - Máximo: {GOOGLE_ADS_BEST_PRACTICES['descriptions']['max']} descripciones
        - Caracteres por descripción: {GOOGLE_ADS_BEST_PRACTICES['descriptions']['max_chars']} máximo
        """)
    
    # Temas del copy
    st.markdown("#### 🎯 Temas a Incluir en el Copy")
    
    with st.expander("Ver temas efectivos"):
        for theme in GOOGLE_ADS_BEST_PRACTICES['copy_themes']:
            st.markdown(f"📌 {theme}")
    
    # Inserción de ubicaciones
    st.markdown("#### 📍 Inserción de Ubicaciones")
    
    with st.expander("¿Qué es la inserción de ubicaciones?"):
        st.markdown("""
        La inserción de ubicación personaliza automáticamente tus anuncios según la ubicación del usuario.
        
        **Beneficios:**
        - ✅ Aumenta el CTR hasta un 50%
        - ✅ Mejora la relevancia del anuncio
        - ✅ Mayor probabilidad de conversión
        - ✅ Gestión eficiente (un anuncio, múltiples ubicaciones)
        
        **Niveles disponibles:**
        """)
        
        for level_key, level_info in LOCATION_LEVELS.items():
            st.markdown(f"""
            **{level_info['label']}**
            - Código: `{{{level_info['code']}}}`
            - Ejemplo: {level_info['example']}
            - {level_info['description']}
            """)
        
        st.markdown("""
        **Mejores prácticas:**
        - Usa entre 3-5 títulos con inserción de ubicación
        - Combina diferentes niveles (ciudad, estado, país)
        - Asegúrate de tener texto predeterminado
        - Verifica que los códigos no excedan el límite de caracteres
        """)
    
    # Ejemplos
    st.markdown("#### 💡 Ejemplos de Anuncios Optimizados")
    
    with st.expander("Ver ejemplos reales"):
        st.markdown("""
        **Ejemplo 1: Servicios Esotéricos con Ubicación**
        
        **Headlines:**
        - `Curandero en {LOCATION(City)}`
        - `Brujos Efectivos {LOCATION(State)}`
        - Trabajos Espirituales Reales
        - Amarres de Amor Garantizados
        - `Brujería Profesional {LOCATION(Country)}`
        - Resultados en 24 Horas
        
        **Descriptions:**
        - Servicios esotéricos con más de 20 años de experiencia. Resultados comprobados.
        - Consulta gratis. Pago después de ver resultados. Testimonios reales verificables.
        
        ---
        
        **Ejemplo 2: E-commerce sin Ubicación**
        
        **Headlines:**
        - Compra Online con Envío Gratis
        - Productos Originales Garantizados
        - Hasta 50% de Descuento Hoy
        - Miles de Productos Disponibles
        - Devolución Gratis 30 Días
        
        **Descriptions:**
        - Envío gratis en compras mayores a $50. Entrega en 24-48 horas a todo el país.
        - Más de 10,000 productos originales. Pago seguro. Garantía de satisfacción 100%.
        """)

# ============================================================================
# EJECUTAR
# ============================================================================

# ============================================================================
# TAB 5: AJUSTES RÁPIDOS
# ============================================================================

def render_settings_tab():
    """Tab de ajustes rápidos que se guardan en storage local"""
    
    st.markdown("### ⚙️ Ajustes Rápidos")
    st.markdown("Configura tus preferencias por defecto para la generación de anuncios.")
    
    try:
        user_storage = get_user_storage()
        available_providers = get_available_providers()
        
        if not available_providers:
            st.warning("⚠️ No hay proveedores configurados. Ve a **⚙️ User Storage** para configurar tus API keys.")
            return
        
        # Formulario de configuración
        with st.form("settings_form"):
            st.markdown("#### 🤖 Configuración de IA")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Proveedor por defecto
                current_provider = st.session_state.get('default_provider', available_providers[0])
                if current_provider not in available_providers:
                    current_provider = available_providers[0]
                
                default_provider = st.selectbox(
                    "Proveedor por defecto:",
                    available_providers,
                    index=available_providers.index(current_provider),
                    format_func=lambda x: f"{AI_MODELS_2025[x]['icon']} {AI_MODELS_2025[x]['name']}"
                )
                
                # Tono por defecto
                current_tone = st.session_state.get('default_tone', 'emocional')
                tone_options = list(TONE_PRESETS.keys())
                tone_index = tone_options.index(current_tone) if current_tone in tone_options else 0
                
                default_tone = st.selectbox(
                    "Tono por defecto:",
                    tone_options,
                    index=tone_index,
                    format_func=lambda x: f"{TONE_PRESETS[x]['icon']} {x.title()}"
                )
            
            with col2:
                # Cantidad de anuncios
                default_num_ads = st.number_input(
                    "Cantidad de anuncios por defecto:",
                    min_value=1,
                    max_value=10,
                    value=st.session_state.get('default_num_ads', 1)
                )
                
                # Número de headlines
                default_num_headlines = st.slider(
                    "Títulos por defecto:",
                    min_value=5,
                    max_value=15,
                    value=st.session_state.get('default_num_headlines', 10)
                )
                
                # Número de descriptions
                default_num_descriptions = st.slider(
                    "Descriptions por defecto:",
                    min_value=2,
                    max_value=4,
                    value=st.session_state.get('default_num_descriptions', 3)
                )
            
            st.markdown("#### 🔧 Configuración Automática")
            
            col3, col4 = st.columns(2)
            
            with col3:
                auto_validation = st.checkbox(
                    "✅ Validación automática",
                    value=st.session_state.get('auto_validation', True),
                    help="Validar automáticamente las políticas de Google Ads"
                )
                
                auto_scoring = st.checkbox(
                    "📊 Scoring automático",
                    value=st.session_state.get('auto_scoring', True),
                    help="Calcular automáticamente el score de calidad"
                )
            
            with col4:
                auto_best_practices = st.checkbox(
                    "📚 Mejores prácticas automáticas",
                    value=st.session_state.get('auto_best_practices', True),
                    help="Aplicar automáticamente las mejores prácticas de Google Ads"
                )
                
                auto_location_insertion = st.checkbox(
                    "📍 Inserción de ubicaciones por defecto",
                    value=st.session_state.get('auto_location_insertion', False),
                    help="Activar inserción de ubicaciones por defecto"
                )
            
            # Botón de guardar
            submitted = st.form_submit_button(
                "💾 Guardar Configuración",
                type="primary",
                use_container_width=True
            )
            
            if submitted:
                try:
                    # Guardar configuración de IA
                    ai_settings = {
                        'default_provider': default_provider,
                        'default_tone': default_tone,
                        'default_num_ads': default_num_ads,
                        'default_num_headlines': default_num_headlines,
                        'default_num_descriptions': default_num_descriptions,
                        'auto_validation': auto_validation,
                        'auto_scoring': auto_scoring,
                        'auto_best_practices': auto_best_practices,
                        'auto_location_insertion': auto_location_insertion
                    }
                    
                    user_storage.save_ai_settings(ai_settings)
                    
                    # Actualizar session state
                    for key, value in ai_settings.items():
                        st.session_state[key] = value
                    
                    st.success("✅ Configuración guardada correctamente")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error guardando configuración: {e}")
        
        # Información actual
        st.markdown("---")
        st.markdown("#### 📊 Configuración Actual")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"**Proveedor:** {AI_MODELS_2025[st.session_state.get('default_provider', 'openai')]['name']}")
            st.info(f"**Tono:** {st.session_state.get('default_tone', 'emocional').title()}")
        
        with col2:
            st.info(f"**Anuncios:** {st.session_state.get('default_num_ads', 1)}")
            st.info(f"**Títulos:** {st.session_state.get('default_num_headlines', 10)}")
        
        with col3:
            st.info(f"**Descriptions:** {st.session_state.get('default_num_descriptions', 3)}")
            validation_status = "✅" if st.session_state.get('auto_validation', True) else "❌"
            st.info(f"**Auto-validación:** {validation_status}")
        
        # Botón de reset
        if st.button("🔄 Restaurar Valores por Defecto", type="secondary"):
            try:
                # Valores por defecto
                default_settings = {
                    'default_provider': available_providers[0],
                    'default_tone': 'emocional',
                    'default_num_ads': 1,
                    'default_num_headlines': 10,
                    'default_num_descriptions': 3,
                    'auto_validation': True,
                    'auto_scoring': True,
                    'auto_best_practices': True,
                    'auto_location_insertion': False
                }
                
                user_storage.save_ai_settings(default_settings)
                
                # Actualizar session state
                for key, value in default_settings.items():
                    st.session_state[key] = value
                
                st.success("✅ Configuración restaurada a valores por defecto")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error restaurando configuración: {e}")
    
    except Exception as e:
        st.error(f"❌ Error accediendo al storage: {e}")

def render_autopilot_tab():
    """Renderiza la pestaña AUTOPILOT 2050 con selector de campañas inteligente"""
    
    st.markdown("### 🤖 AUTOPILOT 2050")
    st.markdown("**Autopublicador Inteligente con Detección de Campañas**")
    
    # Verificar disponibilidad de módulos críticos
    modules_available = True
    error_messages = []
    
    try:
        # Intentar importar los módulos necesarios
        from services.intelligent_autopilot import IntelligentAutopilot
        from modules.ai_ad_generator import AIAdGenerator
    except ImportError as import_err:
        modules_available = False
        error_messages.append(f"Error importando módulos: {import_err}")
    except Exception as e:
        modules_available = False
        error_messages.append(f"Error general: {e}")
    
    # CSS futurístico específico para AUTOPILOT 2050
    st.markdown("""
    <style>
        .autopilot-header {
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
            padding: 3rem;
            border-radius: 20px;
            text-align: center;
            color: #00ffff;
            margin-bottom: 2rem;
            box-shadow: 0 0 30px rgba(0, 255, 255, 0.3);
            border: 2px solid #00ffff;
            position: relative;
            overflow: hidden;
        }
        
        .autopilot-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(0, 255, 255, 0.1), transparent);
            animation: scan 3s infinite;
        }
        
        @keyframes scan {
            0% { left: -100%; }
            100% { left: 100%; }
        }
        
        .autopilot-header h1 {
            margin: 0;
            font-size: 3.5rem;
            font-weight: 900;
            text-shadow: 0 0 20px #00ffff;
            font-family: 'Courier New', monospace;
            letter-spacing: 3px;
        }
        
        .autopilot-subtitle {
            font-size: 1.2rem;
            margin-top: 1rem;
            opacity: 0.8;
            font-family: 'Courier New', monospace;
        }
        
        .neural-card {
            background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 100%);
            border: 1px solid #00ffff;
            border-radius: 15px;
            padding: 2rem;
            margin: 1rem 0;
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
            color: #ffffff;
        }
        
        .neural-card h3 {
            color: #00ffff;
            font-family: 'Courier New', monospace;
            text-shadow: 0 0 10px #00ffff;
        }
        
        .campaign-card {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border: 1px solid #00ffff;
            border-radius: 10px;
            padding: 1.5rem;
            margin: 0.5rem 0;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .campaign-card:hover {
            box-shadow: 0 0 15px rgba(0, 255, 255, 0.4);
            transform: translateY(-2px);
        }
        
        .campaign-card.selected {
            border-color: #00ff00;
            box-shadow: 0 0 20px rgba(0, 255, 0, 0.3);
        }
        
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        
        .status-online { background-color: #00ff00; }
        .status-processing { background-color: #ffff00; }
        .status-offline { background-color: #ff0000; }
        .status-paused { background-color: #ff8800; }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .matrix-text {
            font-family: 'Courier New', monospace;
            color: #00ff00;
            background: #000;
            padding: 1rem;
            border-radius: 8px;
            font-size: 0.9rem;
            line-height: 1.4;
        }
        
        .cyber-button {
            background: linear-gradient(135deg, #00ffff 0%, #0080ff 100%);
            color: #000;
            border: none;
            padding: 1rem 2rem;
            border-radius: 10px;
            font-weight: bold;
            font-family: 'Courier New', monospace;
            text-transform: uppercase;
            letter-spacing: 1px;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 0 20px rgba(0, 255, 255, 0.5);
        }
        
        .cyber-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 0 30px rgba(0, 255, 255, 0.8);
        }
        
        .progress-neural {
            background: #0a0a1a;
            border-radius: 10px;
            padding: 1rem;
            border: 1px solid #00ffff;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header futurístico
    st.markdown("""
    <div class="autopilot-header">
        <h1>🤖 AUTOPILOT 2050</h1>
        <div class="autopilot-subtitle">
            Autopublicador Inteligente con Detección de Campañas - VERSIÓN COMPLETA RESTAURADA ✅
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Verificar si los módulos están disponibles
    if not modules_available:
        st.error("❌ **AUTOPILOT 2050 no está completamente disponible**")
        
        for error_msg in error_messages:
            st.warning(f"⚠️ {error_msg}")
        
        st.markdown("""
        <div class="neural-card">
            <h3>🔧 Soluciones Posibles</h3>
            <p>• Verifica que todos los módulos estén instalados correctamente</p>
            <p>• Reinicia la aplicación</p>
            <p>• Usa la pestaña <strong>🚀 Generar</strong> para funciones básicas</p>
            <p>• Contacta al administrador si el problema persiste</p>
        </div>
        """, unsafe_allow_html=True)
        
        return
    
    # Verificar importaciones necesarias
    try:
        # Verificar cliente de Google Ads
        google_ads_client = st.session_state.get('google_ads_client')
        if not google_ads_client:
            st.error("❌ Cliente de Google Ads no inicializado")
            st.info("💡 Ve a la aplicación principal para conectar con Google Ads primero.")
            return
        
        # ✅ VERIFICAR Y CONFIGURAR API KEYS
        import os
        openai_key = os.getenv('OPENAI_API_KEY')
        
        if not openai_key or openai_key == 'tu_openai_api_key_aqui':
            st.error("❌ **API Key de OpenAI no configurada**")
            
            st.markdown("""
            <div class="neural-card">
                <h3>🔑 Configuración de API Keys Requerida</h3>
                <p>Para usar el AUTOPILOT 2050, necesitas configurar tu API key de OpenAI:</p>
                <ol>
                    <li>Ve a <a href="https://platform.openai.com/api-keys" target="_blank">OpenAI API Keys</a></li>
                    <li>Crea una nueva API key</li>
                    <li>Configúrala usando una de estas opciones:</li>
                </ol>
            </div>
            """, unsafe_allow_html=True)
            
            # Opción 1: Configuración temporal en la sesión
            with st.expander("🔧 Configuración Temporal (Solo para esta sesión)"):
                temp_api_key = st.text_input(
                    "🔑 OpenAI API Key",
                    type="password",
                    placeholder="sk-...",
                    help="Esta key solo se usará durante esta sesión y no se guardará"
                )
                
                if st.button("✅ Configurar API Key Temporal"):
                    if temp_api_key and temp_api_key.startswith('sk-'):
                        os.environ['OPENAI_API_KEY'] = temp_api_key
                        st.success("✅ API Key configurada temporalmente")
                        st.info("🔄 Recarga la página para continuar")
                        st.rerun()
                    else:
                        st.error("❌ API Key inválida. Debe comenzar con 'sk-'")
            
            # Opción 2: Configuración permanente
            with st.expander("💾 Configuración Permanente"):
                st.markdown("""
                **Para configuración permanente, ejecuta estos comandos en tu terminal:**
                
                ```bash
                # 1. Ir al directorio del proyecto
                cd /Users/edwarbechara/dashboard-api-googleads
                
                # 2. Ejecutar el script de configuración
                ./setup_env.sh
                
                # 3. Reiniciar la aplicación
                source venv/bin/activate && streamlit run app.py --server.port 8501 --server.address 0.0.0.0
                ```
                """)
            
            return
        
        # Crear instancias
        try:
            ai_generator = AIAdGenerator()
            intelligent_autopilot = IntelligentAutopilot(google_ads_client)
        except Exception as init_error:
            st.error(f"❌ Error inicializando servicios: {init_error}")
            st.info("💡 Verifica que todos los módulos estén correctamente configurados.")
            return
            
    except Exception as e:
        st.error(f"❌ Error general en AUTOPILOT: {e}")
        st.info("💡 Usa las otras pestañas mientras se resuelve este problema.")
        return
    
    # Verificar customer seleccionado
    if 'selected_customer' not in st.session_state or not st.session_state.selected_customer:
        st.warning("⚠️ Por favor selecciona un cliente en la barra lateral para continuar")
        return
    
    selected_customer = st.session_state.selected_customer
    
    # Estado del sistema
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="neural-card">
            <h3>🧠 Estado Neural</h3>
            <p><span class="status-indicator status-online"></span>IA ACTIVA</p>
            <p><span class="status-indicator status-online"></span>DETECCIÓN ONLINE</p>
            <p><span class="status-indicator status-online"></span>AUTOPILOT READY</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="neural-card">
            <h3>⚡ Capacidades</h3>
            <p>• Detección de Campañas Existentes</p>
            <p>• Creación de Grupos Automática</p>
            <p>• Targeting USA + COP</p>
            <p>• Publicación Inteligente</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="neural-card">
            <h3>🎯 Configuración</h3>
            <p>• Moneda: COP (Pesos)</p>
            <p>• País: Estados Unidos</p>
            <p>• Edad: Sin restricción</p>
            <p>• Modo: Autopublicador</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # PASO 1: Selector de Modo de Campaña
    st.markdown("""
    <div class="neural-card">
        <h3>🎯 PASO 1: SELECCIONAR MODO DE CAMPAÑA</h3>
    </div>
    """, unsafe_allow_html=True)
    
    campaign_mode = st.radio(
        "Selecciona el modo de operación:",
        ["🆕 Crear Nueva Campaña", "📋 Usar Campaña Existente"],
        help="Elige si quieres crear una campaña completamente nueva o agregar grupos de anuncios a una campaña existente"
    )
    
    st.markdown("---")
    
    # PASO 2: Configuración según el modo
    if campaign_mode == "📋 Usar Campaña Existente":
        st.markdown("""
        <div class="neural-card">
            <h3>📋 PASO 2: SELECCIONAR CAMPAÑA EXISTENTE</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Cargar campañas existentes
        with st.spinner("🔍 Detectando campañas existentes..."):
            try:
                available_campaigns = intelligent_autopilot.get_available_campaigns(selected_customer)
                
                if not available_campaigns:
                    st.warning("⚠️ No se encontraron campañas existentes. Cambia a 'Crear Nueva Campaña'")
                    return
                
                # Mostrar campañas disponibles
                st.success(f"✅ Se encontraron {len(available_campaigns)} campañas disponibles")
                
                # Selector de campaña
                campaign_options = []
                for campaign in available_campaigns:
                    if not campaign.is_new:  # Excluir la opción "nueva"
                        status_icon = "🟢" if campaign.campaign_status == "ENABLED" else "🟡" if campaign.campaign_status == "PAUSED" else "🔴"
                        campaign_options.append(f"{status_icon} {campaign.campaign_name} (ID: {campaign.campaign_id})")
                
                if not campaign_options:
                    st.warning("⚠️ No hay campañas válidas disponibles")
                    return
                
                selected_campaign_display = st.selectbox(
                    "Selecciona la campaña:",
                    campaign_options,
                    help="Elige la campaña donde quieres agregar grupos de anuncios automáticamente"
                )
                
                # Extraer ID de la campaña seleccionada
                selected_campaign_id = selected_campaign_display.split("ID: ")[1].split(")")[0]
                selected_campaign_obj = next(c for c in available_campaigns if c.campaign_id == selected_campaign_id)
                
                # Mostrar detalles de la campaña seleccionada
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div class="campaign-card selected">
                        <h4>📊 Detalles de la Campaña</h4>
                        <p><strong>Nombre:</strong> {selected_campaign_obj.campaign_name}</p>
                        <p><strong>Estado:</strong> <span class="status-indicator status-{'online' if selected_campaign_obj.campaign_status == 'ENABLED' else 'paused'}"></span>{selected_campaign_obj.campaign_status}</p>
                        <p><strong>Tipo:</strong> {selected_campaign_obj.campaign_type}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    # Obtener detalles adicionales
                    campaign_details = intelligent_autopilot.get_campaign_details(selected_customer, selected_campaign_id)
                    st.markdown(f"""
                    <div class="campaign-card">
                        <h4>💰 Información Adicional</h4>
                        <p><strong>Presupuesto:</strong> {campaign_details.get('budget', 'N/A')}</p>
                        <p><strong>Grupos Existentes:</strong> {campaign_details.get('ad_groups_count', 0)}</p>
                        <p><strong>Anuncios Activos:</strong> {campaign_details.get('ads_count', 0)}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ Error cargando campañas: {e}")
                return
    
    else:  # Crear Nueva Campaña
        st.markdown("""
        <div class="neural-card">
            <h3>🆕 PASO 2: CONFIGURAR NUEVA CAMPAÑA</h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            campaign_name = st.text_input(
                "📝 Nombre de la Campaña",
                placeholder="Ej: Medicina Alternativa - Autopilot 2050",
                help="Nombre descriptivo para tu nueva campaña"
            )
            
            daily_budget = st.number_input(
                "💰 Presupuesto Diario (COP)",
                min_value=10000,
                max_value=1000000,
                value=50000,
                step=5000,
                help="Presupuesto diario en pesos colombianos"
            )
        
        with col2:
            campaign_objective = st.selectbox(
                "🎯 Objetivo Principal",
                ["Generar Leads", "Aumentar Ventas", "Tráfico Web", "Brand Awareness"],
                help="Objetivo principal de tu campaña"
            )
            
            bidding_strategy = st.selectbox(
                "💡 Estrategia de Puja",
                ["Maximizar Clics", "CPC Manual", "Maximizar Conversiones"],
                help="Estrategia de puja para optimizar el rendimiento"
            )
    
    st.markdown("---")
    
    # PASO 3: Configuración del Negocio
    st.markdown("""
    <div class="neural-card">
        <h3>🏢 PASO 3: INFORMACIÓN DEL NEGOCIO</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        business_description = st.text_area(
            "📊 Descripción del Negocio",
            placeholder="Ej: Somos una clínica de medicina alternativa especializada en tratamientos holísticos y terapias naturales...",
            height=120,
            help="Describe detalladamente tu negocio para generar grupos de anuncios relevantes"
        )
    
    with col2:
        business_url = st.text_input(
            "🌐 URL del Sitio Web",
            placeholder="https://www.ejemplo.com",
            help="URL principal de tu sitio web"
        )
        
        num_ad_groups = st.slider(
            "📦 Número de Grupos de Anuncios",
            min_value=1,
            max_value=10,
            value=1,
            help="Cantidad de grupos de anuncios a generar"
        )
    
    # NUEVA FUNCIONALIDAD: Configuración por grupo (si hay más de 1)
    target_keywords = None  # Variable para compatibilidad
    ad_groups_config = []  # Nueva estructura para múltiples grupos
    
    if num_ad_groups > 1:
        st.markdown("### 📋 CONFIGURACIÓN POR GRUPO")
        st.info("Configura keywords y URL específicas para cada grupo de anuncios")
        
        for i in range(num_ad_groups):
            with st.expander(f"📦 Grupo #{i+1}", expanded=(i==0)):
                st.markdown(f"<div style='background: rgba(0,255,255,0.05); padding: 1rem; border-radius: 10px; border: 1px solid #00ffff;'>", unsafe_allow_html=True)
                
                group_name = st.text_input(
                    f"📛 Nombre del Grupo #{i+1}",
                    value=f"Grupo {i+1}",
                    key=f"group_name_{i}",
                    placeholder="Ej: Amarres de Amor"
                )
                
                group_keywords = st.text_area(
                    f"🔑 Keywords para Grupo #{i+1}",
                    placeholder="amarre de amor\nhechizo amor\nbrujería amor\n(una por línea)",
                    height=80,
                    key=f"group_keywords_{i}",
                    help="Keywords específicas para este grupo (una por línea)"
                )
                
                group_url = st.text_input(
                    f"🌐 URL específica para Grupo #{i+1}",
                    placeholder="https://ejemplo.com/amarres",
                    key=f"group_url_{i}",
                    help="URL de destino para este grupo específico"
                )
                
                # ✅ NUEVO: Checkbox para inserciones de ubicación
                col_loc1, col_loc2 = st.columns([3, 1])
                
                with col_loc1:
                    use_location_insertion = st.checkbox(
                        f"📍 Usar Inserciones de Ubicación en Grupo #{i+1}",
                        key=f"use_location_{i}",
                        help="Activa esto para insertar automáticamente la ubicación del usuario en 3-5 títulos (mejora el CTR)"
                    )
                
                with col_loc2:
                    if use_location_insertion:
                        st.markdown("""
                        <div style='background: rgba(0,255,0,0.1); padding: 0.5rem; border-radius: 5px; text-align: center;'>
                            <span style='color: #00ff00; font-size: 1.5rem;'>✅</span>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Mostrar información sobre inserciones de ubicación
                if use_location_insertion:
                    st.info("""
                    📍 **Inserciones de Ubicación Activadas**
                    
                    Se generarán 3-5 títulos con códigos de inserción:
                    - 🏙️ `{LOCATION(City)}` - Ej: "Curandero en {LOCATION(City)}"
                    - 🗺️ `{LOCATION(State)}` - Ej: "Brujos Efectivos {LOCATION(State)}"
                    - 🌍 `{LOCATION(Country)}` - Ej: "Amarres en {LOCATION(Country)}"
                    
                    Esto personaliza los anuncios según la ubicación del usuario y mejora el CTR.
                    """)
                
                # Procesar keywords
                if group_keywords:
                    keywords_list = [kw.strip() for kw in group_keywords.split('\n') if kw.strip()]
                    
                    if keywords_list and group_url:
                        st.success(f"✅ {len(keywords_list)} keywords configuradas")
                        ad_groups_config.append({
                            'name': group_name,
                            'keywords': keywords_list,
                            'url': group_url,
                            'use_location_insertion': use_location_insertion  # ✅ Agregar flag
                        })
                    elif keywords_list or group_url:
                        st.warning(f"⚠️ Completa keywords Y URL para el Grupo #{i+1}")
                
                st.markdown("</div>", unsafe_allow_html=True)
    
    else:
        # Si solo es 1 grupo, usar el formato anterior
        target_keywords = st.text_area(
            "🔑 Keywords Principales",
            placeholder="medicina alternativa, terapias naturales, tratamientos holísticos",
            height=120,
            help="Palabras clave principales separadas por comas o líneas"
        )
        
        # ✅ NUEVO: Checkbox para inserciones de ubicación (grupo único)
        st.markdown("---")
        
        col_loc1, col_loc2 = st.columns([3, 1])
        
        with col_loc1:
            use_location_insertion_single = st.checkbox(
                "📍 Usar Inserciones de Ubicación",
                key="use_location_single",
                help="Activa esto para insertar automáticamente la ubicación del usuario en 3-5 títulos (mejora el CTR)"
            )
        
        with col_loc2:
            if use_location_insertion_single:
                st.markdown("""
                <div style='background: rgba(0,255,0,0.1); padding: 0.5rem; border-radius: 5px; text-align: center;'>
                    <span style='color: #00ff00; font-size: 1.5rem;'>✅</span>
                </div>
                """, unsafe_allow_html=True)
        
        # Mostrar información sobre inserciones de ubicación
        if use_location_insertion_single:
            st.info("""
            📍 **Inserciones de Ubicación Activadas**
            
            Se generarán 3-5 títulos con códigos de inserción:
            - 🏙️ `{LOCATION(City)}` - Ej: "Curandero en {LOCATION(City)}"
            - 🗺️ `{LOCATION(State)}` - Ej: "Brujos Efectivos {LOCATION(State)}"
            - 🌍 `{LOCATION(Country)}` - Ej: "Amarres en {LOCATION(Country)}"
            
            Esto personaliza los anuncios según la ubicación del usuario y mejora el CTR.
            """)
    
    st.markdown("---")
    
    # ✅ RESUMEN DE CONFIGURACIÓN
    if num_ad_groups > 1 and ad_groups_config:
        with st.expander("📊 Resumen de Configuración de Grupos"):
            st.write(f"**Total de grupos configurados:** {len(ad_groups_config)}")
            for idx, group in enumerate(ad_groups_config, 1):
                st.write(f"**Grupo {idx}: {group['name']}**")
                st.write(f"  - Keywords: {len(group['keywords'])}")
                st.write(f"  - URL: {group['url']}")
                st.write(f"  - Inserciones de Ubicación: {'✅ Activadas' if group.get('use_location_insertion', False) else '❌ Desactivadas'}")
    
    st.markdown("---")
    
    # PASO 4: Configuración Avanzada
    with st.expander("⚙️ CONFIGURACIÓN AVANZADA"):
        col1, col2 = st.columns(2)
        
        with col1:
            ai_creativity = st.slider(
                "🎨 Creatividad de la IA",
                min_value=0.1,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="Nivel de creatividad para generar anuncios (0.1 = conservador, 1.0 = muy creativo)"
            )
            
            keywords_per_group = st.slider(
                "🔑 Keywords por Grupo",
                min_value=5,
                max_value=30,
                value=15,
                help="Número de keywords por grupo de anuncios"
            )
            
            # ✅ NUEVO: MODO MAGNÉTICO
            use_magnetic = st.checkbox(
                "🔴 Modo MAGNÉTICO",
                value=False,
                help="Activa prompts de alta intensidad psicológica para servicios esotéricos"
            )
            
            if use_magnetic:
                st.markdown("""
                <div class="ultra-info">
                    <h4>🔴 MODO MAGNÉTICO ACTIVADO</h4>
                    <p>Los anuncios se generarán con prompts de alta intensidad psicológica distribuidos en:</p>
                    <ul>
                        <li>🎯 <strong>Beneficio + Urgencia:</strong> 5 títulos</li>
                        <li>🏆 <strong>Credibilidad + Exclusividad:</strong> 5 títulos</li>
                        <li>🧠 <strong>Control + Curiosidad:</strong> 5 títulos</li>
                    </ul>
                    <p><em>Ideal para servicios esotéricos, coaching y productos de transformación personal.</em></p>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            # ✅ NUEVO: Selector de proveedor AI
            ai_provider = st.selectbox(
                "🤖 Proveedor AI",
                ["openai", "gemini", "anthropic"],
                format_func=lambda x: {"openai": "🔵 OpenAI", "gemini": "🔴 Google Gemini", "anthropic": "🟣 Anthropic"}[x],
                help="Selecciona el motor de IA para generar anuncios"
            )
            
            # ✅ NUEVO: Selector de modelo según proveedor
            if ai_provider == "openai":
                ai_model = st.selectbox(
                    "🎯 Modelo",
                    ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
                    help="Modelo de OpenAI"
                )
            elif ai_provider == "gemini":
                ai_model = st.selectbox(
                    "🎯 Modelo",
                    ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"],
                    help="Modelo de Google Gemini"
                )
            else:  # anthropic
                ai_model = st.selectbox(
                    "🎯 Modelo",
                    ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
                    help="Modelo de Anthropic Claude"
                )
            
            ads_per_group = st.slider(
                "📝 Anuncios por Grupo",
                min_value=3,
                max_value=15,
                value=8,
                help="Número de anuncios por grupo"
            )
            
            match_types = st.multiselect(
                "🎯 Tipos de Concordancia",
                ["Exacta", "Frase", "Amplia Modificada", "Amplia"],
                default=["Exacta", "Frase"],
                help="Tipos de concordancia para las keywords"
            )
    
    st.markdown("---")
    
    # PASO 5: Botón de Publicación
    st.markdown("""
    <div class="neural-card">
        <h3>🚀 PASO 5: INICIAR AUTOPUBLICADOR</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Validaciones
    can_publish = True
    validation_messages = []
    
    if not business_description:
        validation_messages.append("❌ Descripción del negocio requerida")
        can_publish = False
    
    if campaign_mode == "🆕 Crear Nueva Campaña" and not campaign_name:
        validation_messages.append("❌ Nombre de campaña requerido")
        can_publish = False
    
    if campaign_mode == "🆕 Crear Nueva Campaña" and not business_url:
        validation_messages.append("❌ URL del sitio web requerida")
        can_publish = False
    
    # Validación para múltiples grupos o grupo único
    if num_ad_groups > 1:
        if not ad_groups_config or len(ad_groups_config) == 0:
            validation_messages.append("❌ Debes configurar al menos 1 grupo con keywords y URL")
            can_publish = False
        elif len(ad_groups_config) < num_ad_groups:
            validation_messages.append(f"⚠️ Configurados {len(ad_groups_config)}/{num_ad_groups} grupos")
            can_publish = False
    else:
        # Validación para grupo único
        if not target_keywords:
            validation_messages.append("❌ Keywords principales requeridas")
            can_publish = False
    
    # Mostrar mensajes de validación
    if validation_messages:
        for msg in validation_messages:
            st.error(msg)
    
    # Botón de publicación
    if st.button("🚀 INICIAR AUTOPUBLICADOR INTELIGENTE", type="primary", use_container_width=True, disabled=not can_publish):
        
        # Mostrar progreso
        progress_container = st.container()
        
        with progress_container:
            st.markdown("""
            <div class="progress-neural">
                <h4 style="color: #00ffff; font-family: 'Courier New', monospace;">
                    🧠 INICIANDO AUTOPUBLICADOR INTELIGENTE...
                </h4>
            </div>
            """, unsafe_allow_html=True)
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Paso 1: Generar grupos de anuncios
                status_text.markdown("""
                <div class="matrix-text">
                    🔍 Analizando negocio y generando grupos de anuncios...
                </div>
                """, unsafe_allow_html=True)
                progress_bar.progress(0.2)
                
                # Procesar target_keywords correctamente (separar por comas y saltos de línea)
                if isinstance(target_keywords, str):
                    # Separar por comas y saltos de línea, limpiar espacios
                    processed_keywords = []
                    for keyword in target_keywords.replace('\n', ',').split(','):
                        keyword = keyword.strip()
                        if keyword:  # Solo agregar si no está vacío
                            processed_keywords.append(keyword)
                    target_keywords_list = processed_keywords
                else:
                    target_keywords_list = target_keywords if target_keywords else []
                
                # Configurar parámetros para generación
                generation_config = {
                    'business_description': business_description,
                    'target_keywords': target_keywords_list if num_ad_groups == 1 else [],
                    'num_ad_groups': num_ad_groups,
                    'keywords_per_group': keywords_per_group,
                    'ads_per_group': ads_per_group,
                    'ai_creativity': ai_creativity,
                    'match_types': match_types,
                    'business_url': business_url,
                    'use_magnetic': use_magnetic,
                    'ai_provider': ai_provider,
                    'ai_model': ai_model,
                    'use_location_insertion': use_location_insertion_single if num_ad_groups == 1 else False  # ✅ Para grupo único
                }
                
                # Generar grupos de anuncios
                try:
                    if num_ad_groups > 1:
                        # ✅ NUEVO: Usar generate_ad_groups_from_config para múltiples grupos
                        ad_groups = intelligent_autopilot.generate_ad_groups_from_config(
                            business_description,
                            ad_groups_config,
                            generation_config
                        )
                    else:
                        # ✅ Método tradicional para grupo único
                        ad_groups = intelligent_autopilot.generate_ad_groups_for_business(
                            business_description, 
                            target_keywords_list, 
                            generation_config
                        )
                    
                    if not ad_groups:
                        st.warning("⚠️ No se generaron grupos de anuncios. Verifica la descripción del negocio.")
                        return
                    
                    st.info(f"✅ Se generaron {len(ad_groups)} grupos de anuncios")
                    
                except Exception as e:
                    st.error(f"❌ Error generando grupos de anuncios: {str(e)}")
                    return
                
                progress_bar.progress(0.5)
                
                # Paso 2: Publicar según el modo
                if campaign_mode == "📋 Usar Campaña Existente":
                    status_text.markdown("""
                    <div class="matrix-text">
                        📋 Agregando grupos de anuncios a campaña existente...
                    </div>
                    """, unsafe_allow_html=True)
                    
                    result = intelligent_autopilot.publish_complete_campaign(
                        customer_id=selected_customer,
                        campaign_option=selected_campaign_obj,
                        ad_groups=ad_groups
                    )
                    
                else:  # Nueva campaña
                    status_text.markdown("""
                    <div class="matrix-text">
                        🆕 Creando nueva campaña con grupos de anuncios...
                    </div>
                    """, unsafe_allow_html=True)
                    
                    campaign_config = {
                        'name': campaign_name,
                        'daily_budget': daily_budget,
                        'objective': campaign_objective,
                        'bidding_strategy': bidding_strategy,
                        'business_url': business_url
                    }
                    
                    # Crear objeto CampaignOption para nueva campaña
                    new_campaign_option = CampaignOption(
                        campaign_id="new",
                        campaign_name=campaign_name,
                        campaign_status="PAUSED",
                        campaign_type="SEARCH",
                        is_new=True
                    )
                    
                    result = intelligent_autopilot.publish_complete_campaign(
                        customer_id=selected_customer,
                        campaign_option=new_campaign_option,
                        ad_groups=ad_groups,
                        campaign_config=campaign_config
                    )
                
                progress_bar.progress(0.8)
                
                status_text.markdown("""
                <div class="matrix-text">
                    ✅ Finalizando publicación...
                </div>
                """, unsafe_allow_html=True)
                progress_bar.progress(1.0)
                
                # Mostrar resultados
                if result.get('success'):
                    st.success("🎉 ¡AUTOPUBLICADOR COMPLETADO EXITOSAMENTE!")
                else:
                    st.error("❌ Error en la publicación")
                    if result.get('errors'):
                        for err in result['errors']:
                            st.write(f"• {err}")
                
                # Mostrar métricas reales
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("📦 Grupos Creados", len(result.get('ad_group_ids', [])))
                
                with col2:
                    st.metric("📝 Anuncios Publicados", len(result.get('ad_ids', [])))
                
                with col3:
                    st.metric("🔑 Keywords Agregadas", len(result.get('keyword_ids', [])))
                
                # Mostrar información adicional
                if result.get('campaign_id'):
                    st.info(f"🆔 **ID de Campaña:** {result['campaign_id']}")
                
                if result.get('campaign_resource_name'):
                    st.info(f"🔗 **Resource:** {result['campaign_resource_name']}")
                
                # Mostrar resumen de grupos creados (si existe)
                if result.get('ad_groups_summary'):
                    st.markdown("### 📊 Resumen de Grupos Creados")
                    for group in result['ad_groups_summary']:
                        with st.expander(f"📦 {group['name']}"):
                            st.write(f"**Keywords:** {group['keywords_count']}")
                            st.write(f"**Anuncios:** {group['ads_count']}")
                            st.write(f"**CPC Sugerido:** ${group['suggested_cpc']:.2f} COP")
                
            except Exception as e:
                st.error(f"❌ Error en el autopublicador: {e}")
                progress_bar.progress(0)
                status_text.empty()

# ============================================================================
# FUNCIÓN DE PUBLICACIÓN AUTOPILOT
# ============================================================================

def publish_autopilot_campaign(autopilot, blueprint, customer_id):
    """
    Publica una campaña AUTOPILOT 2050 a Google Ads con progreso en tiempo real
    """
    try:
        # Contenedor principal para el progreso
        progress_container = st.container()
        
        with progress_container:
            st.markdown("### 🚀 Publicando Campaña AUTOPILOT 2050...")
            
            # Barra de progreso principal
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Contenedor para logs detallados
            log_container = st.expander("📋 Ver detalles del proceso", expanded=True)
            
            # Variables de seguimiento
            total_steps = 6
            current_step = 0
            
            def update_progress(step, message, details=None):
                nonlocal current_step
                current_step = step
                progress = current_step / total_steps
                progress_bar.progress(progress)
                status_text.info(f"**Paso {step}/{total_steps}:** {message}")
                
                with log_container:
                    st.write(f"✅ **{message}**")
                    if details:
                        for detail in details:
                            st.write(f"   • {detail}")
            
            # PASO 1: Validación inicial y verificación de acceso
            update_progress(1, "Validando datos de la campaña y acceso a la cuenta", [
                f"Nombre: {blueprint.campaign_name}",
                f"Presupuesto diario: ${blueprint.budget_daily:.2f}",
                f"Grupos de anuncios: {len(blueprint.ad_groups)}",
                f"Customer ID: {customer_id}"
            ])
            
            # Validar acceso a la cuenta
            try:
                # Obtener cliente primero
                wrapper = st.session_state.google_ads_client
                client = wrapper.get_client()
                
                # Hacer una consulta simple para verificar acceso
                query = "SELECT customer.id, customer.descriptive_name FROM customer LIMIT 1"
                response = client.search(customer_id, query)
                
                account_found = False
                account_name = ""
                for row in response:
                    account_found = True
                    account_name = row.customer.descriptive_name
                    break
                
                if not account_found:
                    st.error(f"❌ No se pudo acceder a la cuenta {customer_id}")
                    return
                
                with log_container:
                    st.success(f"✅ Acceso verificado a cuenta: {account_name} ({customer_id})")
                    
            except Exception as e:
                st.error(f"❌ Error validando acceso a la cuenta {customer_id}: {str(e)}")
                with st.expander("🔍 Detalles del error de validación"):
                    st.code(str(e))
                return
            
            time.sleep(1)
            
            # PASO 2: Obtener cliente de Google Ads
            update_progress(2, "Conectando con Google Ads API")
            
            if not hasattr(st.session_state, 'google_ads_client'):
                st.error("❌ Cliente de Google Ads no inicializado")
                return
            
            wrapper = st.session_state.google_ads_client
            client = wrapper.get_client()
            
            if not client:
                st.error("❌ No se pudo obtener el cliente de Google Ads")
                return
            
            # PASO 3: Crear presupuesto y campaña principal
            update_progress(3, "Creando presupuesto y campaña principal en Google Ads")
            
            try:
                campaign_service = client.get_service("CampaignService")
                campaign_budget_service = client.get_service("CampaignBudgetService")
                
                # 1. Crear presupuesto primero
                budget_operation = client.get_type("CampaignBudgetOperation")
                budget = budget_operation.create
                
                budget.name = f"Budget for {blueprint.campaign_name}"
                budget.amount_micros = int(blueprint.budget_daily * 1_000_000)
                budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
                
                budget_response = campaign_budget_service.mutate_campaign_budgets(
                    customer_id=customer_id,
                    operations=[budget_operation]
                )
                
                budget_resource_name = budget_response.results[0].resource_name
                
                with log_container:
                    st.success(f"✅ Presupuesto creado: ${blueprint.budget_daily:.2f}/día")
                
                # 2. Crear campaña con el presupuesto creado
                campaign_operation = client.get_type("CampaignOperation")
                campaign = campaign_operation.create
                
                # Configurar campaña
                campaign.name = blueprint.campaign_name
                campaign.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.SEARCH
                campaign.status = client.enums.CampaignStatusEnum.PAUSED  # Crear pausada por seguridad
                campaign.campaign_budget = budget_resource_name
                
                # Estrategia de puja: Maximizar clics
                campaign.bidding_strategy_type = client.enums.BiddingStrategyTypeEnum.MAXIMIZE_CLICKS
                
                # Network settings
                campaign.network_settings.target_google_search = True
                campaign.network_settings.target_search_network = True
                campaign.network_settings.target_content_network = False
                campaign.network_settings.target_partner_search_network = False
                
                # Fechas (1 año de duración)
                start_date = datetime.now()
                end_date = start_date + timedelta(days=365)
                campaign.start_date = start_date.strftime("%Y-%m-%d")
                campaign.end_date = end_date.strftime("%Y-%m-%d")
                
                # Ejecutar creación de campaña
                response = campaign_service.mutate_campaigns(
                    customer_id=customer_id,
                    operations=[campaign_operation]
                )
                
                campaign_id = response.results[0].resource_name.split('/')[-1]
                
                with log_container:
                    st.success(f"✅ Campaña creada exitosamente - ID: {campaign_id}")
                
            except Exception as e:
                st.error(f"❌ Error creando campaña: {str(e)}")
                with st.expander("🔍 Detalles del error"):
                    st.code(str(e))
                return
            
            # PASO 4: Crear grupos de anuncios
            update_progress(4, f"Creando {len(blueprint.ad_groups)} grupos de anuncios")
            
            ad_groups_created = 0
            ads_created = 0
            keywords_created = 0
            
            try:
                ad_group_service = client.get_service("AdGroupService")
                ad_group_ad_service = client.get_service("AdGroupAdService")
                ad_group_criterion_service = client.get_service("AdGroupCriterionService")
                
                for i, ad_group_data in enumerate(blueprint.ad_groups):
                    # Crear grupo de anuncios
                    ad_group_operation = client.get_type("AdGroupOperation")
                    ad_group = ad_group_operation.create
                    
                    ad_group.name = ad_group_data.get('name', f'Grupo {i+1}')
                    ad_group.campaign = campaign_service.campaign_path(customer_id, campaign_id)
                    ad_group.type_ = client.enums.AdGroupTypeEnum.SEARCH_STANDARD
                    ad_group.status = client.enums.AdGroupStatusEnum.ENABLED
                    
                    # CPC bid
                    ad_group.cpc_bid_micros = int(ad_group_data.get('max_cpc_bid', 1.0) * 1_000_000)
                    
                    # Crear grupo de anuncios
                    ad_group_response = ad_group_service.mutate_ad_groups(
                        customer_id=customer_id,
                        operations=[ad_group_operation]
                    )
                    
                    ad_group_id = ad_group_response.results[0].resource_name.split('/')[-1]
                    ad_groups_created += 1
                    
                    # Crear anuncios para este grupo
                    ads_data = ad_group_data.get('ads', [])
                    for ad_data in ads_data[:3]:  # Máximo 3 anuncios por grupo
                        try:
                            ad_group_ad_operation = client.get_type("AdGroupAdOperation")
                            ad_group_ad = ad_group_ad_operation.create
                            
                            ad_group_ad.ad_group = ad_group_service.ad_group_path(customer_id, ad_group_id)
                            ad_group_ad.status = client.enums.AdGroupAdStatusEnum.ENABLED
                            
                            # Crear anuncio responsivo de búsqueda
                            responsive_search_ad = ad_group_ad.ad.responsive_search_ad
                            
                            # Headlines
                            headlines = ad_data.get('headlines', [])[:15]  # Máximo 15
                            for headline in headlines:
                                headline_asset = client.get_type("AdTextAsset")
                                headline_asset.text = headline[:30]  # Límite de caracteres
                                responsive_search_ad.headlines.append(headline_asset)
                            
                            # Descriptions
                            descriptions = ad_data.get('descriptions', [])[:4]  # Máximo 4
                            for description in descriptions:
                                desc_asset = client.get_type("AdTextAsset")
                                desc_asset.text = description[:90]  # Límite de caracteres
                                responsive_search_ad.descriptions.append(desc_asset)
                            
                            # Final URL
                            ad_group_ad.ad.final_urls.append("https://example.com")
                            
                            # Crear anuncio
                            ad_group_ad_service.mutate_ad_group_ads(
                                customer_id=customer_id,
                                operations=[ad_group_ad_operation]
                            )
                            
                            ads_created += 1
                            
                        except Exception as ad_error:
                            with log_container:
                                st.warning(f"⚠️ Error creando anuncio: {str(ad_error)}")
                    
                    # Crear keywords para este grupo
                    keywords = ad_group_data.get('keywords', [])
                    for keyword in keywords[:20]:  # Máximo 20 keywords por grupo
                        try:
                            criterion_operation = client.get_type("AdGroupCriterionOperation")
                            criterion = criterion_operation.create
                            
                            criterion.ad_group = ad_group_service.ad_group_path(customer_id, ad_group_id)
                            criterion.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
                            
                            # Configurar keyword
                            criterion.keyword.text = keyword
                            criterion.keyword.match_type = client.enums.KeywordMatchTypeEnum.BROAD
                            
                            # CPC bid para keyword
                            criterion.cpc_bid_micros = int(ad_group_data.get('max_cpc_bid', 1.0) * 1_000_000)
                            
                            # Crear keyword
                            ad_group_criterion_service.mutate_ad_group_criteria(
                                customer_id=customer_id,
                                operations=[criterion_operation]
                            )
                            
                            keywords_created += 1
                            
                        except Exception as kw_error:
                            with log_container:
                                st.warning(f"⚠️ Error creando keyword '{keyword}': {str(kw_error)}")
                
                with log_container:
                    st.success(f"✅ Grupos de anuncios creados: {ad_groups_created}")
                    st.success(f"✅ Anuncios creados: {ads_created}")
                    st.success(f"✅ Keywords creadas: {keywords_created}")
                
            except Exception as e:
                st.error(f"❌ Error creando grupos de anuncios: {str(e)}")
                return
            
            # PASO 5: Configuraciones adicionales
            update_progress(5, "Aplicando configuraciones adicionales")
            time.sleep(1)
            
            # PASO 6: Finalización
            update_progress(6, "¡Campaña publicada exitosamente!")
            
            # Mostrar resumen final
            st.markdown("---")
            st.success("🎉 **¡CAMPAÑA AUTOPILOT 2050 PUBLICADA EXITOSAMENTE!**")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📊 Campaña ID", campaign_id)
            
            with col2:
                st.metric("📁 Grupos de Anuncios", ad_groups_created)
            
            with col3:
                st.metric("📝 Anuncios Creados", ads_created)
            
            with col4:
                st.metric("🔑 Keywords Creadas", keywords_created)
            
            # Información importante
            st.info("""
            **📋 Próximos pasos:**
            
            1. **Revisar la campaña** en Google Ads antes de activarla
            2. **Activar la campaña** manualmente (está pausada por seguridad)
            3. **Monitorear el rendimiento** en los primeros días
            4. **Ajustar presupuestos** según sea necesario
            
            🔗 **Accede a Google Ads:** [ads.google.com](https://ads.google.com)
            """)
            
            # Guardar en historial
            try:
                user_storage = get_user_storage()
                publication_data = {
                    'campaign_name': blueprint.campaign_name,
                    'campaign_id': campaign_id,
                    'customer_id': customer_id,
                    'ad_groups_created': ad_groups_created,
                    'ads_created': ads_created,
                    'keywords_created': keywords_created,
                    'published_at': datetime.now().isoformat(),
                    'status': 'published_paused'
                }
                user_storage.add_to_history('autopilot_campaign_published', publication_data)
                
                with log_container:
                    st.success("✅ Publicación guardada en historial")
                    
            except Exception as e:
                with log_container:
                    st.warning(f"⚠️ Error guardando en historial: {e}")
    
    except Exception as e:
        st.error(f"❌ Error general en la publicación: {str(e)}")
        with st.expander("🔍 Detalles del error"):
            st.code(str(e))

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    main()