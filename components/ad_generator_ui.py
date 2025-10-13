"""
✨ AD GENERATOR UI - Interfaz de Generación de Anuncios
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def show():
    """Muestra la interfaz del generador de anuncios"""
    
    st.markdown("## ✨ Generador de Anuncios con IA")
    
    st.info("""
    **🎯 Genera anuncios optimizados para Google Ads usando IA**
    
    Selecciona un proveedor de IA (OpenAI, Anthropic, Gemini) y genera 
    automáticamente headlines y descriptions personalizados.
    """)
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["🚀 Generación Simple", "🎨 Con Templates", "⚙️ Configuración"])
    
    # ========== TAB 1: GENERACIÓN SIMPLE ==========
    with tab1:
        st.markdown("### Generación Rápida")
        
        # Selección de proveedor
        col1, col2 = st.columns([2, 1])
        
        with col1:
            provider = st.selectbox(
                "Proveedor de IA:",
                ["OpenAI (GPT-4)", "Anthropic (Claude)", "Google (Gemini)", "Sin IA (Templates)"],
                index=3  # Default: Sin IA
            )
        
        with col2:
            tone = st.selectbox(
                "Tono:",
                ["emocional", "urgente", "profesional", "místico", "poderoso"],
                index=0
            )
        
        # Keywords
        st.markdown("### 🔑 Keywords")
        keywords_input = st.text_area(
            "Ingresa tus keywords (una por línea o separadas por comas):",
            placeholder="amarres de amor\nhechizos efectivos\nbrujería profesional",
            height=100
        )
        
        # Configuración
        col1, col2 = st.columns(2)
        
        with col1:
            num_headlines = st.number_input("Número de Headlines:", 5, 15, 10)
        
        with col2:
            num_descriptions = st.number_input("Número de Descriptions:", 2, 4, 3)
        
        # Botón de generar
        if st.button("✨ Generar Anuncios", type="primary", use_container_width=True):
            if not keywords_input.strip():
                st.error("❌ Por favor ingresa al menos una keyword")
            else:
                # Procesar keywords
                keywords = [
                    kw.strip() 
                    for kw in keywords_input.replace(',', '\n').split('\n') 
                    if kw.strip()
                ]
                
                with st.spinner("🎨 Generando anuncios..."):
                    try:
                        # Si tiene template manager, usarlo
                        if st.session_state.get('template_manager'):
                            from modules.template_manager import TemplateManager
                            
                            tm = st.session_state.template_manager
                            
                            # Generar con templates
                            result = tm.generate_ad(
                                keywords=keywords,
                                tone=tone,
                                num_headlines=num_headlines,
                                num_descriptions=num_descriptions
                            )
                            
                            if result['success']:
                                st.success("✅ ¡Anuncios generados exitosamente!")
                                
                                # Mostrar headlines
                                st.markdown("### 📝 Headlines")
                                for i, headline in enumerate(result['headlines'], 1):
                                    st.code(f"{i}. {headline}", language="text")
                                
                                # Mostrar descriptions
                                st.markdown("### 📄 Descriptions")
                                for i, desc in enumerate(result['descriptions'], 1):
                                    st.code(f"{i}. {desc}", language="text")
                                
                                # Guardar en session state
                                st.session_state.last_generated_ad = result
                                
                                # Actualizar estadísticas
                                st.session_state.stats['anuncios_generados'] += 1
                                
                                # Botón de exportar
                                st.markdown("---")
                                if st.button("📦 Exportar Anuncios", use_container_width=True):
                                    st.info("Funcionalidad de exportación disponible en la pestaña 📦 Exportación")
                            else:
                                st.error(f"❌ Error: {result.get('error', 'Error desconocido')}")
                        
                        else:
                            st.warning("⚠️ Template Manager no disponible. Generando con datos de ejemplo...")
                            
                            # Generar con datos de ejemplo
                            import random
                            
                            example_headlines = [
                                f"Amarres de Amor {tone.capitalize()}",
                                f"Hechizos Efectivos - Resultados en 24h",
                                f"Brujería Profesional Certificada",
                                f"Recupera a Tu Pareja {tone.capitalize()}",
                                f"Magia Blanca Poderosa - {keywords[0].title()}",
                            ]
                            
                            example_descriptions = [
                                f"Amarres de amor con magia blanca efectiva. Tono {tone}. Resultados garantizados.",
                                f"Bruja profesional especializada en {keywords[0]}. Consulta gratis disponible.",
                                f"Recupera a tu pareja con rituales poderosos. Discreto y seguro."
                            ]
                            
                            st.success("✅ Anuncios de ejemplo generados")
                            
                            st.markdown("### 📝 Headlines")
                            for i, h in enumerate(example_headlines[:num_headlines], 1):
                                st.code(f"{i}. {h}", language="text")
                            
                            st.markdown("### 📄 Descriptions")
                            for i, d in enumerate(example_descriptions[:num_descriptions], 1):
                                st.code(f"{i}. {d}", language="text")
                            
                            st.info("💡 **Tip:** Configura un proveedor de IA para generar anuncios reales")
                    
                    except Exception as e:
                        st.error(f"❌ Error generando anuncios: {e}")
    
    # ========== TAB 2: CON TEMPLATES ==========
    with tab2:
        st.markdown("### 🎨 Generar con Templates")
        
        st.info("""
        Usa templates predefinidos para generar anuncios más específicos.
        Los templates están optimizados para el nicho esotérico.
        """)
        
        if st.session_state.get('template_manager'):
            tm = st.session_state.template_manager
            
            # Listar templates disponibles
            templates = tm.list_templates()
            
            if templates:
                template_names = [t['name'] for t in templates]
                
                selected_template = st.selectbox(
                    "Selecciona un template:",
                    template_names
                )
                
                # Buscar template seleccionado
                template = next((t for t in templates if t['name'] == selected_template), None)
                
                if template:
                    st.markdown(f"**Categoría:** {template.get('category', 'N/A')}")
                    st.markdown(f"**Keywords sugeridas:** {', '.join(template.get('keywords', []))}")
                    
                    # Keywords personalizadas
                    custom_keywords = st.text_area(
                        "O ingresa tus propias keywords:",
                        placeholder="Opcional - deja vacío para usar las del template"
                    )
                    
                    if st.button("✨ Generar desde Template", type="primary", use_container_width=True):
                        keywords_to_use = template.get('keywords', [])
                        
                        if custom_keywords.strip():
                            keywords_to_use = [kw.strip() for kw in custom_keywords.split('\n') if kw.strip()]
                        
                        with st.spinner("Generando..."):
                            result = tm.generate_from_template(
                                template_name=selected_template,
                                keywords=keywords_to_use
                            )
                            
                            if result['success']:
                                st.success("✅ Anuncios generados desde template")
                                
                                st.markdown("### 📝 Headlines")
                                for i, h in enumerate(result['headlines'], 1):
                                    st.code(f"{i}. {h}", language="text")
                                
                                st.markdown("### 📄 Descriptions")
                                for i, d in enumerate(result['descriptions'], 1):
                                    st.code(f"{i}. {d}", language="text")
                            else:
                                st.error(f"❌ Error: {result.get('error')}")
            else:
                st.warning("⚠️ No hay templates disponibles")
        else:
            st.warning("⚠️ Template Manager no disponible")
    
    # ========== TAB 3: CONFIGURACIÓN ==========
    with tab3:
        st.markdown("### ⚙️ Configuración del Generador")
        
        st.markdown("#### 🔑 Proveedores de IA")
        
        # OpenAI
        with st.expander("🔵 OpenAI (GPT-4)"):
            openai_key = st.text_input(
                "API Key:",
                type="password",
                placeholder="sk-...",
                key="openai_key"
            )
            
            openai_model = st.selectbox(
                "Modelo:",
                ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                key="openai_model"
            )
            
            if st.button("💾 Guardar OpenAI", key="save_openai"):
                st.success("✅ Configuración guardada")
        
        # Anthropic
        with st.expander("🟣 Anthropic (Claude)"):
            anthropic_key = st.text_input(
                "API Key:",
                type="password",
                placeholder="sk-ant-...",
                key="anthropic_key"
            )
            
            anthropic_model = st.selectbox(
                "Modelo:",
                ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                key="anthropic_model"
            )
            
            if st.button("💾 Guardar Anthropic", key="save_anthropic"):
                st.success("✅ Configuración guardada")
        
        # Google Gemini
        with st.expander("🔴 Google (Gemini)"):
            gemini_key = st.text_input(
                "API Key:",
                type="password",
                placeholder="AIza...",
                key="gemini_key"
            )
            
            gemini_model = st.selectbox(
                "Modelo:",
                ["gemini-pro", "gemini-ultra"],
                key="gemini_model"
            )
            
            if st.button("💾 Guardar Gemini", key="save_gemini"):
                st.success("✅ Configuración guardada")
        
        st.markdown("---")
        st.info("""
        **💡 Sin API Keys:**
        
        Puedes usar el sistema sin configurar proveedores de IA.
        En ese caso, se generarán anuncios usando templates predefinidos.
        """)