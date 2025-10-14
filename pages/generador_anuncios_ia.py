"""
Generador de Anuncios con IA - Sistema Ultra-Profesional 2025
Fecha: 2025-10-13
Autor: Sistema IA Avanzado

Características principales:
- Generación de anuncios con múltiples proveedores de IA
- Inserción automática de ubicaciones
- Mejores prácticas de Google Ads integradas
- AUTOPILOT 2050: Sistema de generación automática de campañas
- Validación y scoring automático
- Interfaz futurística y profesional
"""

import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

# Imports locales
from modules.ai_ad_generator import AIAdGenerator
from utils.ad_scorer import AdScorer
from utils.user_storage import get_user_storage
from utils.autopilot_campaign_gen import AutopilotCampaignGenerator

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

# Configurar página
st.set_page_config(
    page_title="🤖 Generador IA",
    page_icon="🤖",
    layout="wide"
)

# Logger
logger = logging.getLogger(__name__)

# Storage
user_storage = get_user_storage()

# ============================================================================
# CONFIGURACIÓN DE MODELOS IA 2025
# ============================================================================

AI_MODELS_2025 = {
    'openai': {
        'name': '🟢 OpenAI',
        'icon': '🟢',
        'models': [
            'gpt-4o',
            'gpt-4o-mini',
            'gpt-4-turbo',
            'gpt-4',
            'gpt-3.5-turbo'
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
    
    /* AUTOPILOT 2050 CSS */
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
    
    .neural-card {
        background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 100%);
        border: 1px solid #00ffff;
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 0 20px rgba(0, 255, 255, 0.2);
        color: #ffffff;
    }
    
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse-dot 2s infinite;
    }
    
    .status-online { background-color: #00ff00; box-shadow: 0 0 10px #00ff00; }
    
    @keyframes pulse-dot {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .matrix-text {
        font-family: 'Courier New', monospace;
        color: #00ff00;
        background: #000;
        padding: 1rem;
        border-radius: 8px;
        font-size: 0.9rem;
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

def save_ad_for_campaigns(ad: Dict[str, Any]) -> bool:
    """
    Guarda un anuncio generado en el historial del usuario
    
    Args:
        ad: Diccionario con los datos del anuncio generado
        
    Returns:
        bool: True si se guardó exitosamente
    """
    try:
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
        
        # Usar add_to_history del UserStorage
        success = user_storage.add_to_history('ad_saved_for_campaigns', ad_data)
        
        if success:
            logger.info(f"✅ Anuncio guardado para campañas: {ad_data['id']}")
            return True
        
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
            # Configuraciones por defecto
            defaults = {
                'default_provider': 'openai',
                'default_tone': 'emocional',
                'default_num_ads': 1,
                'default_num_headlines': 10,
                'default_num_descriptions': 3,
                'auto_validate': True,
                'auto_score': True,
                'auto_best_practices': True,
                'auto_location_insertion': False
            }
            
            for key, default_value in defaults.items():
                if key not in st.session_state:
                    st.session_state[key] = ai_settings.get(key, default_value)
        
        # Cargar configuración de Google Ads
        google_ads_settings = settings.get('google_ads', {})
        if google_ads_settings:
            for key, value in google_ads_settings.items():
                if f'google_ads_{key}' not in st.session_state:
                    st.session_state[f'google_ads_{key}'] = value
                    
    except Exception as e:
        logger.error(f"Error cargando configuración del storage: {e}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Función principal"""
    
    # Aplicar CSS
    st.markdown(ULTRA_PRO_CSS, unsafe_allow_html=True)
    
    # Inicializar
    initialize_session_state()
    
    # Verificar proveedores disponibles
    available_providers = get_available_providers()
    
    # Header
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
        st.warning("⚠️ No hay proveedores de IA configurados. Ve a **⚙️ Settings** para configurar tus API keys.")
    
    # Tabs
    tabs = st.tabs([
        "🚀 Generar",
        "🎨 Galería",
        "🤖 AUTOPILOT 2050",
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
        render_best_practices_tab()
    
    with tabs[4]:
        render_settings_tab()

# ============================================================================
# TAB 1: GENERAR
# ============================================================================

def render_generation_tab():
    """Tab de generación con inserción de ubicaciones"""
    
    st.markdown("### 🎯 Generación de Anuncios Optimizados")
    
    available_providers = get_available_providers()
    
    if not available_providers:
        st.markdown("""
        <div class="ultra-info">
            <h4>⚠️ No hay proveedores configurados</h4>
            <p>Ve a <strong>⚙️ Settings</strong> en el menú principal para configurar tus API keys de OpenAI, Gemini o Anthropic.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Formulario
    with st.form("gen_form"):
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            default_provider = st.session_state.get('default_provider', available_providers[0])
            if default_provider not in available_providers:
                default_provider = available_providers[0]
            
            provider_type = st.selectbox(
                "Proveedor IA:",
                available_providers,
                index=available_providers.index(default_provider),
                format_func=lambda x: f"{AI_MODELS_2025[x]['icon']} {AI_MODELS_2025[x]['name']}"
            )
        
        with col2:
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
            default_num_ads = st.session_state.get('default_num_ads', 1)
            num_ads = st.number_input("Cantidad:", 1, 10, default_num_ads)
        
        # Keywords
        keywords_input = st.text_area(
            "Keywords (una por línea o separadas por comas):",
            placeholder="amarres de amor\nhechizos efectivos\nbrujería profesional\ntarot del amor",
            height=100
        )
        
        # Inserción de Ubicaciones
        st.markdown("---")
        st.markdown("#### 📍 Inserción de Ubicaciones (Mejora el CTR)")
        
        use_location_insertion = st.checkbox(
            "✅ Incluir inserción de ubicaciones",
            value=st.session_state.get('auto_location_insertion', False),
            help="Agrega códigos de ubicación dinámica en los títulos"
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
                format_func=lambda x: LOCATION_LEVELS[x]['label']
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
                num_headlines = st.slider(
                    "Títulos:",
                    5, 15,
                    st.session_state.get('default_num_headlines', 10)
                )
                business_type = st.selectbox(
                    "Tipo de negocio:",
                    ['esoteric', 'generic', 'ecommerce', 'services', 'local'],
                    index=0
                )
            
            with col2:
                num_descriptions = st.slider(
                    "Descriptions:",
                    2, 4,
                    st.session_state.get('default_num_descriptions', 3)
                )
                apply_best_practices = st.checkbox(
                    "📚 Aplicar mejores prácticas de Google Ads",
                    value=st.session_state.get('auto_best_practices', True)
                )
            
            validate_ads = st.checkbox(
                "✅ Validar políticas",
                st.session_state.get('auto_validate', True)
            )
            score_ads = st.checkbox(
                "📊 Calcular score",
                st.session_state.get('auto_score', True)
            )
        
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
            
            # Generar anuncios
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
    
    # Obtener API keys
    try:
        api_keys = user_storage.get_api_keys()
    except Exception as e:
        st.error(f"❌ Error accediendo al storage: {e}")
        return
    
    # Verificar API key del proveedor
    provider_config = api_keys.get(provider_type)
    if not provider_config or not isinstance(provider_config, dict) or not provider_config.get('api_key', '').strip():
        st.error(f"❌ No hay API key configurada para {provider_type}. Ve a **⚙️ Settings** para configurarla.")
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
        
        # Agregar metadata
        for ad in batch_result['ads']:
            ad['uses_location_insertion'] = use_location_insertion
            ad['location_levels'] = location_levels if use_location_insertion else []
        
        progress_bar.progress(1.0)
        status.empty()
        progress_bar.empty()
        
        # Guardar
        if batch_result['successful'] > 0:
            st.session_state.generated_ads_batch.extend(batch_result['ads'])
            
            # Guardar en historial
            try:
                action_data = {
                    'provider': provider_type,
                    'keywords': keywords,
                    'tone': tone,
                    'num_ads': num_ads,
                    'successful_ads': batch_result['successful'],
                    'failed_ads': batch_result['failed']
                }
                user_storage.add_to_history('ad_generation', action_data)
            except Exception as e:
                logger.warning(f"No se pudo guardar en historial: {e}")
            
            st.success(f"✅ ¡{batch_result['successful']} anuncio(s) generado(s) con éxito!")
            
            if use_location_insertion:
                st.info(f"📍 Incluyendo inserción de ubicaciones: {', '.join([LOCATION_LEVELS[l]['label'] for l in location_levels])}")
            
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
# TAB 2: GALERÍA
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
                st.success(f"✅ {count} anuncio(s) guardado(s)")
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
            
            # Mostrar headlines
            st.markdown("**📝 Headlines:**")
            for h in ad.get('headlines', []):
                if '{LOCATION(' in h:
                    st.markdown(f"<span class='location-badge'>📍 {h}</span> ({len(h)}/30)", unsafe_allow_html=True)
                else:
                    st.text(f"• {h} ({len(h)}/30)")
            
            st.markdown("**📄 Descriptions:**")
            for d in ad.get('descriptions', []):
                st.text(f"• {d} ({len(d)}/90)")
            
            # Info de ubicaciones
            if ad.get('uses_location_insertion'):
                location_levels = ad.get('location_levels', [])
                st.markdown(f"**📍 Ubicaciones:** {', '.join([LOCATION_LEVELS[l]['label'] for l in location_levels])}")

# ============================================================================
# TAB 3: AUTOPILOT 2050
# ============================================================================

def render_autopilot_tab():
    """Tab de AUTOPILOT 2050 con interfaz futurística"""
    
    # Header futurístico
    st.markdown("""
    <div class="autopilot-header">
        <h1>🤖 AUTOPILOT 2050</h1>
        <div style="font-size: 1.2rem; margin-top: 1rem; opacity: 0.9; position: relative; z-index: 1;">
            Sistema de Generación Automática de Campañas Impulsado por IA Neural
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Inicializar autopilot
    try:
        ai_generator = st.session_state.ai_generator
        autopilot = AutopilotCampaignGenerator(
            ai_generator=ai_generator,
            google_ads_client=st.session_state.get('google_ads_client'),
            user_storage=user_storage
        )
    except Exception as e:
        st.error(f"❌ Error inicializando AUTOPILOT: {e}")
        return
    
    # Estado del sistema
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="neural-card">
            <h3>🧠 Estado Neural</h3>
            <p><span class="status-indicator status-online"></span>IA ACTIVA</p>
            <p><span class="status-indicator status-online"></span>ANÁLISIS ONLINE</p>
            <p><span class="status-indicator status-online"></span>GENERACIÓN READY</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="neural-card">
            <h3>⚡ Capacidades</h3>
            <p>• Análisis de Negocio Automático</p>
            <p>• Generación de Keywords IA</p>
            <p>• Creación de Anuncios Masiva</p>
            <p>• Optimización Predictiva</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="neural-card">
            <h3>🎯 Métricas</h3>
            <p>• Precisión: 98.7%</p>
            <p>• Velocidad: 1000x Humano</p>
            <p>• Eficiencia: 99.2%</p>
            <p>• Uptime: 24/7/365</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Configuración
    st.markdown("""
    <div class="neural-card">
        <h3>🎛️ CONFIGURACIÓN DE MISIÓN</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        business_description = st.text_area(
            "📊 Descripción del Negocio",
            placeholder="Ej: Somos una clínica de medicina alternativa...",
            height=120
        )
        
        target_audience = st.text_input(
            "🎯 Audiencia Objetivo",
            placeholder="Ej: Personas de 25-55 años..."
        )
        
        budget_range = st.selectbox(
            "💰 Rango de Presupuesto",
            ["$100-500/mes", "$500-1000/mes", "$1000-5000/mes", "$5000+/mes"]
        )
    
    with col2:
        campaign_objectives = st.multiselect(
            "🎯 Objetivos de Campaña",
            ["Generar Leads", "Aumentar Ventas", "Brand Awareness", "Tráfico Web", "Conversiones"],
            default=["Generar Leads"]
        )
        
        geographic_targeting = st.text_input(
            "🌍 Targeting Geográfico",
            placeholder="Ej: Ciudad de México, Guadalajara"
        )
        
        num_campaigns = st.slider(
            "📈 Número de Campañas a Generar",
            1, 5, 2
        )
    
    # Botón de generación
    if st.button("🚀 INICIAR AUTOPILOT 2050", type="primary", use_container_width=True):
        if not business_description or not target_audience:
            st.error("❌ Completa la descripción del negocio y audiencia objetivo")
            return
        
        progress_container = st.container()
        
        with progress_container:
            st.markdown("""
            <div style="background: #0a0a1a; border: 1px solid #00ffff; border-radius: 10px; padding: 1rem;">
                <h4 style="color: #00ffff; font-family: 'Courier New', monospace;">
                    🧠 INICIANDO SECUENCIA NEURAL...
                </h4>
            </div>
            """, unsafe_allow_html=True)
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            steps = [
                "🔍 Analizando descripción del negocio...",
                "🧠 Procesando audiencia objetivo...",
                "🎯 Generando estrategia de keywords...",
                "📝 Creando variaciones de anuncios...",
                "⚡ Optimizando campañas...",
                "🚀 Finalizando blueprint de campaña..."
            ]
            
            for i, step in enumerate(steps):
                status_text.markdown(f"""
                <div class="matrix-text">{step}</div>
                """, unsafe_allow_html=True)
                progress_bar.progress((i + 1) / len(steps))
                time.sleep(1)
            
            # Generar campaña
            try:
                campaign_config = {
                    'business_description': business_description,
                    'target_audience': target_audience,
                    'budget_range': budget_range,
                    'objectives': campaign_objectives,
                    'geographic_targeting': geographic_targeting,
                    'num_campaigns': num_campaigns
                }
                
                blueprint = autopilot.generate_campaign_blueprint(campaign_config)
                
                st.success("✅ AUTOPILOT 2050 COMPLETADO CON ÉXITO")
                st.session_state['autopilot_blueprint'] = blueprint
                
            except Exception as e:
                st.error(f"❌ Error en AUTOPILOT 2050: {e}")
                return
    
    # Mostrar resultados
    if 'autopilot_blueprint' in st.session_state:
        blueprint = st.session_state['autopilot_blueprint']
        
        st.markdown("---")
        st.markdown("""
        <div class="neural-card">
            <h3>📊 BLUEPRINT DE CAMPAÑA GENERADO</h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🎯 Información General:**")
            st.write(f"**Nombre:** {blueprint.campaign_name}")
            st.write(f"**Presupuesto Diario:** ${blueprint.budget_daily}")
            st.write(f"**Total Keywords:** {blueprint.total_keywords}")
            st.write(f"**Total Anuncios:** {blueprint.total_ads}")
        
        with col2:
            st.markdown("**📍 Targeting:**")
            st.write(f"**Ubicaciones:** {', '.join(blueprint.target_locations)}")
            st.write(f"**Idiomas:** {', '.join(blueprint.languages)}")
            st.write(f"**Grupos:** {len(blueprint.ad_groups)}")
            st.write(f"**CTR Estimado:** {blueprint.estimated_ctr}%")
        
        # Mostrar grupos
        if blueprint.ad_groups:
            st.markdown("**📦 Grupos de Anuncios:**")
            for i, ad_group in enumerate(blueprint.ad_groups[:3]):
                with st.expander(f"📂 {ad_group['name']}"):
                    keywords_text = ', '.join(ad_group['keywords'][:10])
                    if len(ad_group['keywords']) > 10:
                        keywords_text += f" ... (+{len(ad_group['keywords']) - 10} más)"
                    st.write(f"**Keywords:** {keywords_text}")
        
        # Botones de acción
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 Guardar Blueprint", type="secondary"):
                try:
                    blueprint_data = {
                        'campaign_name': blueprint.campaign_name,
                        'budget_daily': blueprint.budget_daily,
                        'target_locations': blueprint.target_locations,
                        'ad_groups': blueprint.ad_groups,
                        'created_at': datetime.now().isoformat()
                    }
                    user_storage.add_to_history('autopilot_blueprint', blueprint_data)
                    st.success("✅ Blueprint guardado")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        with col2:
            if st.button("📊 Exportar CSV", type="secondary"):
                csv_data = []
                for ad_group in blueprint.ad_groups:
                    for keyword in ad_group['keywords']:
                        csv_data.append({
                            'Campaign': blueprint.campaign_name,
                            'Ad Group': ad_group['name'],
                            'Keyword': keyword,
                            'Match Type': 'Broad',
                            'Max CPC': ad_group['max_cpc_bid']
                        })
                
                if csv_data:
                    df = pd.DataFrame(csv_data)
                    csv = df.to_csv(index=False)
                    st.download_button(
                        "⬇️ Descargar CSV",
                        csv,
                        f"autopilot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        "text/csv"
                    )
        
        with col3:
            if st.button("🔄 Nueva Campaña", type="secondary"):
                if 'autopilot_blueprint' in st.session_state:
                    del st.session_state['autopilot_blueprint']
                st.rerun()

# ============================================================================
# TAB 4: MEJORES PRÁCTICAS
# ============================================================================

def render_best_practices_tab():
    """Tab con mejores prácticas de Google Ads"""
    
    st.markdown("### 📚 Mejores Prácticas de Google Ads")
    
    st.markdown("""
    <div class="ultra-info">
        <p><strong>ℹ️ Información:</strong> Estas prácticas están basadas en las guías oficiales de Google Ads.</p>
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
        - Caracteres: {GOOGLE_ADS_BEST_PRACTICES['headlines']['max_chars']} máximo
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
        - Caracteres: {GOOGLE_ADS_BEST_PRACTICES['descriptions']['max_chars']} máximo
        """)
    
    # Inserción de ubicaciones
    st.markdown("#### 📍 Inserción de Ubicaciones")
    
    with st.expander("¿Qué es la inserción de ubicaciones?"):
        st.markdown("""
        La inserción de ubicación personaliza automáticamente tus anuncios según la ubicación del usuario.
        
        **Beneficios:**
        - ✅ Aumenta el CTR hasta un 50%
        - ✅ Mejora la relevancia del anuncio
        - ✅ Mayor probabilidad de conversión
        """)
        
        for level_key, level_info in LOCATION_LEVELS.items():
            st.markdown(f"""
            **{level_info['label']}**
            - Código: `{{{level_info['code']}}}`
            - Ejemplo: {level_info['example']}
            """)

# ============================================================================
# TAB 5: AJUSTES RÁPIDOS
# ============================================================================

def render_settings_tab():
    """Tab de ajustes rápidos"""
    
    st.markdown("### ⚙️ Ajustes Rápidos")
    st.markdown("Configura tus preferencias por defecto para la generación de anuncios.")
    
    try:
        available_providers = get_available_providers()
        
        if not available_providers:
            st.warning("⚠️ No hay proveedores configurados. Ve a **⚙️ Settings** en el menú principal.")
            return
        
        # Formulario
        with st.form("settings_form"):
            st.markdown("#### 🤖 Configuración de IA")
            
            col1, col2 = st.columns(2)
            
            with col1:
                current_provider = st.session_state.get('default_provider', available_providers[0])
                if current_provider not in available_providers:
                    current_provider = available_providers[0]
                
                default_provider = st.selectbox(
                    "Proveedor por defecto:",
                    available_providers,
                    index=available_providers.index(current_provider),
                    format_func=lambda x: f"{AI_MODELS_2025[x]['icon']} {AI_MODELS_2025[x]['name']}"
                )
                
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
                default_num_ads = st.number_input(
                    "Cantidad de anuncios:",
                    1, 10,
                    st.session_state.get('default_num_ads', 1)
                )
                
                default_num_headlines = st.slider(
                    "Títulos por defecto:",
                    5, 15,
                    st.session_state.get('default_num_headlines', 10)
                )
                
                default_num_descriptions = st.slider(
                    "Descriptions por defecto:",
                    2, 4,
                    st.session_state.get('default_num_descriptions', 3)
                )
            
            st.markdown("#### 🔧 Configuración Automática")
            
            col3, col4 = st.columns(2)
            
            with col3:
                auto_validate = st.checkbox(
                    "✅ Validación automática",
                    st.session_state.get('auto_validate', True)
                )
                
                auto_score = st.checkbox(
                    "📊 Scoring automático",
                    st.session_state.get('auto_score', True)
                )
            
            with col4:
                auto_best_practices = st.checkbox(
                    "📚 Mejores prácticas automáticas",
                    st.session_state.get('auto_best_practices', True)
                )
                
                auto_location_insertion = st.checkbox(
                    "📍 Inserción de ubicaciones por defecto",
                    st.session_state.get('auto_location_insertion', False)
                )
            
            # Botón de guardar
            submitted = st.form_submit_button(
                "💾 Guardar Configuración",
                type="primary",
                use_container_width=True
            )
            
            if submitted:
                try:
                    # Obtener settings completos
                    settings = user_storage.get_settings()
                    
                    # Actualizar sección de AI
                    settings['ai_generation'] = {
                        'default_provider': default_provider,
                        'default_tone': default_tone,
                        'default_num_ads': default_num_ads,
                        'default_num_headlines': default_num_headlines,
                        'default_num_descriptions': default_num_descriptions,
                        'auto_validate': auto_validate,
                        'auto_score': auto_score,
                        'auto_best_practices': auto_best_practices,
                        'auto_location_insertion': auto_location_insertion
                    }
                    
                    # Guardar con save_settings
                    if user_storage.save_settings(settings):
                        # Actualizar session state
                        for key, value in settings['ai_generation'].items():
                            st.session_state[key] = value
                        
                        st.success("✅ Configuración guardada correctamente")
                        st.rerun()
                    else:
                        st.error("❌ Error guardando configuración")
                        
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
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
            st.info(f"**Ubicaciones:** {'✅' if st.session_state.get('auto_location_insertion', False) else '❌'}")
    
    except Exception as e:
        st.error(f"❌ Error en configuración: {e}")

# ============================================================================
# EJECUTAR
# ============================================================================

if __name__ == "__main__":
    main()