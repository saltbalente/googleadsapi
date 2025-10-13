"""
🏠 HOME UI - Página de Inicio Completa
"""

import streamlit as st
from datetime import datetime

def show():
    """Muestra la página de inicio completa"""
    
    # Bienvenida
    st.markdown("## 👋 ¡Bienvenido al Dashboard Completo!")
    
    st.markdown("""
    Sistema integrado de **generación inteligente de anuncios** con IA y 
    **gestión completa** de Google Ads API.
    """)
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Anuncios Generados</div>
            <div class="metric-value">{st.session_state.stats['anuncios_generados']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Tests A/B</div>
            <div class="metric-value">{st.session_state.stats['tests_ab']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Análisis Realizados</div>
            <div class="metric-value">{st.session_state.stats['analisis_realizados']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Keywords Extraídas</div>
            <div class="metric-value">{st.session_state.stats['keywords_extraidas']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick Actions
    st.markdown("### 🚀 Acciones Rápidas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✨ Generar Anuncios", use_container_width=True):
            st.session_state.current_page = "✨ Generador de Anuncios"
            st.rerun()
        st.caption("Crea anuncios con IA en segundos")
    
    with col2:
        if st.button("📊 Analizar Anuncios", use_container_width=True):
            st.session_state.current_page = "📊 Análisis y Scoring"
            st.rerun()
        st.caption("Evalúa la calidad de tus anuncios")
    
    with col3:
        if st.button("🧪 Crear Test A/B", use_container_width=True):
            st.session_state.current_page = "🧪 Pruebas A/B"
            st.rerun()
        st.caption("Compara variaciones de anuncios")
    
    st.markdown("---")
    
    # Funcionalidades
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### 🤖 Generación con IA
        - ✅ OpenAI, Anthropic, Gemini
        - ✅ Generación masiva
        - ✅ Tonos personalizables
        - ✅ Validación automática
        - ✅ Templates esotéricos
        
        #### 📈 Análisis y Optimización
        - ✅ Scoring 0-100
        - ✅ Análisis por categorías
        - ✅ Recomendaciones IA
        - ✅ Benchmarks de industria
        - ✅ Predicción CTR/CPC
        """)
    
    with col2:
        st.markdown("""
        #### 🧪 Testing y Competencia
        - ✅ Pruebas A/B automáticas
        - ✅ Análisis competitivo
        - ✅ Detección de gaps
        - ✅ Estrategias diferenciación
        - ✅ Scraping de anuncios
        
        #### 🔧 Herramientas Avanzadas
        - ✅ Extractor keywords
        - ✅ Análisis landing pages
        - ✅ Asistente conversacional
        - ✅ Exportación multi-formato
        - ✅ Control de versiones
        """)
    
    st.success(f"🕐 Sistema actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")