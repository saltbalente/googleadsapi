"""
Diagnóstico de Conexión Google Ads
"""

import streamlit as st
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.google_ads_client import GoogleAdsClientWrapper
from google.ads.googleads.client import GoogleAdsClient

st.title("🔍 Diagnóstico de Google Ads API")

st.markdown("---")

# Test 1: Verificar secrets
st.subheader("1️⃣ Verificar Secrets")

if "google_ads" in st.secrets:
    st.success("✅ Secrets de google_ads encontrados")
    
    config = st.secrets["google_ads"]
    
    st.info(f"""
    **Developer Token:** {'✅ Presente' if config.get('developer_token') else '❌ Falta'}
    **Client ID:** {'✅ Presente' if config.get('client_id') else '❌ Falta'}
    **Client Secret:** {'✅ Presente' if config.get('client_secret') else '❌ Falta'}
    **Login Customer ID:** {config.get('login_customer_id', 'N/A')}
    **Refresh Token:** {'✅ Presente' if config.get('refresh_token') else '❌ Falta'}
    """)
else:
    st.error("❌ No se encontraron secrets de google_ads")
    st.stop()

st.markdown("---")

# Test 2: Crear cliente
st.subheader("2️⃣ Crear Cliente de Google Ads")

try:
    wrapper = GoogleAdsClientWrapper()
    client = wrapper.get_client()
    
    if client:
        st.success("✅ Cliente creado exitosamente")
    else:
        st.error("❌ No se pudo crear el cliente")
        st.stop()
        
except Exception as e:
    st.error(f"❌ Error creando cliente: {e}")
    import traceback
    st.code(traceback.format_exc())
    st.stop()

st.markdown("---")

# Test 3: Obtener cuentas accesibles
st.subheader("3️⃣ Obtener Cuentas Accesibles")

try:
    customer_service = client.get_service("CustomerService")
    
    st.info("🔄 Consultando CustomerService...")
    
    # Intentar sin login_customer_id primero
    accessible_customers = customer_service.list_accessible_customers()
    resource_names = accessible_customers.resource_names
    
    if resource_names:
        st.success(f"✅ Encontradas {len(resource_names)} cuentas")
        
        st.markdown("### 📋 Cuentas Encontradas:")
        
        for resource_name in resource_names:
            customer_id = resource_name.split('/')[-1]
            
            st.markdown(f"#### Cuenta: `{customer_id}`")
            
            # Intentar obtener detalles
            try:
                query = f"""
                    SELECT
                        customer.id,
                        customer.descriptive_name,
                        customer.currency_code,
                        customer.time_zone,
                        customer.manager
                    FROM customer
                    WHERE customer.id = {customer_id}
                """
                
                ga_service = client.get_service("GoogleAdsService")
                
                # Intentar con este customer_id
                response = ga_service.search(customer_id=customer_id, query=query)
                
                for row in response:
                    customer = row.customer
                    
                    st.success(f"""
                    **Nombre:** {customer.descriptive_name}  
                    **ID:** {customer.id}  
                    **Moneda:** {customer.currency_code}  
                    **Zona Horaria:** {customer.time_zone}  
                    **Es Manager:** {'Sí' if customer.manager else 'No'}
                    """)
                    
                    if customer.manager:
                        st.warning("⚠️ Esta es una cuenta Manager (MCC)")
                    
            except Exception as detail_error:
                st.warning(f"⚠️ No se pudo obtener detalles: {detail_error}")
                
            st.markdown("---")
    else:
        st.error("❌ No se encontraron cuentas accesibles")
        
        st.markdown("### 🔍 Posibles causas:")
        st.markdown("""
        1. **La cuenta de Google no tiene acceso a Google Ads**
           - Ve a https://ads.google.com
           - Verifica que puedes ver alguna cuenta
        
        2. **El Developer Token no está aprobado**
           - Ve a Google Ads → Herramientas → API Center
           - Verifica el estado del token
        
        3. **Permisos insuficientes**
           - La cuenta necesita permisos de lectura mínimo
        
        4. **Login Customer ID incorrecto**
           - Verifica que sea el ID correcto de tu cuenta
        """)
        
except Exception as e:
    st.error(f"❌ Error: {e}")
    
    st.markdown("### 🔍 Detalles del Error:")
    import traceback
    st.code(traceback.format_exc())
    
    st.markdown("### 💡 Soluciones:")
    st.markdown("""
    1. **Verifica tus credenciales en Google Ads:**
       - https://ads.google.com
       - Inicia sesión con: contactodeamarres@gmail.com
    
    2. **Verifica el Developer Token:**
       - https://ads.google.com/aw/apicenter
       - Estado debe ser "Approved" (no "Test")
    
    3. **Verifica el OAuth:**
       - El refresh_token debe ser válido
       - Intenta re-autenticar si es necesario
    """)

st.markdown("---")

# Test 4: Información adicional
st.subheader("4️⃣ Información de Configuración")

st.code(f"""
Login Customer ID: {st.secrets['google_ads']['login_customer_id']}
Developer Token: {st.secrets['google_ads']['developer_token'][:10]}...
Refresh Token Length: {len(st.secrets['google_ads']['refresh_token'])} chars
""")