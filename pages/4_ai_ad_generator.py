"""
🤖 GENERADOR DE ANUNCIOS CON IA - VERSIÓN ULTRA-PROFESIONAL 2025
Página de Streamlit para generación de anuncios con IA
Versión: 3.0 Ultra
Fecha: 2025-01-13
"""

import streamlit as st
import pandas as pd
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import sys
import os
from pathlib import Path

# ============================================================================
# CONFIGURAR PATH
# ============================================================================

# Agregar directorio raíz al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ============================================================================
# IMPORTS
# ============================================================================

try:
    from modules.ai_ad_generator import AIAdGenerator
    from utils.ad_scorer import AdScorer
    logger = logging.getLogger(__name__)
    logger.info("✅ Módulos importados correctamente")
except ImportError as e:
    st.error(f"❌ Error importando módulos: {e}")
    st.stop()

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
    }
}

TONE_PRESETS = {
    'emocional': {'icon': '❤️', 'description': 'Apela a sentimientos'},
    'urgente': {'icon': '⚡', 'description': 'Crea inmediatez'},
    'profesional': {'icon': '💼', 'description': 'Tono corporativo'},
    'místico': {'icon': '🔮', 'description': 'Lenguaje espiritual'},
    'poderoso': {'icon': '💪', 'description': 'Resultados y efectividad'},
    'esperanzador': {'icon': '🌟', 'description': 'Optimismo y posibilidad'},
    'tranquilizador': {'icon': '🕊️', 'description': 'Calma y paz'}
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
    
    .ultra-metric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transition: transform 0.3s ease;
    }
    
    .ultra-metric:hover {
        transform: scale(1.05);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .provider-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border: 2px solid transparent;
        transition: all 0.3s ease;
    }
    
    .provider-card.connected {
        border-color: #4caf50;
        background: linear-gradient(135deg, rgba(76, 175, 80, 0.05) 0%, rgba(69, 160, 73, 0.05) 100%);
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
# FUNCIONES DE ALMACENAMIENTO
# ============================================================================

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

def clear_api_config(provider: str):
    """Limpia configuración de API"""
    if 'api_configs' in st.session_state and provider in st.session_state.api_configs:
        del st.session_state.api_configs[provider]

def get_configured_providers() -> List[str]:
    """Obtiene proveedores configurados"""
    if 'api_configs' not in st.session_state:
        return []
    
    return [
        provider for provider, config in st.session_state.api_configs.items()
        if config.get('api_key')
    ]

def save_ad_for_campaigns(ad_data: Dict[str, Any]) -> bool:
    """Guarda anuncio para campañas"""
    try:
        if 'pending_ai_ads' not in st.session_state:
            st.session_state.pending_ai_ads = []
        
        ad_for_campaign = {
            'id': ad_data.get('id', f"AD_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"),
            'timestamp': ad_data.get('timestamp', datetime.now().isoformat()),
            'provider': ad_data.get('provider', 'Unknown'),
            'model': ad_data.get('model', 'Unknown'),
            'keywords': ad_data.get('keywords', []),
            'tone': ad_data.get('tone', 'profesional'),
            'headlines': ad_data.get('headlines', []),
            'descriptions': ad_data.get('descriptions', []),
            'validation_result': ad_data.get('validation_result', {}),
            'score': ad_data.get('score', 0),
            'used': False
        }
        
        existing_ids = [ad['id'] for ad in st.session_state.pending_ai_ads]
        if ad_for_campaign['id'] not in existing_ids:
            st.session_state.pending_ai_ads.append(ad_for_campaign)
            return True
        
        return False
    
    except Exception as e:
        st.error(f"Error guardando: {e}")
        return False

def get_pending_ads_count() -> int:
    """Obtiene anuncios pendientes"""
    if 'pending_ai_ads' not in st.session_state:
        return 0
    
    return len([ad for ad in st.session_state.pending_ai_ads if not ad.get('used', False)])

# ============================================================================
# INICIALIZACIÓN
# ============================================================================

def initialize_session_state():
    """Inicializa session state"""
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

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Función principal"""
    
    # Aplicar CSS
    st.markdown(ULTRA_PRO_CSS, unsafe_allow_html=True)
    
    # Inicializar
    initialize_session_state()
    
    # Header
    st.markdown("""
    <div class="ultra-header">
        <h1>🤖 Generador de Anuncios con IA</h1>
        <p>Sistema Ultra-Profesional 2025 | GPT-4o, Gemini 2.0, Claude 3</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabs
    tabs = st.tabs([
        "🚀 Generar",
        "🎨 Galería",
        "⚙️ Config API",
        "📦 Export/Import"
    ])
    
    # Tab 1: Generar
    with tabs[0]:
        render_generation_tab()
    
    # Tab 2: Galería
    with tabs[1]:
        render_gallery_tab()
    
    # Tab 3: Config
    with tabs[2]:
        render_config_tab()
    
    # Tab 4: Export
    with tabs[3]:
        render_export_tab()

# ============================================================================
# TAB 1: GENERAR
# ============================================================================

def render_generation_tab():
    """Tab de generación"""
    
    st.markdown("### 🎯 Generación de Anuncios")
    
    configured_providers = get_configured_providers()
    
    if not configured_providers:
        st.markdown("""
        <div class="ultra-info">
            <h4>⚠️ No hay proveedores configurados</h4>
            <p>Ve a la pestaña <strong>⚙️ Config API</strong> para configurar OpenAI o Gemini.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Formulario
    with st.form("gen_form"):
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            provider_type = st.selectbox(
                "Proveedor:",
                configured_providers,
                format_func=lambda x: f"{AI_MODELS_2025[x]['icon']} {AI_MODELS_2025[x]['name']}"
            )
        
        with col2:
            tone = st.selectbox(
                "Tono:",
                list(TONE_PRESETS.keys()),
                format_func=lambda x: f"{TONE_PRESETS[x]['icon']} {x.title()}"
            )
        
        with col3:
            num_ads = st.number_input("Cantidad:", 1, 10, 1)
        
        keywords_input = st.text_area(
            "Keywords (una por línea o separadas por comas):",
            placeholder="amarres de amor\nhechizos efectivos\nbrujería profesional",
            height=120
        )
        
        with st.expander("⚙️ Avanzado"):
            col1, col2 = st.columns(2)
            
            with col1:
                num_headlines = st.slider("Títulos:", 5, 15, 10)
            
            with col2:
                num_descriptions = st.slider("Descriptions:", 2, 4, 3)
            
            validate_ads = st.checkbox("✅ Validar políticas", True)
            score_ads = st.checkbox("📊 Calcular score", True)
        
        submitted = st.form_submit_button(
            f"✨ Generar {num_ads} Anuncio{'s' if num_ads > 1 else ''}",
            type="primary",
            use_container_width=True
        )
        
        if submitted:
            if not keywords_input.strip():
                st.error("❌ Ingresa keywords")
                return
            
            keywords = [kw.strip() for kw in keywords_input.replace(',', '\n').split('\n') if kw.strip()]
            
            if not keywords:
                st.error("❌ No hay keywords válidas")
                return
            
            # Generar
            generate_ads(
                provider_type,
                keywords,
                tone,
                num_ads,
                num_headlines,
                num_descriptions,
                validate_ads,
                score_ads
            )

def generate_ads(provider_type, keywords, tone, num_ads, num_headlines, num_descriptions, validate, score):
    """Genera anuncios"""
    
    provider_config = load_api_config(provider_type)
    
    if not provider_config or not provider_config.get('api_key'):
        st.error(f"❌ No hay configuración para {provider_type}")
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
        
        success = ai_gen.set_provider(
            provider_type=provider_type,
            api_key=provider_config['api_key'],
            model=provider_config['model']
        )
        
        if not success:
            st.error(f"❌ No se pudo configurar {provider_type}")
            return
        
        # Generar
        status.text(f"🎨 Generando {num_ads} anuncio(s)...")
        progress_bar.progress(0.5)
        
        batch_result = ai_gen.generate_batch(
            keywords=keywords,
            num_ads=num_ads,
            num_headlines=num_headlines,
            num_descriptions=num_descriptions,
            tone=tone,
            validate=validate,
            business_type='esoteric',
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
        
        progress_bar.progress(1.0)
        status.empty()
        progress_bar.empty()
        
        # Guardar
        if batch_result['successful'] > 0:
            st.session_state.generated_ads_batch.extend(batch_result['ads'])
            
            st.success(f"✅ ¡{batch_result['successful']} anuncio(s) generado(s)!")
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
            
            st.info("👉 Ve a **🎨 Galería** para ver los resultados")
        else:
            st.error("❌ No se pudo generar ningún anuncio")
    
    except Exception as e:
        st.error(f"❌ Error: {e}")

# ============================================================================
# TAB 2: GALERÍA
# ============================================================================

def render_gallery_tab():
    """Tab de galería"""
    
    st.markdown("### 🎨 Galería de Anuncios")
    
    if not st.session_state.generated_ads_batch:
        st.info("ℹ️ No hay anuncios generados")
        return
    
    total = len(st.session_state.generated_ads_batch)
    st.success(f"📊 **{total}** anuncio(s) generado(s)")
    
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
        
        with st.expander(f"📢 Anuncio #{idx+1} - {ad.get('tone', 'N/A').title()}", expanded=(idx==0)):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Proveedor", ad.get('provider', 'N/A'))
            
            with col2:
                st.metric("Tono", ad.get('tone', 'N/A'))
            
            with col3:
                st.metric("Score", f"{ad.get('score', 0):.1f}")
            
            st.markdown("**📝 Headlines:**")
            for h in ad.get('headlines', []):
                st.text(f"• {h} ({len(h)}/30)")
            
            st.markdown("**📄 Descriptions:**")
            for d in ad.get('descriptions', []):
                st.text(f"• {d} ({len(d)}/90)")

# ============================================================================
# TAB 3: CONFIG API
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
# TAB 4: EXPORT
# ============================================================================

def render_export_tab():
    """Tab de exportación"""
    
    st.markdown("### 📦 Importar/Exportar")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📤 Exportar")
        
        if st.session_state.generated_ads_batch:
            if st.button("📥 Exportar JSON", use_container_width=True):
                data = {
                    'exported_at': datetime.now().isoformat(),
                    'total': len(st.session_state.generated_ads_batch),
                    'ads': st.session_state.generated_ads_batch
                }
                
                json_str = json.dumps(data, indent=2, ensure_ascii=False)
                
                st.download_button(
                    "💾 Descargar",
                    json_str,
                    f"anuncios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    "application/json"
                )
        else:
            st.info("No hay anuncios")
    
    with col2:
        st.markdown("#### 📥 Importar")
        
        uploaded = st.file_uploader("Archivo JSON:", type=['json'])
        
        if uploaded:
            if st.button("📥 Importar", use_container_width=True):
                try:
                    data = json.loads(uploaded.read())
                    ads = data.get('ads', [])
                    
                    st.session_state.generated_ads_batch.extend(ads)
                    st.success(f"✅ {len(ads)} importados")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {e}")

# ============================================================================
# EJECUTAR
# ============================================================================

if __name__ == "__main__":
    main()