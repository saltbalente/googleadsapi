"""
Debug Cache - Página de diagnóstico para caché de cuentas
"""

import streamlit as st
import os
from pathlib import Path

st.set_page_config(page_title="Debug Cache", page_icon="🔧", layout="wide")

st.title("🔧 Diagnóstico de Caché de Cuentas")

# Verificar session state
st.header("1️⃣ Session State")
if 'account_cache_manager' in st.session_state:
    st.success("✅ account_cache_manager existe en session_state")
    cache_info = st.session_state.account_cache_manager.get_cache_info()
    st.json(cache_info)
else:
    st.error("❌ account_cache_manager NO existe en session_state")

# Verificar directorio data
st.header("2️⃣ Directorio data/")
data_dir = Path("data")
if data_dir.exists():
    st.success(f"✅ Directorio data/ existe: {data_dir.absolute()}")
    files = list(data_dir.glob("*"))
    if files:
        st.write("Archivos en data/:")
        for f in files:
            st.write(f"- {f.name}")
    else:
        st.warning("⚠️ Directorio data/ está vacío")
else:
    st.error("❌ Directorio data/ NO existe")
    if st.button("Crear directorio data/"):
        data_dir.mkdir(exist_ok=True)
        st.success("✅ Directorio creado")
        st.rerun()

# Verificar permisos
st.header("3️⃣ Permisos")
try:
    test_file = Path("data/test_permissions.txt")
    test_file.parent.mkdir(exist_ok=True)
    test_file.write_text("test")
    test_file.unlink()
    st.success("✅ Permisos de escritura OK")
except Exception as e:
    st.error(f"❌ Error de permisos: {e}")

# Verificar customer_ids
st.header("4️⃣ Customer IDs")
if 'customer_ids' in st.session_state:
    st.success(f"✅ {len(st.session_state.customer_ids)} cuentas encontradas")
    st.write(st.session_state.customer_ids)
else:
    st.error("❌ customer_ids NO existe")

# Verificar cliente de Google Ads
st.header("5️⃣ Cliente Google Ads")
if 'google_ads_client' in st.session_state:
    client = st.session_state.google_ads_client
    st.success("✅ Cliente existe")
    
    # Verificar si tiene el método
    if hasattr(client, 'get_account_descriptive_names'):
        st.success("✅ Método get_account_descriptive_names existe")
        
        # Probar el método
        if st.button("🧪 Probar obtener nombres desde API"):
            with st.spinner("Consultando API..."):
                try:
                    if 'customer_ids' in st.session_state and st.session_state.customer_ids:
                        # Probar solo con la primera cuenta
                        test_id = st.session_state.customer_ids[0]
                        st.info(f"Probando con cuenta: {test_id}")
                        
                        names = client.get_account_descriptive_names([test_id])
                        st.success("✅ API respondió correctamente")
                        st.json(names)
                    else:
                        st.error("No hay customer_ids")
                except Exception as e:
                    st.error(f"❌ Error llamando API: {e}")
                    st.exception(e)
    else:
        st.error("❌ Método get_account_descriptive_names NO existe")
        st.warning("⚠️ Debes agregar el método a modules/google_ads_client.py")
else:
    st.error("❌ Cliente NO existe")

# Forzar actualización manual
st.header("6️⃣ Forzar Caché Manual")
if st.button("🔄 Forzar actualización completa"):
    if 'account_cache_manager' in st.session_state and 'customer_ids' in st.session_state:
        try:
            # Limpiar caché
            st.session_state.account_cache_manager.clear_cache()
            st.info("🗑️ Caché limpiado")
            
            # Obtener nombres
            client = st.session_state.google_ads_client
            if client and hasattr(client, 'get_account_descriptive_names'):
                customer_ids = st.session_state.customer_ids
                st.info(f"📡 Consultando API para {len(customer_ids)} cuentas...")
                
                names = client.get_account_descriptive_names(customer_ids)
                st.success(f"✅ Obtenidos {len(names)} nombres")
                st.json(names)
                
                # Guardar en caché
                st.session_state.account_cache_manager.set_multiple_accounts(names)
                st.success("💾 Guardado en caché")
                
                # Verificar archivo
                cache_file = Path("data/account_names_cache.json")
                if cache_file.exists():
                    st.success(f"✅ Archivo creado: {cache_file.absolute()}")
                    st.code(cache_file.read_text(), language="json")
                else:
                    st.error("❌ Archivo NO se creó")
            else:
                st.error("Método get_account_descriptive_names no disponible")
        except Exception as e:
            st.error(f"❌ Error: {e}")
            st.exception(e)
    else:
        st.error("Falta account_cache_manager o customer_ids")

# Ver logs
st.header("7️⃣ Logs Recientes")
if st.button("📋 Ver logs"):
    log_file = Path("logs/app.log")
    if log_file.exists():
        logs = log_file.read_text().split("\n")
        st.code("\n".join(logs[-50:]))  # Últimas 50 líneas
    else:
        st.warning("No se encontró archivo de logs")