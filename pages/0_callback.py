"""
OAuth Callback Handler
Esta página captura automáticamente el código de autorización
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.auth import GoogleAdsAuth

st.set_page_config(page_title="Procesando autenticación...", page_icon="🔄")

# Ocultar esta página del menú
st.markdown("""
<style>
    [data-testid="stSidebarNav"] li:first-child {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔄 Procesando autenticación...")

# Obtener query params
query_params = st.query_params

if "code" in query_params:
    auth_code = query_params["code"]
    st.info(f"✅ Código de autorización recibido: {auth_code[:20]}...")
    
    # Crear instancia de auth
    auth = GoogleAdsAuth()
    
    # Construir la URL completa
    if "scope" in query_params:
        scope = query_params["scope"]
        full_url = f"https://appadsapi-miynrefpxescytebdgkkng.streamlit.app/?code={auth_code}&scope={scope}"
    else:
        full_url = f"https://appadsapi-miynrefpxescytebdgkkng.streamlit.app/?code={auth_code}"
    
    st.info("🔄 Procesando código...")
    
    # Procesar el callback
    if auth.handle_callback(full_url):
        st.success("🎉 ¡Autenticación exitosa!")
        
        # Limpiar query params
        st.query_params.clear()
        
        # Esperar un momento y redirigir
        import time
        time.sleep(2)
        
        st.markdown("""
        <meta http-equiv="refresh" content="0; url=/" />
        """, unsafe_allow_html=True)
        
        st.info("Redirigiendo al dashboard...")
        
    else:
        st.error("❌ Error procesando la autenticación")
        
        if st.button("🔄 Reintentar"):
            st.query_params.clear()
            st.rerun()
            
elif "error" in query_params:
    error = query_params["error"]
    st.error(f"❌ Error de autenticación: {error}")
    
    if st.button("🏠 Volver al inicio"):
        st.query_params.clear()
        st.switch_page("app.py")
        
else:
    st.warning("⚠️ No se encontró código de autorización")
    st.info("Si acabas de autorizar, espera un momento...")
    
    if st.button("🏠 Volver al inicio"):
        st.switch_page("app.py")