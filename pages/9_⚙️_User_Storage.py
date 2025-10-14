"""
Página de Configuración con Sistema de Storage Local
Gestiona preferencias, API keys, configuraciones y datos de usuario
"""

import streamlit as st
from utils.user_storage import get_user_storage
import json
from datetime import datetime
import pandas as pd

st.set_page_config(
    page_title="⚙️ Configuración de Usuario",
    page_icon="⚙️",
    layout="wide"
)

# Obtener storage del usuario
user_storage = get_user_storage("saltbalente")

st.title("⚙️ Configuración de Usuario")
st.markdown("**Sistema de Persistencia Local** - Gestiona tus preferencias, API keys y configuraciones")

tabs = st.tabs([
    "🎨 Preferencias",
    "🔑 API Keys",
    "⚙️ Settings",
    "⭐ Favoritos",
    "📜 Historial",
    "💾 Storage Info"
])

# ========================================================================
# TAB 1: PREFERENCIAS
# ========================================================================

with tabs[0]:
    st.header("🎨 Preferencias de Usuario")
    
    prefs = user_storage.get_preferences()
    
    with st.form("preferences_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            language = st.selectbox(
                "Idioma",
                options=['es', 'en'],
                index=0 if prefs.get('language') == 'es' else 1,
                help="Idioma de la interfaz"
            )
            
            theme = st.selectbox(
                "Tema",
                options=['dark', 'light'],
                index=0 if prefs.get('theme') == 'dark' else 1,
                help="Tema visual de la aplicación"
            )
            
            currency = st.selectbox(
                "Moneda",
                options=['USD', 'EUR', 'MXN', 'COP'],
                index=['USD', 'EUR', 'MXN', 'COP'].index(prefs.get('currency', 'USD')),
                help="Moneda por defecto para reportes"
            )
            
            timezone = st.selectbox(
                "Zona Horaria",
                options=['UTC', 'America/Mexico_City', 'America/Bogota', 'Europe/Madrid'],
                index=['UTC', 'America/Mexico_City', 'America/Bogota', 'Europe/Madrid'].index(prefs.get('timezone', 'UTC')),
                help="Zona horaria para fechas y reportes"
            )
        
        with col2:
            notifications_enabled = st.checkbox(
                "Notificaciones Habilitadas",
                value=prefs.get('notifications_enabled', True),
                help="Recibir notificaciones del sistema"
            )
            
            auto_refresh = st.checkbox(
                "Auto-actualización",
                value=prefs.get('auto_refresh', True),
                help="Actualizar datos automáticamente"
            )
            
            refresh_interval = st.slider(
                "Intervalo de actualización (segundos)",
                min_value=60,
                max_value=600,
                value=prefs.get('refresh_interval', 300),
                step=30,
                help="Frecuencia de actualización automática"
            )
            
            sidebar_collapsed = st.checkbox(
                "Sidebar colapsado por defecto",
                value=prefs.get('sidebar_collapsed', False),
                help="Iniciar con sidebar colapsado"
            )
        
        if st.form_submit_button("💾 Guardar Preferencias", type="primary"):
            new_prefs = {
                'language': language,
                'theme': theme,
                'currency': currency,
                'timezone': timezone,
                'notifications_enabled': notifications_enabled,
                'auto_refresh': auto_refresh,
                'refresh_interval': refresh_interval,
                'sidebar_collapsed': sidebar_collapsed
            }
            
            if user_storage.save_preferences(new_prefs):
                st.success("✅ Preferencias guardadas correctamente")
                st.rerun()
            else:
                st.error("❌ Error guardando preferencias")

# ========================================================================
# TAB 2: API KEYS
# ========================================================================

with tabs[1]:
    st.header("🔑 API Keys (Encriptadas)")
    st.info("🔒 Las API keys se almacenan encriptadas localmente")
    
    api_keys = user_storage.get_api_keys()
    
    # OpenAI
    with st.expander("🤖 OpenAI", expanded=True):
        with st.form("openai_form"):
            openai_data = api_keys.get('openai', {})
            
            openai_key = st.text_input(
                "API Key",
                value="***" if openai_data.get('api_key') else "",
                type="password",
                help="Tu API key de OpenAI"
            )
            
            openai_model = st.selectbox(
                "Modelo por defecto",
                options=['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo'],
                index=['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo'].index(openai_data.get('model', 'gpt-4o')),
                help="Modelo de OpenAI a usar por defecto"
            )
            
            if st.form_submit_button("💾 Guardar OpenAI"):
                if openai_key and openai_key != "***":
                    if user_storage.update_api_key('openai', openai_key, openai_model):
                        st.success("✅ API key de OpenAI guardada")
                    else:
                        st.error("❌ Error guardando API key")
    
    # Gemini
    with st.expander("🔮 Google Gemini"):
        with st.form("gemini_form"):
            gemini_data = api_keys.get('gemini', {})
            
            gemini_key = st.text_input(
                "API Key",
                value="***" if gemini_data.get('api_key') else "",
                type="password",
                help="Tu API key de Google Gemini"
            )
            
            gemini_model = st.selectbox(
                "Modelo por defecto",
                options=['gemini-2.0-flash-exp', 'gemini-1.5-pro', 'gemini-1.5-flash'],
                index=['gemini-2.0-flash-exp', 'gemini-1.5-pro', 'gemini-1.5-flash'].index(gemini_data.get('model', 'gemini-2.0-flash-exp')),
                help="Modelo de Gemini a usar por defecto"
            )
            
            if st.form_submit_button("💾 Guardar Gemini"):
                if gemini_key and gemini_key != "***":
                    if user_storage.update_api_key('gemini', gemini_key, gemini_model):
                        st.success("✅ API key de Gemini guardada")
                    else:
                        st.error("❌ Error guardando API key")
    
    # Anthropic
    with st.expander("🧠 Anthropic Claude"):
        with st.form("anthropic_form"):
            anthropic_data = api_keys.get('anthropic', {})
            
            anthropic_key = st.text_input(
                "API Key",
                value="***" if anthropic_data.get('api_key') else "",
                type="password",
                help="Tu API key de Anthropic"
            )
            
            anthropic_model = st.selectbox(
                "Modelo por defecto",
                options=['claude-3-5-sonnet-20241022', 'claude-3-haiku-20240307', 'claude-3-opus-20240229'],
                index=['claude-3-5-sonnet-20241022', 'claude-3-haiku-20240307', 'claude-3-opus-20240229'].index(anthropic_data.get('model', 'claude-3-5-sonnet-20241022')),
                help="Modelo de Claude a usar por defecto"
            )
            
            if st.form_submit_button("💾 Guardar Anthropic"):
                if anthropic_key and anthropic_key != "***":
                    if user_storage.update_api_key('anthropic', anthropic_key, anthropic_model):
                        st.success("✅ API key de Anthropic guardada")
                    else:
                        st.error("❌ Error guardando API key")

# ========================================================================
# TAB 3: SETTINGS
# ========================================================================

with tabs[2]:
    st.header("⚙️ Configuraciones Generales")
    
    settings = user_storage.get_settings()
    
    # Google Ads Settings
    with st.expander("📢 Google Ads", expanded=True):
        with st.form("google_ads_settings"):
            google_ads = settings.get('google_ads', {})
            
            default_customer_id = st.text_input(
                "Customer ID por defecto",
                value=google_ads.get('default_customer_id', ''),
                help="ID del cliente de Google Ads por defecto"
            )
            
            login_customer_id = st.text_input(
                "Login Customer ID",
                value=google_ads.get('login_customer_id', ''),
                help="ID del cliente de login (MCC)"
            )
            
            auto_select_account = st.checkbox(
                "Seleccionar cuenta automáticamente",
                value=google_ads.get('auto_select_account', False),
                help="Seleccionar automáticamente la primera cuenta disponible"
            )
            
            if st.form_submit_button("💾 Guardar Google Ads"):
                new_settings = settings.copy()
                new_settings['google_ads'] = {
                    'default_customer_id': default_customer_id,
                    'login_customer_id': login_customer_id,
                    'auto_select_account': auto_select_account
                }
                
                if user_storage.save_settings(new_settings):
                    st.success("✅ Configuración de Google Ads guardada")
                else:
                    st.error("❌ Error guardando configuración")
    
    # AI Generation Settings
    with st.expander("🤖 Generación de Anuncios IA"):
        with st.form("ai_generation_settings"):
            ai_gen = settings.get('ai_generation', {})
            
            default_provider = st.selectbox(
                "Proveedor IA por defecto",
                options=['openai', 'gemini', 'anthropic'],
                index=['openai', 'gemini', 'anthropic'].index(ai_gen.get('default_provider', 'openai')),
                help="Proveedor de IA a usar por defecto"
            )
            
            default_tone = st.selectbox(
                "Tono por defecto",
                options=['profesional', 'casual', 'persuasivo', 'técnico', 'emocional'],
                index=['profesional', 'casual', 'persuasivo', 'técnico', 'emocional'].index(ai_gen.get('default_tone', 'profesional')),
                help="Tono de los anuncios generados"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                num_headlines = st.slider(
                    "Número de headlines",
                    min_value=3,
                    max_value=15,
                    value=ai_gen.get('num_headlines', 10),
                    help="Cantidad de headlines a generar"
                )
            
            with col2:
                num_descriptions = st.slider(
                    "Número de descripciones",
                    min_value=2,
                    max_value=8,
                    value=ai_gen.get('num_descriptions', 3),
                    help="Cantidad de descripciones a generar"
                )
            
            auto_validate = st.checkbox(
                "Validación automática",
                value=ai_gen.get('auto_validate', True),
                help="Validar anuncios automáticamente al generar"
            )
            
            auto_score = st.checkbox(
                "Puntuación automática",
                value=ai_gen.get('auto_score', True),
                help="Calcular puntuación automáticamente"
            )
            
            if st.form_submit_button("💾 Guardar IA Settings"):
                new_settings = settings.copy()
                new_settings['ai_generation'] = {
                    'default_provider': default_provider,
                    'default_tone': default_tone,
                    'num_headlines': num_headlines,
                    'num_descriptions': num_descriptions,
                    'auto_validate': auto_validate,
                    'auto_score': auto_score
                }
                
                if user_storage.save_settings(new_settings):
                    st.success("✅ Configuración de IA guardada")
                else:
                    st.error("❌ Error guardando configuración")

# ========================================================================
# TAB 4: FAVORITOS
# ========================================================================

with tabs[3]:
    st.header("⭐ Favoritos")
    
    favorites = user_storage.get_favorites()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("📢 Campañas")
        campaigns = favorites.get('campaigns', [])
        if campaigns:
            for campaign in campaigns[-5:]:  # Últimos 5
                st.write(f"• {campaign.get('name', 'Sin nombre')}")
        else:
            st.info("No hay campañas favoritas")
    
    with col2:
        st.subheader("🔑 Keywords")
        keywords = favorites.get('keywords', [])
        if keywords:
            for keyword in keywords[-5:]:  # Últimos 5
                st.write(f"• {keyword.get('text', 'Sin texto')}")
        else:
            st.info("No hay keywords favoritas")
    
    with col3:
        st.subheader("📝 Anuncios")
        ads = favorites.get('ads', [])
        if ads:
            for ad in ads[-5:]:  # Últimos 5
                st.write(f"• {ad.get('headline', 'Sin headline')}")
        else:
            st.info("No hay anuncios favoritos")

# ========================================================================
# TAB 5: HISTORIAL
# ========================================================================

with tabs[4]:
    st.header("📜 Historial de Acciones")
    
    history = user_storage.get_history(limit=50)
    
    if history:
        # Convertir a DataFrame para mejor visualización
        df_history = pd.DataFrame(history)
        df_history['timestamp'] = pd.to_datetime(df_history['timestamp'])
        df_history = df_history.sort_values('timestamp', ascending=False)
        
        # Mostrar tabla
        st.dataframe(
            df_history[['timestamp', 'action', 'user']],
            use_container_width=True,
            hide_index=True
        )
        
        # Botón para limpiar historial
        if st.button("🗑️ Limpiar Historial", type="secondary"):
            # Aquí podrías implementar la función de limpiar historial
            st.warning("Función de limpiar historial no implementada aún")
    else:
        st.info("No hay historial disponible")

# ========================================================================
# TAB 6: STORAGE INFO
# ========================================================================

with tabs[5]:
    st.header("💾 Información del Storage")
    
    storage_info = user_storage.get_storage_info()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Usuario", storage_info['user_id'])
        st.metric("Tamaño Total", f"{storage_info['total_size_mb']:.2f} MB")
        st.metric("Ruta Base", storage_info['base_path'])
    
    with col2:
        st.subheader("📁 Archivos")
        for name, info in storage_info['files'].items():
            status = "✅" if info['exists'] else "❌"
            size_kb = info['size_bytes'] / 1024 if info['size_bytes'] > 0 else 0
            st.write(f"{status} **{name}**: {size_kb:.1f} KB")
    
    # Botones de utilidad
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧹 Limpiar Cache", type="secondary"):
            user_storage.clear_cache()
            st.success("Cache limpiada")
    
    with col2:
        if st.button("📤 Exportar Datos", type="secondary"):
            export_data = user_storage.export_all_data()
            st.download_button(
                "⬇️ Descargar Export",
                data=json.dumps(export_data, indent=2, ensure_ascii=False),
                file_name=f"user_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col3:
        if st.button("🔄 Recargar Info", type="primary"):
            st.rerun()

# ========================================================================
# SIDEBAR: ACCIONES RÁPIDAS
# ========================================================================

with st.sidebar:
    st.header("🚀 Acciones Rápidas")
    
    # Mostrar estado de API keys
    api_keys = user_storage.get_api_keys()
    
    st.subheader("🔑 Estado API Keys")
    for provider, data in api_keys.items():
        if provider != 'created_at' and provider != 'last_updated':
            has_key = bool(data.get('api_key'))
            status = "✅" if has_key else "❌"
            st.write(f"{status} {provider.title()}")
    
    # Botón para agregar al historial (ejemplo)
    if st.button("📝 Test Historial"):
        user_storage.add_to_history(
            "test_action",
            {"message": "Acción de prueba desde la interfaz"}
        )
        st.success("Acción agregada al historial")

# ========================================================================
# FOOTER
# ========================================================================

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        💾 Sistema de Persistencia Local v1.0<br>
        Datos almacenados localmente y encriptados de forma segura
    </div>
    """,
    unsafe_allow_html=True
)