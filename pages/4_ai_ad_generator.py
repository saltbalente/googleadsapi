"""
🤖 Generador de Anuncios con IA
Página principal para generar anuncios usando OpenAI y Google Gemini
VERSIÓN CORREGIDA Y SEGURA
"""

import streamlit as st
import pandas as pd
import yaml
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Any
import logging

def save_ad_for_campaigns(ad_data: Dict[str, Any]) -> bool:
    """
    Guarda un anuncio generado para usar en campañas
    
    Args:
        ad_data: Datos del anuncio generado
    
    Returns:
        bool: True si se guardó exitosamente
    """
    try:
        # Inicializar lista de anuncios pendientes si no existe
        if 'pending_ai_ads' not in st.session_state:
            st.session_state.pending_ai_ads = []
        
        # Crear estructura compatible con AdCreative
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
            'used': False,  # Marca si ya fue usado
            'campaign_id': None,
            'ad_group_id': None
        }
        
        # Verificar que no esté duplicado
        existing_ids = [ad['id'] for ad in st.session_state.pending_ai_ads]
        if ad_for_campaign['id'] not in existing_ids:
            st.session_state.pending_ai_ads.append(ad_for_campaign)
            logger.info(f"✅ Anuncio {ad_for_campaign['id']} guardado para campañas")
            return True
        else:
            logger.warning(f"⚠️ Anuncio {ad_for_campaign['id']} ya existe en pendientes")
            return False
        
    except Exception as e:
        logger.error(f"❌ Error guardando anuncio para campañas: {e}")
        return False


def get_pending_ads_count() -> int:
    """Obtiene el número de anuncios pendientes de usar en campañas"""
    if 'pending_ai_ads' not in st.session_state:
        return 0
    
    # Contar solo los no usados
    return len([ad for ad in st.session_state.pending_ai_ads if not ad.get('used', False)])


def mark_ad_as_used(ad_id: str, campaign_id: str = None, ad_group_id: str = None):
    """Marca un anuncio como usado en una campaña"""
    if 'pending_ai_ads' not in st.session_state:
        return
    
    for ad in st.session_state.pending_ai_ads:
        if ad['id'] == ad_id:
            ad['used'] = True
            ad['campaign_id'] = campaign_id
            ad['ad_group_id'] = ad_group_id
            ad['used_at'] = datetime.now().isoformat()
            logger.info(f"✅ Anuncio {ad_id} marcado como usado")
            break

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.ai_ad_generator import AIAdGenerator
from modules.ai_providers import OpenAIProvider, GeminiProvider
from utils.ad_validator import GoogleAdsValidator

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de página
st.set_page_config(
    page_title="🤖 Generador de Anuncios IA",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_config():
    """Cargar configuración desde ai_config.yaml"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "ai_config.yaml")
        with open(config_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except Exception as e:
        st.error(f"❌ Error cargando configuración: {e}")
        return None

def initialize_session_state():
    """Inicializar variables de sesión"""
    if 'ai_generator' not in st.session_state:
        st.session_state.ai_generator = AIAdGenerator()
    
    if 'generated_ads' not in st.session_state:
        st.session_state.generated_ads = []
    
    if 'validation_results' not in st.session_state:
        st.session_state.validation_results = {}
    
    if 'provider_status' not in st.session_state:
        st.session_state.provider_status = {
            'openai': {'connected': False, 'error': None},
            'gemini': {'connected': False, 'error': None}
        }

def test_provider_connection(provider_type: str, api_key: str, model: str) -> Dict[str, Any]:
    """Probar conexión con proveedor de IA"""
    try:
        if provider_type == "OpenAI":
            provider = OpenAIProvider(api_key=api_key, model=model)
        elif provider_type == "Gemini":
            provider = GeminiProvider(api_key=api_key, model=model)
        else:
            return {'success': False, 'error': 'Proveedor no válido'}
        
        success = provider.test_connection()
        return {'success': success, 'error': None if success else 'Conexión fallida'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

def render_provider_config():
    """Renderizar configuración de proveedores de IA"""
    st.subheader("🔧 Configuración de Proveedores de IA")
    
    config = load_config()
    if not config:
        st.error("❌ No se pudo cargar la configuración")
        return None, None
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🤖 OpenAI")
        
        # ✅ CORRECCIÓN: Input para API Key (NO hardcodeado)
        openai_api_key = st.text_input(
            "API Key OpenAI:",
            type="password",
            placeholder="sk-proj-...",
            key="openai_api_key_input",
            help="Ingresa tu API key de OpenAI. Obtén una en https://platform.openai.com/api-keys"
        )
        
        openai_model = st.selectbox(
            "Modelo OpenAI:",
            options=config.get('providers', {}).get('openai', {}).get('available_models', ["gpt-4", "gpt-3.5-turbo"]),
            index=0,
            key="openai_model"
        )
        
        # Botón para probar conexión OpenAI
        if st.button("🔍 Probar Conexión OpenAI", key="test_openai", disabled=not openai_api_key):
            with st.spinner("Probando conexión con OpenAI..."):
                result = test_provider_connection("OpenAI", openai_api_key, openai_model)
                st.session_state.provider_status['openai'] = {
                    'connected': result['success'],
                    'error': result['error'],
                    'api_key': openai_api_key if result['success'] else None,
                    'model': openai_model if result['success'] else None
                }
        
        # Estado de conexión OpenAI
        if st.session_state.provider_status['openai']['connected']:
            st.success(f"✅ OpenAI conectado correctamente ({openai_model})")
        elif st.session_state.provider_status['openai']['error']:
            st.error(f"❌ Error OpenAI: {st.session_state.provider_status['openai']['error']}")
    
    with col2:
        st.markdown("### 🧠 Google Gemini")
        
        # ✅ CORRECCIÓN: Input para API Key (NO hardcodeado)
        gemini_api_key = st.text_input(
            "API Key Gemini:",
            type="password",
            placeholder="AIzaSy...",
            key="gemini_api_key_input",
            help="Ingresa tu API key de Google Gemini. Obtén una en https://makersuite.google.com/app/apikey"
        )
        
        gemini_model = st.selectbox(
            "Modelo Gemini:",
            options=config.get('providers', {}).get('gemini', {}).get('available_models', ["gemini-pro"]),
            index=0,
            key="gemini_model"
        )
        
        # Botón para probar conexión Gemini
        if st.button("🔍 Probar Conexión Gemini", key="test_gemini", disabled=not gemini_api_key):
            with st.spinner("Probando conexión con Gemini..."):
                result = test_provider_connection("Gemini", gemini_api_key, gemini_model)
                st.session_state.provider_status['gemini'] = {
                    'connected': result['success'],
                    'error': result['error'],
                    'api_key': gemini_api_key if result['success'] else None,
                    'model': gemini_model if result['success'] else None
                }
        
        # Estado de conexión Gemini
        if st.session_state.provider_status['gemini']['connected']:
            st.success(f"✅ Gemini conectado correctamente ({gemini_model})")
        elif st.session_state.provider_status['gemini']['error']:
            st.error(f"❌ Error Gemini: {st.session_state.provider_status['gemini']['error']}")
    
    # ✅ Retornar configuración desde session_state (no desde inputs)
    providers_config = {
        'openai': {
            'api_key': st.session_state.provider_status['openai'].get('api_key'),
            'model': st.session_state.provider_status['openai'].get('model')
        },
        'gemini': {
            'api_key': st.session_state.provider_status['gemini'].get('api_key'),
            'model': st.session_state.provider_status['gemini'].get('model')
        }
    }
    
    return providers_config, config

def render_ad_generation_form(providers_config, config):
    """Renderizar formulario de generación de anuncios"""
    st.subheader("✨ Generar Anuncios")
    
    with st.form("ad_generation_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Selección de proveedor
            provider_options = []
            if st.session_state.provider_status['openai']['connected']:
                provider_options.append("OpenAI")
            if st.session_state.provider_status['gemini']['connected']:
                provider_options.append("Gemini")
            
            if not provider_options:
                st.warning("⚠️ Conecta al menos un proveedor de IA primero")
                st.form_submit_button("🚀 Generar Anuncios", disabled=True)
                return
            
            selected_provider = st.selectbox(
                "🤖 Proveedor de IA:",
                options=provider_options,
                key="selected_provider"
            )
            
            # Palabras clave
            keywords_input = st.text_area(
                "🔑 Palabras Clave:",
                placeholder="Ej: marketing digital, SEO, publicidad online",
                help="Separa las palabras clave con comas",
                key="keywords_input",
                height=100
            )
            
            # Tono del anuncio
            available_tones = list(config.get('generation', {}).get('available_tones', {}).keys())
            tone = st.selectbox(
                "🎭 Tono del Anuncio:",
                options=available_tones if available_tones else ["profesional"],
                index=0,
                key="tone_select"
            )
        
        with col2:
            # Cantidad de títulos y descripciones
            num_headlines = st.slider(
                "📝 Número de Títulos:",
                min_value=3,
                max_value=15,
                value=15,
                help="Google Ads permite hasta 15 títulos",
                key="num_headlines"
            )
            
            num_descriptions = st.slider(
                "📄 Número de Descripciones:",
                min_value=2,
                max_value=4,
                value=4,
                help="Google Ads permite hasta 4 descripciones",
                key="num_descriptions"
            )
            
            # Opciones avanzadas
            st.markdown("**⚙️ Opciones:**")
            validate_ads = st.checkbox(
                "✅ Validar automáticamente",
                value=True,
                key="validate_ads"
            )
            
            save_to_csv = st.checkbox(
                "💾 Guardar en CSV",
                value=True,
                key="save_to_csv"
            )
        
        # Botón de generación
        generate_button = st.form_submit_button(
            "🚀 Generar Anuncios",
            type="primary",
            use_container_width=True
        )
        
        if generate_button:
            if not keywords_input.strip():
                st.error("❌ Por favor ingresa al menos una palabra clave")
                return
            
            keywords = [kw.strip() for kw in keywords_input.split(",") if kw.strip()]
            
            if len(keywords) > config.get('limits', {}).get('max_keywords_per_request', 10):
                st.error(f"❌ Máximo {config.get('limits', {}).get('max_keywords_per_request', 10)} palabras clave permitidas")
                return
            
            # Generar anuncios
            generate_ads(
                selected_provider,
                providers_config,
                keywords,
                num_headlines,
                num_descriptions,
                tone,
                validate_ads,
                save_to_csv
            )

def generate_ads(provider_name, providers_config, keywords, num_headlines, 
                num_descriptions, tone, validate_ads, save_to_csv):
    """Generar anuncios con el proveedor seleccionado"""
    
    try:
        with st.spinner(f"🤖 Generando anuncios con {provider_name}..."):
            
            # ✅ CORRECCIÓN: Usar AIAdGenerator completo
            ai_generator = st.session_state.ai_generator
            
            # Configurar proveedor
            provider_config = providers_config[provider_name.lower()]
            success = ai_generator.set_provider(
                provider_type=provider_name.lower(),
                api_key=provider_config['api_key'],
                model=provider_config['model']
            )
            
            if not success:
                st.error(f"❌ No se pudo configurar {provider_name}")
                return
            
            # ✅ CORRECCIÓN: Usar método correcto con todos los parámetros
            generated_ads = ai_generator.generate_ad(
                keywords=keywords,
                num_ads=1,
                num_headlines=num_headlines,
                num_descriptions=num_descriptions,
                tone=tone,
                user=st.session_state.get('user_login', 'saltbalente'),
                validate=validate_ads
            )
            
            if not generated_ads or len(generated_ads) == 0:
                st.error("❌ No se generaron anuncios")
                return
            
            # Tomar el primer anuncio generado
            result = generated_ads[0]
            
            if 'error' in result:
                st.error(f"❌ Error generando anuncios: {result['error']}")
                return
            
            # Guardar en session state
            st.session_state.generated_ads = result
            st.session_state.validation_results = result.get('validation_result', {})
            
            st.success(f"✅ ¡Anuncios generados exitosamente con {provider_name}!")
            st.balloons()
            
    except Exception as e:
        st.error(f"❌ Error inesperado: {str(e)}")
        logger.error(f"Error generando anuncios: {e}", exc_info=True)

def render_results():
    """Renderizar resultados de anuncios generados"""
    if not st.session_state.generated_ads:
        return
    
    st.subheader("📊 Resultados Generados")
    
    ads = st.session_state.generated_ads
    validation = st.session_state.validation_results
    
    # ===== AGREGAR: Botón para usar en campañas =====
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
                border-left: 4px solid #667eea; border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
        <h4 style="margin: 0 0 0.5rem 0;">💡 ¿Quieres usar este anuncio en una campaña?</h4>
        <p style="margin: 0; font-size: 0.9rem;">
            Guárdalo y luego podrás importarlo directamente en el editor de campañas.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col_save, col_status = st.columns([1, 2])
    
    with col_save:
        if st.button("📤 Guardar para Usar en Campañas", use_container_width=True, type="primary", key="save_for_campaigns"):
            success = save_ad_for_campaigns(ads)
            if success:
                st.success("✅ Anuncio guardado. Ve a **Campañas → Editar → Crear Grupo** para usarlo.")
                st.balloons()
                time.sleep(2)
                st.rerun()
            else:
                st.warning("⚠️ Este anuncio ya está guardado")
    
    with col_status:
        pending_count = get_pending_ads_count()
        if pending_count > 0:
            st.info(f"📋 Tienes **{pending_count}** anuncio(s) listo(s) para usar en campañas")
        else:
            st.caption("No hay anuncios guardados aún")
    
    st.markdown("---")
    
    # Información general
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🤖 Proveedor", ads.get('provider', 'N/A'))
    
    with col2:
        st.metric("📝 Títulos", len(ads.get('headlines', [])))
    
    with col3:
        st.metric("📄 Descripciones", len(ads.get('descriptions', [])))
    
    with col4:
        if validation and 'summary' in validation:
            valid_count = validation['summary'].get('valid_headlines', 0)
            total_count = validation['summary'].get('total_headlines', 0)
            st.metric("✅ Títulos Válidos", f"{valid_count}/{total_count}")
    
    # Tabs para mostrar resultados
    tab1, tab2, tab3 = st.tabs(["📝 Títulos", "📄 Descripciones", "📊 Validación"])
    
    with tab1:
        st.markdown("### 📝 Títulos Generados")
        headlines_data = []
        
        for i, headline in enumerate(ads.get('headlines', [])):
            # ✅ CORRECCIÓN: Usar índice numérico
            headline_validation = validation.get('headlines', {}).get(i, {})
            is_valid = headline_validation.get('valid', True)
            errors = headline_validation.get('errors', [])
            
            headlines_data.append({
                '#': i + 1,
                'Título': headline,
                'Caracteres': len(headline),
                'Estado': '✅ Válido' if is_valid else '❌ Inválido',
                'Problemas': ', '.join(errors) if errors else '-'
            })
        
        df_headlines = pd.DataFrame(headlines_data)
        st.dataframe(df_headlines, use_container_width=True, hide_index=True)
        
        # Exportar títulos
        if headlines_data:
            csv_headlines = df_headlines.to_csv(index=False)
            st.download_button(
                "📥 Exportar Títulos (CSV)",
                csv_headlines,
                f"titulos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )
    
    with tab2:
        st.markdown("### 📄 Descripciones Generadas")
        descriptions_data = []
        
        for i, description in enumerate(ads.get('descriptions', [])):
            # ✅ CORRECCIÓN: Usar índice numérico
            desc_validation = validation.get('descriptions', {}).get(i, {})
            is_valid = desc_validation.get('valid', True)
            errors = desc_validation.get('errors', [])
            
            descriptions_data.append({
                '#': i + 1,
                'Descripción': description,
                'Caracteres': len(description),
                'Estado': '✅ Válido' if is_valid else '❌ Inválido',
                'Problemas': ', '.join(errors) if errors else '-'
            })
        
        df_descriptions = pd.DataFrame(descriptions_data)
        st.dataframe(df_descriptions, use_container_width=True, hide_index=True)
        
        # Exportar descripciones
        if descriptions_data:
            csv_descriptions = df_descriptions.to_csv(index=False)
            st.download_button(
                "📥 Exportar Descripciones (CSV)",
                csv_descriptions,
                f"descripciones_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )
    
    with tab3:
        if validation and 'summary' in validation:
            st.markdown("### 📊 Resumen de Validación")
            
            summary = validation.get('summary', {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📝 Títulos:**")
                st.write(f"• Total: {summary.get('total_headlines', 0)}")
                st.write(f"• ✅ Válidos: {summary.get('valid_headlines', 0)}")
                st.write(f"• ❌ Inválidos: {summary.get('invalid_headlines', 0)}")
            
            with col2:
                st.markdown("**📄 Descripciones:**")
                st.write(f"• Total: {summary.get('total_descriptions', 0)}")
                st.write(f"• ✅ Válidas: {summary.get('valid_descriptions', 0)}")
                st.write(f"• ❌ Inválidas: {summary.get('invalid_descriptions', 0)}")
            
            # Estado general
            is_valid = validation.get('valid', False)
            if is_valid:
                st.success("✅ El anuncio cumple con todas las políticas de Google Ads")
            else:
                st.error("❌ El anuncio tiene errores que deben corregirse")
            
            # Mostrar errores si existen
            if 'errors' in validation and validation['errors']:
                st.markdown("**⚠️ Errores Encontrados:**")
                for error in validation['errors']:
                    st.write(f"• {error}")
            
            # Mostrar advertencias si existen
            if 'warnings' in validation and validation['warnings']:
                st.markdown("**💡 Advertencias:**")
                for warning in validation['warnings']:
                    st.write(f"• {warning}")
        else:
            st.info("ℹ️ No se ejecutó validación para estos anuncios")

def main():
    """Función principal"""
    st.title("🤖 Generador de Anuncios con IA")
    st.markdown("Crea anuncios impactantes para Google Ads usando Inteligencia Artificial")
    st.markdown("---")
    
    # Inicializar session state
    initialize_session_state()
    
    # Sidebar con información
    with st.sidebar:
        st.markdown("### ℹ️ Información")
        st.markdown("""
        **Características:**
        • 🤖 OpenAI GPT-4 y Google Gemini
        • ✅ Validación automática de políticas
        • 💾 Almacenamiento en CSV
        • 🎭 Múltiples tonos de voz
        • 📊 Análisis detallado de resultados
        """)
        
        st.markdown("---")
        
        st.markdown("### 📋 Límites de Google Ads")
        st.markdown("""
        **Títulos:**
        • Máx. 30 caracteres
        • Mín. 3 títulos requeridos
        
        **Descripciones:**
        • Máx. 90 caracteres
        • Mín. 2 descripciones requeridas
        
        **Restricciones:**
        • Sin mayúsculas consecutivas (ej: USA ✅, OFERTA ❌)
        • Sin signos: ! ? ¡ ¿
        • Sin emojis
        • Sin palabras prohibidas
        """)
        
        st.markdown("---")
        
        # Estadísticas
        if st.session_state.ai_generator:
            st.markdown("### 📊 Estadísticas")
            try:
                stats = st.session_state.ai_generator.get_statistics()
                st.metric("Total Anuncios", stats.get('total_ads', 0))
                st.metric("Publicados", stats.get('published_ads', 0))
            except:
                st.info("No hay estadísticas disponibles")
    
    # Configuración de proveedores
    providers_config, config = render_provider_config()
    
    if providers_config and config:
        st.markdown("---")
        
        # Formulario de generación
        render_ad_generation_form(providers_config, config)
        
        st.markdown("---")
        
        # Mostrar resultados
        render_results()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "Desarrollado con ❤️ para optimizar tus campañas de Google Ads"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()