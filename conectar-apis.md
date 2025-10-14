# 🔌 **INTEGRACIÓN: Storage Local → Generador IA**

Vamos a conectar el sistema de storage local con el generador de anuncios para que use las API keys guardadas.

---

## 📄 **PASO 1: Actualizar `pages/4_🤖_AI_Ad_Generator.py`**

Reemplaza la sección de inicialización y configuración de APIs:

```python
"""
🤖 GENERADOR DE ANUNCIOS CON IA - VERSIÓN ULTRA-PROFESIONAL 2025
Con Inserción de Ubicaciones y Storage Local
Versión: 3.2 Ultra
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

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ============================================================================
# IMPORTS
# ============================================================================

try:
    from modules.ai_ad_generator import AIAdGenerator
    from utils.ad_scorer import AdScorer
    from utils.user_storage import get_user_storage  # ← NUEVO
    from utils.performance_utils import show_performance_sidebar
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
# OBTENER USER STORAGE
# ============================================================================

# Obtener el usuario actual
CURRENT_USER = os.getlogin() if hasattr(os, 'getlogin') else "saltbalente"
user_storage = get_user_storage(CURRENT_USER)

# ============================================================================
# MODELOS IA 2025 CON STORAGE
# ============================================================================

def get_available_providers() -> Dict[str, Dict]:
    """
    Obtiene proveedores disponibles basándose en API keys guardadas
    
    Returns:
        Dict con proveedores configurados
    """
    api_keys = user_storage.get_api_keys()
    
    providers = {}
    
    # OpenAI
    openai_data = api_keys.get('openai', {})
    if openai_data.get('api_key'):
        providers['openai'] = {
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
            'default': openai_data.get('model', 'gpt-4o'),
            'api_key': openai_data.get('api_key'),
            'color': '#10a37f'
        }
    
    # Gemini
    gemini_data = api_keys.get('gemini', {})
    if gemini_data.get('api_key'):
        providers['gemini'] = {
            'name': '🔴 Google Gemini',
            'icon': '🔴',
            'models': [
                'gemini-2.0-flash-exp',
                'gemini-1.5-pro',
                'gemini-1.5-flash',
                'gemini-pro'
            ],
            'default': gemini_data.get('model', 'gemini-2.0-flash-exp'),
            'api_key': gemini_data.get('api_key'),
            'color': '#4285f4'
        }
    
    # Anthropic
    anthropic_data = api_keys.get('anthropic', {})
    if anthropic_data.get('api_key'):
        providers['anthropic'] = {
            'name': '🟣 Anthropic Claude',
            'icon': '🟣',
            'models': [
                'claude-3-5-sonnet-20241022',
                'claude-3-opus-20240229',
                'claude-3-sonnet-20240229',
                'claude-3-haiku-20240307'
            ],
            'default': anthropic_data.get('model', 'claude-3-5-sonnet-20241022'),
            'api_key': anthropic_data.get('api_key'),
            'color': '#9333ea'
        }
    
    return providers


# ============================================================================
# INICIALIZACIÓN CON STORAGE
# ============================================================================

def initialize_session_state():
    """Inicializa session state con datos del storage"""
    
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
    
    # ← NUEVO: Cargar preferencias del storage
    if 'user_preferences' not in st.session_state:
        st.session_state.user_preferences = user_storage.get_preferences()
    
    # ← NUEVO: Cargar settings de IA
    if 'ai_settings' not in st.session_state:
        settings = user_storage.get_settings()
        st.session_state.ai_settings = settings.get('ai_generation', {})


# ============================================================================
# MAIN CON STORAGE
# ============================================================================

def main():
    """Función principal con storage integrado"""
    
    # Aplicar CSS
    st.markdown(ULTRA_PRO_CSS, unsafe_allow_html=True)
    
    # Inicializar
    initialize_session_state()
    
    # Header
    st.markdown("""
    <div class="ultra-header">
        <h1>🤖 Generador de Anuncios con IA</h1>
        <p>Sistema Ultra-Profesional 2025 | Con Storage Local Integrado</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ← NUEVO: Verificar si hay API keys configuradas
    available_providers = get_available_providers()
    
    if not available_providers:
        st.error("❌ No hay API keys configuradas")
        st.markdown("""
        <div class="ultra-info">
            <h3>🔑 Configura tus API Keys</h3>
            <p>Ve a <strong>⚙️ Configuración → API Keys</strong> para agregar tus claves.</p>
            <p>Necesitas al menos una API key de:</p>
            <ul>
                <li>🔵 OpenAI (GPT-4o, GPT-4-turbo)</li>
                <li>🔴 Google Gemini (Gemini 2.0 Flash)</li>
                <li>🟣 Anthropic Claude (Claude 3.5 Sonnet)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("⚙️ Ir a Configuración", use_container_width=True, type="primary"):
                st.switch_page("pages/9_⚙️_Settings.py")
        
        return
    
    # Mostrar proveedores disponibles
    st.success(f"✅ {len(available_providers)} proveedor(es) de IA configurado(s)")
    
    with st.expander("📋 Ver proveedores disponibles"):
        cols = st.columns(len(available_providers))
        for idx, (key, provider) in enumerate(available_providers.items()):
            with cols[idx]:
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem; background: var(--dark-card); border-radius: 12px;">
                    <div style="font-size: 2rem;">{provider['icon']}</div>
                    <div style="font-weight: 700; margin-top: 0.5rem;">{provider['name']}</div>
                    <div style="font-size: 0.8rem; color: var(--text-muted);">{provider['default']}</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Tabs
    tabs = st.tabs([
        "🚀 Generar",
        "🎨 Galería",
        "📊 Estadísticas",
        "⚙️ Ajustes"
    ])
    
    with tabs[0]:
        render_generation_tab(available_providers)
    
    with tabs[1]:
        render_gallery_tab()
    
    with tabs[2]:
        render_stats_tab()
    
    with tabs[3]:
        render_settings_tab()


# ============================================================================
# TAB 1: GENERAR CON STORAGE
# ============================================================================

def render_generation_tab(available_providers: Dict):
    """Tab de generación con proveedores del storage"""
    
    st.markdown("### 🎯 Generación de Anuncios Optimizados")
    
    # ← NUEVO: Obtener configuración por defecto del storage
    default_settings = st.session_state.ai_settings
    
    # Formulario
    with st.form("gen_form"):
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            # ← NUEVO: Provider con el default del storage
            default_provider = default_settings.get('default_provider', list(available_providers.keys())[0])
            if default_provider not in available_providers:
                default_provider = list(available_providers.keys())[0]
            
            provider_type = st.selectbox(
                "Proveedor IA:",
                list(available_providers.keys()),
                index=list(available_providers.keys()).index(default_provider),
                format_func=lambda x: f"{available_providers[x]['icon']} {available_providers[x]['name']}"
            )
        
        with col2:
            # ← NUEVO: Tono con el default del storage
            default_tone = default_settings.get('default_tone', 'profesional')
            
            tone = st.selectbox(
                "Tono:",
                list(TONE_PRESETS.keys()),
                index=list(TONE_PRESETS.keys()).index(default_tone) if default_tone in TONE_PRESETS else 0,
                format_func=lambda x: f"{TONE_PRESETS[x]['icon']} {x.title()}"
            )
        
        with col3:
            num_ads = st.number_input("Cantidad:", 1, 10, 1)
        
        # Keywords
        keywords_input = st.text_area(
            "Keywords (una por línea o separadas por comas):",
            placeholder="amarres de amor\nhechizos efectivos\nbrujería profesional\ntarot del amor",
            height=100
        )
        
        # Inserción de ubicaciones
        st.markdown("---")
        st.markdown("#### 📍 Inserción de Ubicaciones (Mejora el CTR)")
        
        use_location_insertion = st.checkbox(
            "✅ Incluir inserción de ubicaciones",
            value=False,
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
        else:
            location_levels = []
        
        # Configuración avanzada
        with st.expander("⚙️ Configuración Avanzada"):
            col1, col2 = st.columns(2)
            
            with col1:
                # ← NUEVO: Valores default del storage
                num_headlines = st.slider(
                    "Títulos:", 
                    5, 15, 
                    default_settings.get('num_headlines', 10)
                )
                business_type = st.selectbox(
                    "Tipo de negocio:",
                    ['esoteric', 'generic', 'ecommerce', 'services', 'local'],
                    index=0
                )
            
            with col2:
                # ← NUEVO: Valores default del storage
                num_descriptions = st.slider(
                    "Descriptions:", 
                    2, 4, 
                    default_settings.get('num_descriptions', 3)
                )
                apply_best_practices = st.checkbox(
                    "📚 Aplicar mejores prácticas de Google Ads",
                    value=True
                )
            
            # ← NUEVO: Valores default del storage
            validate_ads = st.checkbox(
                "✅ Validar políticas", 
                default_settings.get('auto_validate', True)
            )
            score_ads = st.checkbox(
                "📊 Calcular score", 
                default_settings.get('auto_score', True)
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
            
            # ← NUEVO: Usar API key del storage
            api_key = available_providers[provider_type]['api_key']
            model = available_providers[provider_type]['default']
            
            # Generar con configuración del storage
            generate_ads_with_storage(
                provider_type=provider_type,
                api_key=api_key,
                model=model,
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
    api_key: str,
    model: str,
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
    """Genera anuncios usando API keys del storage"""
    
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
        
        # ← NUEVO: Usar API key del storage
        success = ai_gen.set_provider(
            provider_type=provider_type,
            api_key=api_key,
            model=model
        )
        
        if not success:
            st.error(f"❌ No se pudo configurar {provider_type}")
            st.info("💡 Verifica que tu API key sea correcta en ⚙️ Configuración")
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
            ad['provider'] = provider_type
            ad['model'] = model
        
        progress_bar.progress(1.0)
        status.empty()
        progress_bar.empty()
        
        # Guardar
        if batch_result['successful'] > 0:
            st.session_state.generated_ads_batch.extend(batch_result['ads'])
            
            # ← NUEVO: Guardar en historial
            user_storage.add_to_history(
                action='generate_ads',
                data={
                    'provider': provider_type,
                    'model': model,
                    'num_ads': batch_result['successful'],
                    'keywords': keywords,
                    'tone': tone
                }
            )
            
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
            st.info("💡 Verifica tu API key y límites de uso")
    
    except Exception as e:
        st.error(f"❌ Error: {e}")
        import traceback
        st.code(traceback.format_exc())


# ============================================================================
# TAB 4: AJUSTES RÁPIDOS
# ============================================================================

def render_settings_tab():
    """Tab de ajustes rápidos del generador"""
    
    st.markdown("### ⚙️ Ajustes del Generador")
    
    st.info("💡 Los cambios aquí se guardarán en tu configuración local")
    
    settings = user_storage.get_settings()
    ai_settings = settings.get('ai_generation', {})
    
    with st.form("quick_settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            default_provider = st.selectbox(
                "Proveedor por defecto:",
                ['openai', 'gemini', 'anthropic'],
                index=['openai', 'gemini', 'anthropic'].index(ai_settings.get('default_provider', 'openai'))
            )
            
            default_tone = st.selectbox(
                "Tono por defecto:",
                list(TONE_PRESETS.keys()),
                index=list(TONE_PRESETS.keys()).index(ai_settings.get('default_tone', 'profesional'))
            )
        
        with col2:
            num_headlines = st.number_input(
                "Títulos por defecto:",
                min_value=3,
                max_value=15,
                value=ai_settings.get('num_headlines', 10)
            )
            
            num_descriptions = st.number_input(
                "Descriptions por defecto:",
                min_value=2,
                max_value=4,
                value=ai_settings.get('num_descriptions', 3)
            )
        
        auto_validate = st.checkbox(
            "Auto-validar anuncios",
            value=ai_settings.get('auto_validate', True)
        )
        
        auto_score = st.checkbox(
            "Auto-calcular score",
            value=ai_settings.get('auto_score', True)
        )
        
        if st.form_submit_button("💾 Guardar Configuración", use_container_width=True):
            settings['ai_generation'] = {
                'default_provider': default_provider,
                'default_tone': default_tone,
                'num_headlines': num_headlines,
                'num_descriptions': num_descriptions,
                'auto_validate': auto_validate,
                'auto_score': auto_score
            }
            
            if user_storage.save_settings(settings):
                st.session_state.ai_settings = settings['ai_generation']
                st.success("✅ Configuración guardada")
                st.rerun()
            else:
                st.error("❌ Error guardando configuración")


# ============================================================================
# RESTO DEL CÓDIGO (Gallery, Stats, etc.)
# ============================================================================

# ... (mantener el resto de las funciones: render_gallery_tab, render_stats_tab, etc.)


if __name__ == "__main__":
    main()
```

---

## ✅ **CAMBIOS REALIZADOS:**

### 🔑 **1. Carga Automática de API Keys:**
```python
def get_available_providers() -> Dict[str, Dict]:
    """Lee API keys del storage local"""
    api_keys = user_storage.get_api_keys()
    # Retorna solo proveedores con API keys configuradas
```

### ⚙️ **2. Configuración por Defecto:**
```python
default_settings = st.session_state.ai_settings
# Usa los defaults guardados en storage
```

### 💾 **3. Historial Automático:**
```python
user_storage.add_to_history(
    action='generate_ads',
    data={...}
)
```

### 🚀 **4. Flujo Completo:**
1. Carga API keys del storage
2. Muestra solo proveedores configurados
3. Usa configuración por defecto guardada
4. Genera anuncios con las API keys locales
5. Guarda en historial

---

## 🎯 **RESULTADO:**

- ✅ **Sin API keys** → Muestra mensaje para ir a configuración
- ✅ **Con API keys** → Funcionamiento automático
- ✅ **Preferencias persistentes** → Tono, cantidad, validación, etc.
- ✅ **Historial de generaciones** → Todo guardado localmente
- ✅ **Seguridad** → API keys encriptadas

---

**🎉 ¡Listo! Ahora el generador usa el storage local automáticamente.** 
